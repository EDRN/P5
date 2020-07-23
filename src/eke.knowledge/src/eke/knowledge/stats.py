# encoding: utf-8

u'''…'''

from .biomarker import IBiomarker
from .dataset import IDataset
from .protocol import IProtocol
from .publication import IPublication
from five import grok
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from zope.interface import Interface
from plone.memoize.view import memoize
import logging, cStringIO, plone.api, collections


_logger = logging.getLogger(__name__)


class Stats(grok.View):
    u'''Ad hoc graphics'''
    grok.context(Interface)
    grok.name('stats')
    grok.require('zope2.View')

    _friendlyNames = {
        'eke.knowledge.biomarkerpanel': 'Biomarker',
        'eke.knowledge.dataset': 'Dataset',
        'eke.knowledge.elementalbiomarker': 'Biomarker',
        'eke.knowledge.protocol': 'Protocol',
        'eke.knowledge.publication': 'Publication'
    }

    def _generateFigure(self, size=None):
        if size is None: size = (4, 4)
        return Figure(figsize=size, dpi=72, facecolor='None', edgecolor='None')

    @memoize
    def graph_sample(self):
        labels = ['Breast', 'Bone', 'Brain', 'Anus']
        sizes = [15, 30, 45, 200]
        explode = (0, 0.1, 0, 0)

        figure = self._generateFigure()
        ax = figure.subplots()
        ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
        ax.axis('equal')
        return figure

    @memoize
    def graph_knowledgeObjects(self):
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(object_provides=[
            IBiomarker.__identifier__,
            IDataset.__identifier__,
            IProtocol.__identifier__,
            IPublication.__identifier__
        ])
        cnt = collections.Counter()
        for i in results:
            friendlyName = self._friendlyNames.get(i.portal_type)
            if friendlyName:
                cnt[friendlyName] += 1

        figure = self._generateFigure(size=(4, 4))
        axis1 = figure.subplots()
        axis1.bar(cnt.keys(), cnt.values())
        axis1.set_title('Knowledge Environment', fontdict={'weight': 'bold'})
        return figure

    @memoize
    def graph_biomarkers(self):
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(object_provides=IBiomarker.__identifier__)
        cnt = collections.Counter()
        for i in results:
            for j in i.indicatedBodySystems:
                cnt[j] += 1
        figure = self._generateFigure()
        axis1 = figure.subplots()
        axis1.pie(cnt.values(), labels=cnt.keys(), autopct='%1.0f%%', shadow=True, rotatelabels=False)
        axis1.axis('equal')
        axis1.set_title('Biomarkers', fontdict={'weight': 'bold'})
        return figure

    @memoize
    def graph_datasets(self):
        catalog = plone.api.portal.get_tool('portal_catalog')
        results = catalog(object_provides=IDataset.__identifier__)
        cnt = collections.Counter()
        for i in results:
            cnt[i.bodySystemName] += 1
        figure = self._generateFigure((4, 4))
        axis1 = figure.subplots()
        # axis1.bar(cnt.keys(), cnt.values())
        axis1.pie(cnt.values(), labels=cnt.keys(), autopct='%1.0f%%', shadow=True, rotatelabels=False)
        axis1.set_title('Datasets', fontdict={'weight': 'bold'})
        return figure

    def render(self):
        graphic = self.request.form.get('graphic')
        if not graphic:
            raise ValueError('The graphic parameter is required')
        if not graphic.startswith('graph_'):
            raise ValueError('The graphic parameter must start with "graph_')
        method = getattr(self, graphic, None)
        if method is None:
            raise ValueError('The graphic method is unknown')

        self.request.response.setHeader('Content-type', 'image/png; charset=utf-8')
        self.request.response.setHeader('Content-Transfer-Encoding', '8bit')

        figure = method()
        canvas = FigureCanvasAgg(figure)
        buf = cStringIO.StringIO()
        canvas.print_png(buf)
        return buf.getvalue()

        # This wants to draw a windw on the server which is headless:
        # fig1, ax1 = matplotlib.pyplot.subplots()
        # ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
        # ax1.axis('equal')
