# encoding: utf-8

'''😌 EDRN Site Content: table translator command.'''


from django.core.management.base import BaseCommand
from edrnsite.content.models import FlexPage
from html.parser import HTMLParser
from wagtail.rich_text import RichText
from io import StringIO


class _TableConverter(HTMLParser):
    def __init__(self, blocks, command):
        super().__init__()
        self.blocks, self.command, self.in_table, self.buffer = blocks, command, False, StringIO()
        self._reset_for_tables()

    def _reset_for_tables(self):
        self.cell          = StringIO()
        self.columns       = []
        self.has_header    = False
        self.in_table      = False
        self.rows          = []
        self.table_caption = None

    def _append_block(self):
        if self.in_table:
            table_info = {
                'cell': [],  # What is this even for?
                'data': self.rows,
                'first_col_is_header': False,  # We don't use these
                'first_row_is_table_header': self.has_header
            }
            if self.table_caption is not None:
                table_info['table_caption'] = self.table_caption
            self.blocks.append(('table', table_info))
            self._reset_for_tables()
        else:
            self.blocks.append(('rich_text', RichText(self.buffer.getvalue().strip())))
            self.buffer = StringIO()

    def _format_starttag(self, tag, attrs, empty):
        if not attrs:
            return f'<{tag}/>' if empty else f'<{tag}>'
        start = f'<{tag} '
        middle = []
        for key, value in attrs:
            middle.append(f'{key}="{value}"')
        middle = ' '.join(middle)
        end = '/>' if empty else '>'
        return start + middle + end

    def _find_summary(self, attrs):
        summary = None
        for key, value in attrs:
            if key == 'summary':
                summary = value
                break
        return summary

    def handle_starttag(self, tag, attrs):
        assert tag not in ('colgroup', 'caption', 'tfoot')
        if tag == 'table':
            self._append_block()
            self.in_table = True
            self.table_caption = self._find_summary(attrs)
        elif self.in_table:
            if tag == 'thead':
                self.has_header = True
        else:
            self.buffer.write(self._format_starttag(tag, attrs, empty=False))

    def handle_endtag(self, tag):
        if tag == 'table':
            self._append_block()
        elif tag == 'tr':
            self.rows.append(self.columns)
            self.columns = []
        elif tag in ('td', 'th'):
            self.columns.append(self.cell.getvalue().strip())
            self.cell = StringIO()
        elif tag in ('tbody', 'thead'):
            pass
        else:
            self.buffer.write(f'</{tag}>\n')

    def handle_startendtag(self, tag, attrs):
        assert tag != 'table'
        self.buffer.write(self._format_starttag(tag, attrs, empty=True))

    def handle_data(self, data):
        buffer = self.cell if self.in_table else self.buffer
        buffer.write(data)

    def close(self):
        if self.buffer.getvalue():
            self._append_block()
        super().close()

    # Won't have to handle entityrefs, charrefs, comments, decls, pis, or unknonw decls


class Command(BaseCommand):
    help = 'Convert <tables> in RichText to TableBlocks'

    def _convert(self, page: FlexPage):
        # Skip FlexPages with multiple rich_text; these are just for collaborative groups and have no tables
        if len(page.body) != 1: return

        # Skip FlexPages that don't have a rich_text
        if page.body[0].block_type != 'rich_text': return

        # Skip FlexPages with a single rich_text without a single <table>
        if '<table' not in page.body[0].value.source: return
        # if len(page.body[0].value.source.split('<table')) != 2: return

        original = page.body[0].value.source
        del page.body[0]
        self.stdout.write(f'Converting page "{page.title}"')
        converter = _TableConverter(page.body, self)
        converter.feed(original)
        converter.close()
        page.save()

    def handle(self, *args, **options):
        self.stdout.write('Converting tables in RichText to TableBlocks')

        pages = FlexPage.objects.all()
        count = pages.count()
        self.stdout.write(f'Pages to consider: {count}')

        for page in pages:
            self._convert(page)