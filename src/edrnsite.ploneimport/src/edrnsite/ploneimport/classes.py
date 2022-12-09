# encoding: utf-8

'''📦 EDRN Site Import from Plone: classes.'''

from django.core.files import File
from django.core.files.images import ImageFile
from edrnsite.content.models import FlexPage
from wagtail.models import Page
from wagtail.rich_text import RichText
from wagtail.documents.models import Document
from wagtail.images.models import Image
from django.template.loader import render_to_string
import json, html, os, logging, subprocess

_logger = logging.getLogger(__name__)


class Node(object):
    def __init__(self, uid):
        self.uid = uid
        self.children = set()

    def __str__(self):
        return self.uid


class PaperlessExport(object):
    def __init__(self, base_url, content_file, blob_dir):
        self.base_url, self.blob_dir, self.prefix = base_url, blob_dir, len(base_url)
        self.content_by_uid, self.content_by_path, self.tree = {}, {}, {}
        content = json.load(content_file)
        content_file.close()
        for i in content:
            path, uid = i['@id'][self.prefix:], i['UID']
            self.content_by_uid[uid] = self.content_by_path[path] = i
            parent = i['parent']['UID']
            if parent is not None:
                child_node, parent_node = self.tree.get(uid, Node(uid)), self.tree.get(parent, Node(parent))
                parent_node.children.add(child_node)
                self.tree[uid] = child_node
                self.tree[parent] = parent_node

    def __repr__(self):
        return f'{self.__class__.__name__}({self.base_url})' 

    def get_import(self):
        top_level_pages, self.objs_by_uid, self.objs_by_path = [], {}, {}
        for top_level_item in ('network-consulting-team', 'about'):
            top_level_pages.append(self._create_plone_tree(path=top_level_item))
        root = PlonePage(self, None, '/', None, 'EDRN', 'Biomarkers: the key to early detection', top_level_pages, '')
        return root

    def _create_plone_tree(self, path=None, uid=None):
        if path is not None:
            d = self.content_by_path[path]
        elif uid is not None:
            d = self.content_by_uid[uid]
        else:
            raise ValueError('Must specify either path or uid')
        uid, title, description, item_id, path = d['UID'], d['title'], d['description'], d['id'], d['@id'][self.prefix:]
        title = title.strip()
        if d['@type'] == 'Image':
            blob = os.path.join(self.blob_dir, d['image']['blob_path'])
            filename, ct = d['image']['filename'], d['image']['content-type']
            plone_object = PloneImage(self, uid, path, item_id, title, description, filename, ct, blob)
        elif d['@type'] == 'File':
            blob = os.path.join(self.blob_dir, d['file']['blob_path'])
            filename, ct = d['file']['filename'], d['file']['content-type']
            if not filename: filename = d['id']
            plone_object = PloneFile(self, uid, path, item_id, title, description, filename, ct, blob)
        elif d['@type'] == 'Folder':
            children = [self._create_plone_tree(uid=i) for i in [j.uid for j in self.tree.get(uid).children]]
            children = [i for i in children if i is not None]
            children.sort(key=lambda i: i.title)
            body = render_to_string('edrnsite.ploneimport/folder-view.html', {'children': children})
            plone_object = PlonePage(self, uid, path, item_id, title, description, children, body)
        elif d['@type'] == 'eke.knowledge.collaborationsfolder':
            children = []
            for child_uid in [i.uid for i in self.tree.get(uid).children]:
                child = self._create_plone_tree(uid=child_uid)
                if child is not None and child.item_id != 'steering-committee':  # Was imported from `importfromplone`
                    children.append(child)
            plone_object = PlonePage(self, uid, path, item_id, title, description, children, 'Groups here')
        elif d['@type'] in ('eke.knowledge.groupspacefolder', 'eke.knowledge.collaborativegroupfolder'):
            children = [
                self._create_plone_tree(uid=i) for i in [j.uid for j in self.tree.get(uid).children] 
                if i is not None
            ]
            plone_object = PlonePage(self, uid, path, item_id, title, description, children, '<p></p>')
        elif d['@type'] in (
            'Document', 'Link', 'Event', 'eke.knowledge.groupspaceindex', 'eke.knowledge.collaborativegroupindex',
            'News Item'
        ):
            plone_object = None
        else:
            raise ValueError(f'Unexpected type {d["@type"]}')
        self.objs_by_uid[uid] = self.objs_by_path[path] = plone_object
        return plone_object


