# encoding: utf-8

'''🦦 EDRN Site streams: views.'''

from edrn.auth.views import logged_in_or_basicauth
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.apps import apps
from wagtail.blocks.stream_block import StreamValue
from ._data_elements import _ExplorerTreeUpdater
from typing import Generator


def _get_referrer(request: HttpRequest) -> str:
    try:
        return request.META['HTTP_REFERER']
    except KeyError:
        return '/'


def _update_tree_from_spreadsheet(spreadsheet_id: str) -> str:
    updater = _ExplorerTreeUpdater(spreadsheet_id)
    results = '\n'.join(updater.update())
    return f'<h1>{spreadsheet_id}</h1><pre>{results}</pre>'


def _find_data_explorer_blocks(stream_value: StreamValue) -> Generator[str, None, None]:
    for block in stream_value:
        if block.block_type == 'data_explorer':
            yield block
        elif hasattr(block.value, 'stream_data'):
            yield from _find_data_explorer_blocks(block.value)


def update_data_element_explorer_trees() -> list[str]:
    # Cannot import edrnsite.content (circular dependency):
    FlexPage = apps.get_model('edrnsitecontent', 'FlexPage')
    results = []
    for fp in FlexPage.objects.all():
        for deb in _find_data_explorer_blocks(fp.body):
            spreadsheet_id = deb.value.get('spreadsheet_id')
            if spreadsheet_id:
                results.append(_update_tree_from_spreadsheet(spreadsheet_id))
    return results


@logged_in_or_basicauth('edrn')
def update_data_element_explorers(request: HttpRequest) -> HttpResponse:
    if request.user.is_staff or request.user.is_superuser:
        return HttpResponse(update_data_element_explorer_trees(), content_type='text/html')
    else:
        return HttpResponseForbidden()
