import re
from functools import partial

from pyramid.config import Configurator
from path import path

from clld.interfaces import IParameter, IMapMarker, IDomainElement, IValue, IBlog
from clld.web.adapters.base import adapter_factory
from clld.web.app import menu_item
from clld_glottologfamily_plugin.util import LanguageByFamilyMapMarker

# we must make sure custom models are known at database initialization!
from nts import models
from nts.blog import Blog


class NtsMapMarker(LanguageByFamilyMapMarker):
    def get_icon(self, ctx, req):
        """to allow for user-selectable markers, we have to look up a possible custom
        selection from the url params.
        """
        icon = None
        if IValue.providedBy(ctx):
            icon = ctx.domainelement.jsondata['icon']
        elif IDomainElement.providedBy(ctx):
            icon = ctx.jsondata['icon']
        if icon:
            return icon
        return super(NtsMapMarker, self).get_icon(ctx, req)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    convert = lambda spec: ''.join(c if i == 0 else c + c for i, c in enumerate(spec))
    filename_pattern = re.compile('(?P<spec>(c|d|s|f|t)[0-9a-f]{3})\.png')
    icons = {}
    for name in sorted(
        path(__file__).dirname().joinpath('static', 'icons').files()
    ):
        m = filename_pattern.match(name.splitall()[-1])
        if m:
            icons[m.group('spec')] = convert(m.group('spec'))
    settings['icons'] = icons

    config = Configurator(settings=settings)
    config.include('clldmpg')
    config.include('clld_glottologfamily_plugin')
    config.registry.registerUtility(NtsMapMarker(), IMapMarker)
    config.registry.registerUtility(Blog(settings), IBlog)
    config.register_menu(
        ('dataset', partial(menu_item, 'dataset', label='Home')),
        ('parameters', partial(menu_item, 'parameters', label='Features')),
        ('languages', partial(menu_item, 'languages')),
        ('sources', partial(menu_item, 'sources')),
        ('designers', partial(menu_item, 'contributions', label="Contributors")),
    )
    config.register_adapter(adapter_factory(
        'parameter/detail_tab.mako',
        mimetype='application/vnd.clld.tab',
        send_mimetype="text/plain",
        extension='tab',
        name='tab-separated values'), IParameter)
    return config.make_wsgi_app()