class PloneExport(object):
    def __init__(self, base_url, content_file, default_pages_file, blob_dir):
        self.base_url, self.blob_dir, self.prefix = base_url, blob_dir, len(base_url)
        self.content_by_uid, self.content_by_path, self.tree = {}, {}, {}
        content = json.load(content_file)
        content_file.close()
        for i in content:
            path, uid = i['@id'][self.prefix:], i['UID']
            self.content_by_uid[uid] = self.content_by_path[path] = i
            parent = i['parent']['UID']
            if parent is not None:
                child_node, parent_node = self.tree.get(uid, Node(uid)), self.tree.get(parent, Node(parent))
                parent_node.children.add(child_node)
                self.tree[uid] = child_node
                self.tree[parent] = parent_node
        dps = json.load(default_pages_file)
        default_pages_file.close()
        self.default_pages = {}
        for entry in dps:
            uid = entry['uuid']
            assert uid not in self.default_pages
            self.default_pages[uid] = entry['default_page_uuid']

    def __repr__(self):
        return f'{self.__class__.__name__}({self.base_url})'

    def _create_plone_tree(self, path=None, uid=None):
        if path is not None:
            d = self.content_by_path[path]
        elif uid is not None:
            d = self.content_by_uid[uid]
        else:
            raise ValueError('Must specify either path or uid')
        uid, title, description, item_id, path = d['UID'], d['title'], d['description'], d['id'], d['@id'][self.prefix:]
        if d['@type'] == 'Image':
            blob = os.path.join(self.blob_dir, d['image']['blob_path'])
            filename, ct = d['image']['filename'], d['image']['content-type']
            plone_object = PloneImage(self, uid, path, item_id, title, description, filename, ct, blob)
        elif d['@type'] == 'File':
            blob = os.path.join(self.blob_dir, d['file']['blob_path'])
            filename, ct = d['file']['filename'], d['file']['content-type']
            if not filename: filename = d['id']
            plone_object = PloneFile(self, uid, path, item_id, title, description, filename, ct, blob)
        elif d['@type'] == 'Folder':
            content_view = self.default_pages.get(uid)
            children = [self._create_plone_tree(uid=i) for i in [j.uid for j in self.tree.get(uid).children]]
            # Avoid putting the default view of a page into the list of children; we don't want to dupe these
            # since in Wagtail any node can be both content'ish and item'ish (in Plone parlance)
            children = [i for i in children if i is not None and i.uid != content_view]
            if content_view is None:
                # Set up an HTML page which is just our a listing of our child pages
                body = render_to_string('edrnsite.ploneimport/folder-view.html', {'children': children})
            else:
                body = self.content_by_uid[content_view]['text']['data']
            plone_object = PlonePage(self, uid, path, item_id, title, description, children, body)
        elif d['@type'] == 'eke.knowledge.collaborationsfolder':
            children = []
            for child_uid in [i.uid for i in self.tree.get(uid).children]:
                child = self._create_plone_tree(uid=child_uid)
                if child is not None:
                    children.append(child)
            plone_object = PlonePage(self, uid, path, item_id, title, description, children, 'Groups here')
        elif d['@type'] == 'eke.knowledge.groupspacefolder':
            if path.endswith('steering-committee'):
                children = [
                    self._create_plone_tree(uid=i) for i in [j.uid for j in self.tree.get(uid).children] 
                    if i is not None
                ]
                plone_object = PlonePage(self, uid, path, item_id, title, description, children, 'Steering Committee')
            else:
                plone_object = None
        elif d['@type'] == 'Document':
            try:
                body = d['text']['data']
            except TypeError:
                body = ''
            plone_object = PlonePage(self, uid, path, item_id, title, description, None, body)
        elif d['@type'] == 'Link':
            plone_object = PloneLink(self, uid, path, item_id, title, description, d['remoteUrl'])
        elif d['@type'] == 'Event':
            plone_object = PloneEvent(self, uid, path, item_id, title, description, d)
        elif d['@type'] in (
            'eke.knowledge.groupspaceindex', 'eke.knowledge.collaborativegroupindex',
            'eke.knowledge.collaborativegroupfolder', 'Collection'
        ):
            # Ignore these for now
            plone_object = None
        else:
            raise ValueError(f'Unexpected type {d["@type"]}')
        self.objs_by_uid[uid] = self.objs_by_path[path] = plone_object
        return plone_object

    def get_import(self):
        top_level_pages, self.objs_by_uid, self.objs_by_path = [], {}, {}
        for top_level_item in (
            'data-and-resources', 'network-consulting-team', 'news-and-events', 'work-with-edrn', 'about',
            'administrivia'
        ):
            top_level_pages.append(self._create_plone_tree(path=top_level_item))
        root = PlonePage(self, None, '/', None, 'EDRN', 'Biomarkers: the key to early detection', top_level_pages, '')
        return root


