# encoding: utf-8

'''🦦 EDRN Site streams: CDE blocks.'''

from wagtail import blocks


class DataElementExplorerBlock(blocks.StructBlock):
    block_id = blocks.CharBlock(
        null=False, required=True, max_length=8, help_text='Short alphanumeric ID for this block'
    )
    title = blocks.CharBlock(
        null=False, required=False, max_length=80, help_text='Optional title to display for this explorer block'
    )
    spreadsheet_id = blocks.CharBlock(
        null=False, required=False, max_length=60,
        help_text="File ID of a Google Drive spreadsheet; don't forget to Update from Google Drive!"
    )
    class Meta:
        template = 'edrnsite.streams/data-element-explorer-block.html'
        icon = 'form'
        label = 'Data Element Explorer'
        help_text = 'A block that shows an explorer-like tree view of data elements from a Google spreadsheet'
