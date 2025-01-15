# encoding: utf-8

'''🦦 EDRN Site streams: data element trees.'''


from django.db import models
from wagtail.admin.panels import FieldPanel
import dataclasses, logging, traceback, tempfile, gdown, pandas, os

_logger = logging.getLogger(__name__)


@dataclasses.dataclass(order=True)
class _Attribute:
    '''A temporary attribute of a node before getting serialized into Django objects.'''
    text: str
    definition: str
    required: str
    data_type: str
    explanatory_note: str
    permissible_values: list[str]
    inheritance: bool
    def __hash__(self):
        return hash(self.text)
    def instantiate(self, obj):
        attr_obj = DataElementExplorerAttribute(
            text=self.text, definition=self.definition, required=self.required, data_type=self.data_type,
            explanatory_note=self.explanatory_note, obj=obj, inheritance=self.inheritance
        )
        attr_obj.save()
        for pv in self.permissible_values:
            cde_pv = DataElementExplorerPermissibleValue(value=pv, attribute=attr_obj)
            cde_pv.save()
        return attr_obj


@dataclasses.dataclass(order=True)
class _Node:
    '''A temporary node in a tree before getting serialized into Django objects.'''
    name: str
    description: str
    stewardship: str
    attributes: list[_Attribute]
    children: set[object] = dataclasses.field(default_factory=set, init=False, compare=False)
    def __hash__(self):
        return hash(self.name)
    def instantiate(self, parent=None):
        explorer_obj = DataElementExplorerObject(
            name=self.name, description=self.description, stewardship=self.stewardship, parent=parent
        )
        explorer_obj.save()
        for c in self.children:
            c.instantiate(explorer_obj)
        for a in self.attributes:
            a.instantiate(explorer_obj)
        return explorer_obj


class DataElementExplorerObject(models.Model):
    name = models.CharField(null=False, blank=False, max_length=200, help_text='Name of this object in a CDE hierarchy')
    description = models.TextField(null=False, blank=True, help_text='A nice long description of this object')
    stewardship = models.TextField(null=False, blank=True, help_text="Who's responsible for this object")
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE, related_name='children')
    spreadsheet_id = models.CharField(null=False, blank=True, help_text='If a root node, the spreadsheet that generates this node')
    panels = [FieldPanel('name'), FieldPanel('description'), FieldPanel('parent'), FieldPanel('spreadsheet_id')]
    def __str__(self):
        return self.name
    class Meta:
        indexes = [models.Index(fields=['spreadsheet_id'])]


class DataElementExplorerAttribute(models.Model):
    text = models.CharField(null=False, blank=False, max_length=100, help_text='Name of this common data element')
    obj = models.ForeignKey(DataElementExplorerObject, null=True, on_delete=models.CASCADE, related_name='attributes')
    definition = models.TextField(null=False, blank=True, help_text='A thorough definition of this CDE')
    required = models.CharField(null=False, blank=True, max_length=50, help_text='Required, not, or something else?')
    data_type = models.CharField(null=False, blank=True, max_length=30, help_text='Kind of data')
    explanatory_note = models.TextField(null=False, blank=True, help_text='Note helping explain use of the CDE')
    inheritance = models.BooleanField(null=False, blank=False, default=False, help_text='Attribute inherits values')
    panels = [
        FieldPanel('text'),
        FieldPanel('obj'),
        FieldPanel('definition'),
        FieldPanel('required'),
        FieldPanel('data_type'),
        FieldPanel('explanatory_note'),
        FieldPanel('inheritance')
    ]
    def __str__(self):
        return self.text


class DataElementExplorerPermissibleValue(models.Model):
    value = models.CharField(
        null=False, blank=False, max_length=200,
        help_text='An enumerated value allowed for a data element that uses permissible values'
    )
    attribute = models.ForeignKey(DataElementExplorerAttribute, null=True,  on_delete=models.CASCADE, related_name='permissible_values')
    panels = [FieldPanel('value'), FieldPanel('attribute')]
    def __str__(self):
        return self.value