class PloneObject(object):
    def __init__(self, plone_export, uid, path, item_id, title, description, children=None):
        self.plone_export = plone_export
        self.uid, self.path, self.item_id, self.title, self.description = uid, path, item_id, title, description
        assert self.path is not None
        if children is None:
            self.children = []
        else:
            self.children = children
        self._pk = None

    def install(self, parent: Page, export: PloneExport):
        raise NotImplementedError('subclasses must do')

    def rewrite_html(self):
        for child in self.children:
            if child is not None:
                child.rewrite_html()

    def __str__(self):
        return self.path

    @property
    def pk(self):
        if self._pk is None:
            raise AttributeError("Cannot get the primary key until it's installed")
        return self._pk

    @property
    def link_start_tag(self, attrs):
        raise NotImplementedError('subclasses must do')


class HTMLConverter(html.parser.HTMLParser):
    # Document link: <a id="PK" linktype="document">…</a>
    # Image: <embed alt="TITLE" embedtype="image" format="fullwidth" id="PK"/>
    # Page: <a id="PK" linktype="page">…</a>
    # External: <a href="https://what/ever">…</a>
    # <table> should have bootstrap class table

    def __init__(self, plone_export: PloneExport, obj: PloneObject):
        super().__init__(convert_charrefs=True)
        self.plone_export, self.obj, self._body = plone_export, obj, []

    @property
    def body(self) -> str:
        return ''.join(self._body)

    def _find_target_obj(self, link_target):
        if link_target.startswith('#'): return None
        if link_target.endswith('/'): link_target = link_target[:-1]
        link_components = link_target.split('/')
        if len(link_components) >= 2 and 'resolveuid' in link_components:
            target = self.plone_export.objs_by_uid.get(link_components[link_components.index('resolveuid') + 1])
            return target if target else None
        else:
            assert not link_target.startswith('/')
            # Possibilities: it's a direct descendent, it's a sibling, or somewhere else
            my_path_components = self.obj.path.split('/')
            while len(my_path_components) > 0:
                path = '/'.join(my_path_components) + '/' + link_target
                target = self.plone_export.objs_by_path.get(path)
                if target is not None: break
                my_path_components = my_path_components[:-1]
            # So maybe it's a top-level?
            if target is None:
                target = self.plone_export.objs_by_path.get(link_target)
            return target

    def handle_starttag(self, tag, attrs):
        assert tag != 'img'
        attrs = dict(attrs)
        if tag == 'a':
            link_target = attrs.get('href')
            if link_target is None:
                # It's an <a> with either a ``name`` or ``id`` but Wagtail doesn't support these
                # so skip 'em (see https://github.com/wagtail/wagtail/issues/2631)
                return
            elif link_target.startswith('mailto:') or link_target.startswith('tel:') or link_target.startswith('http'):
                self._body.append(f'<a href="{link_target}">')
            else:
                if '@@dataDispatch' in link_target:
                    self._body.append(f'<a href="/{link_target}">')
                else:
                    target = self._find_target_obj(link_target)
                    if target is not None:
                        self._body.append(target.link_start_tag(attrs))
                    # Else we drop the hyperlink
        elif tag == 'table':
            self._body.append('<table class="table table-striped">')
        else:
            # Otherwise it's a tag like <strong>, <em>, <cite>, etc…
            self._body.append(f'<{tag}>')

    def handle_endtag(self, tag):
        self._body.append(f'</{tag}>')

    _plone_wagtail_image_formats = {
        'image-left': 'left',
        'image-right': 'right',
        'image-inline': 'fullwidth',
    }

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self._body.append('<br/>')
        elif tag == 'img':
            attrs = dict(attrs)
            link_target = attrs.get('src')
            if not link_target: return
            target = self._find_target_obj(link_target)
            if not target: return
            attrs['alt'] = html.escape(attrs.get('alt', self.obj.title))
            attrs['img_format'] = self._plone_wagtail_image_formats.get(attrs.get('class', 'image-inline'))
            self._body.append(target.link_start_tag(attrs))
        elif tag == 'param':
            # Movies belong on YouTube etc.
            pass
        else:
            raise ValueError(f'Unexpected start/end tag {tag}')

    def handle_data(self, data):
        self._body.append(data)


