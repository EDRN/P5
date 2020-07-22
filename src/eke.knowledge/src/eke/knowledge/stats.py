# encoding: utf-8

u'''…'''

from five import grok
from plone.memoize.view import memoize
from plone.app.layout.navigation.interfaces import INavigationRoot
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import logging, cStringIO


_logger = logging.getLogger(__name__)


class Stats(grok.View):
    u'''Ad hoc graphics'''
    grok.context(INavigationRoot)
    grok.name('stats')
    grok.require('zope2.View')
    @memoize
    def render(self):
        graphic = self.request.form.get('graphic')
        if not graphic:
            raise ValueError('The graphic parameter is required')
        if graphic != 'home':
            raise ValueError('Unknown graphic type: {}'.format(graphic))

        self.request.response.setHeader('Content-type', 'image/png; charset=utf-8')
        self.request.response.setHeader('Content-Transfer-Encoding', '8bit')

        labels = ['Breast', 'Bone', 'Brain', 'Anus']
        sizes = [15, 30, 45, 10]
        explode = (0, 0.1, 0, 0)

        fig = Figure()
        ax = fig.subplots()
        ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
        ax.axis('equal')
        canvas = FigureCanvasAgg(fig)
        buf = cStringIO.StringIO()
        canvas.print_png(buf)
        return buf.getvalue()

        # This wants to draw a windw on the server which is headless:
        # fig1, ax1 = matplotlib.pyplot.subplots()
        # ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
        # ax1.axis('equal')