class _ExplorerTreeUpdater:
    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.log = []

    def _read_sheet(self, url):
        '''Read the spreadsheet at ``url`` and return it.'''
        fd, fn = tempfile.mkstemp('.xlsx')
        os.close(fd)
        self._log(f'Downloading {self.spreadsheet_id} from Gdrive')
        # use_cookies must be False to work on tumor.jpl.nasa.gov
        fn = gdown.download(id=self.spreadsheet_id, output=fn, quiet=True, use_cookies=False, format='xlsx')
        # gdown doesn't raise an exception on error, but returns None as the filename—even when we pass
        # in the filename we want to use; see wkentaro/gdown#276
        if fn is None:
            raise ValueError('Error reading from gdown; check console log as gdown does not pass this info along')
        return fn

    def _parse_attributes(self, name, sheet):
        '''Using the data in ``sheet``, find the tab ``name`` and get all the attributes there.'''
        self._log(f'Parsing attributes in tab "{name}"')

        frame = sheet[name]
        row_number, attrs = 0, []
        for text in frame['Text']:
            # Gather data from the spreadsheet tab
            pvs_text, defn = frame['Permissible Values'][row_number], frame['Definition'][row_number]
            req, dt = frame['Requirement'][row_number], frame['Data Type'][row_number]
            note, inheritance = frame['Explanatory Note'][row_number], frame['Inheritance'][row_number]

            # Handle the empty cells
            pvs  = [] if pandas.isna(pvs_text) else [i.strip() for i in pvs_text.split('\n')]
            defn = '' if pandas.isna(defn) else defn
            req  = '' if pandas.isna(req) else req
            dt   = '' if pandas.isna(dt) else dt
            note = '' if pandas.isna(note) else note
            inh  = False if pandas.isna(inheritance) else inheritance

            # Create the temporary attribute and add it to the sequence
            attrs.append(_Attribute(text, defn, req, dt, note, pvs, inh))
            row_number += 1
        return attrs

    def _parse_structure(self, sheet):
        '''Using the data ``sheet``, produce a sequence of tree structure that match.'''

        # First, catalog all the nodes and ensure they all have tabs
        self._log('Parsing overall structure in the "Structure" tab and looking for referenced tabs')
        row_number, nodes, roots, structure = 0, {}, [], sheet['Structure']
        for name in structure['Object']:
            description, stewardship = structure['Description'][row_number], structure['Stewardship'][row_number]
            attributes = self._parse_attributes(name, sheet)
            stewardship = '' if pandas.isna(stewardship) else stewardship
            nodes[name] = _Node(name, description, stewardship, attributes)
            row_number += 1

        # Now connect parents to children and gather the roots
        self._log('Connecting child objects to parents')
        row_number = 0
        for name in structure['Object']:
            node = nodes[name]
            parents = structure['Parent'][row_number]
            if pandas.isna(parents):
                roots.append(node)
            else:
                # This handles multiple parents? What does that even mean?
                for parent_name in [i.strip() for i in parents.split(',')]:
                    parent = nodes[parent_name]
                    parent.children.add(node)
            row_number += 1

        # Tell the roots
        self._log(f'Total root objects: {len(roots)}: {", ".join([i.name for i in roots])}')
        return roots

    def _delete_obj(self, obj):
        '''Delete all the CDE explorer objects at and beneath ``obj``.

        It deletes all child objects of ``obj``. It also deletes all the attributes of ``obj`` and
        its children, plus all their permissible values.
        '''
        for attr in obj.attributes.all():
            for pv in attr.permissible_values.all():
                pv.delete()
            attr.delete()
        for child in obj.children.all():
            self._delete_obj(child)
        obj.delete()

    def _delete_old_explorer_objects(self):
        self._log(f'Deleting old explorer objects for {self.spreadsheet_id}')
        for obj in DataElementExplorerObject.objects.filter(spreadsheet_id=self.spreadsheet_id):
            self._delete_obj(obj)

    def update(self) -> list[str]:
        try:
            self._log(f'Reading spreadsheet {self.spreadsheet_id}')
            sheet_filename = self._read_sheet(self.spreadsheet_id)
            sheet = pandas.read_excel(sheet_filename, sheet_name=None)
            roots = self._parse_structure(sheet)

            # At this point, the data in the sheet passes muster, so we drop the old objects and
            # instantiate the new
            self._delete_old_explorer_objects()

            self._log('Installing new explorer objects')
            for root in roots:
                explorer_obj = root.instantiate()
                explorer_obj.spreadsheet_id = self.spreadsheet_id
                explorer_obj.save()       

        except Exception as ex:
            self._log(f'Exception {ex.__class__.__name__}; aborting update on spreadsheet {self.spreadsheet_id}')
            self._log(traceback.format_exc())
            _logger.exception('Abort')
        finally:
            return self.log

    def _log(self, message: str):
        _logger.warning(message)
        self.log.append(message)