class PlonePage(PloneObject):
    def __init__(self, plone_export, uid, path, item_id, title, description, children, body):
        super().__init__(plone_export, uid, path, item_id, title, description, children)
        self.body = body
        self.fp = None
        assert isinstance(body, str)

    def install(self, parent: Page):
        self.fp = FlexPage(title=self.title, live=True, show_in_menus=True)
        parent.add_child(instance=self.fp)
        self.fp.save()
        self._pk = self.fp.pk

        for child in self.children:
            if child is not None:
                child.install(self.fp)
        return self.fp

    def rewrite_html(self):
        super().rewrite_html()

        if self.fp is None:
            raise ValueError(f'Illegal state: page {self.path} ({self.uid}) must be installed before rewriting')

        # First, clean up the icky Plone code
        cp = subprocess.run(
            ['tidy', '-wrap', '-numeric', '-quiet', '-asxhtml', '-utf8', '--show-body-only', 'yes'],
            input=self.body.encode('utf-8'), capture_output=True, check=False
        )
        if cp.returncode == 2:
            raise ValueError(f'Cannot tidy this from Plone: «{self.body}»')
        tidy_body = cp.stdout.decode('utf-8')

        # Now, convert from Plone to Wagtail
        try:
            html_converter = HTMLConverter(self.plone_export, self)
            html_converter.feed(tidy_body)
            html_converter.close()
        except ValueError:
            # Ok, go back to the untidy version
            html_converter = HTMLConverter(self.plone_export, self)
            html_converter.feed(self.body)
            html_converter.close()
        converted_html = html_converter.body

        # Tidy again, removing any problems introduced during the conversion
        cp = subprocess.run(
            ['tidy', '-wrap', '-numeric', '-quiet', '-asxhtml', '-utf8', '--show-body-only', 'yes'],
            input=converted_html.encode('utf-8'), capture_output=True, check=False
        )
        if cp.returncode == 2:
            raise ValueError(f'Cannot tidy this from Wagtail: «{converted_html}»')
        tidied_and_converted = cp.stdout.decode('utf-8')

        self.fp.body.append(('rich_text', RichText(tidied_and_converted)))
        self.fp.save()

    def link_start_tag(self, attrs):
        return f'<a id="{self.pk}" linktype="page">'


class PloneLink(PlonePage):
    def __init__(self, plone_export, uid, path, item_id, title, description, url):
        body = render_to_string('edrnsite.ploneimport/link-view.html', {'url': url})
        super().__init__(plone_export, uid, path, item_id, title, description, None, body)


class PloneEvent(PlonePage):
    def __init__(self, plone_export, uid, path, item_id, title, description, d: dict):
        d['body_text'] = d['text']['data']
        body = render_to_string('edrnsite.ploneimport/event-view.html', d)
        super().__init__(plone_export, uid, path, item_id, title, description, None, body)


class PloneFile(PloneObject):
    def __init__(self, plone_export, uid, path, item_id, title, description, filename, content_type, blob):
        super().__init__(plone_export, uid, path, item_id, title, description)
        self.filename, self.content_type, self.blob = filename, content_type, blob

    def install(self, parent: Page):
        document = Document.objects.filter(title=self.title).first()
        if document is None:
            try:
                with open(self.blob, 'rb') as f:
                    document_file = File(f, name=self.filename)
                    document = Document(title=self.title, file=document_file)
                    document.save()
            except FileNotFoundError:
                with open(os.devnull, 'rb') as f:
                    document_file = File(f, name=self.filename)
                    document = Document(title=self.title, file=document_file)
                    document.save()
        self._pk = document.pk
        return document

    def link_start_tag(self, attrs):
        return f'<a id="{self.pk}" linktype="document">'


class PloneImage(PloneFile):
    def __init__(self, plone_export, uid, path, item_id, title, description, filename, content_type, blob):
        super().__init__(plone_export, uid, path, item_id, title, description, filename, content_type, blob)

    def install(self, parent: Page):
        image = Image.objects.filter(title=self.title).first()
        if image is None:
            try:
                with open(self.blob, 'rb') as f:
                    image_file = ImageFile(f, name=self.filename)
                    image = Image(title=self.title, file=image_file)
                    image.save()
            except FileNotFoundError:
                with open(os.devnull, 'rb') as f:
                    image_file = ImageFile(f, name=self.filename)
                    image = Image(title=self.title, file=image_file)
                    image.save()
        self._pk = image.pk
        return image

    def link_start_tag(self, attrs):
        img_format = attrs.get('img_format', 'fullwidth')
        if img_format is None: img_format = 'fullwidth'
        alt = attrs.get('alt', self.description if self.description else '«unknown»')
        return f'<embed alt="{alt}" embedtype="image" format="{img_format}" id="{self.pk}"/>'
