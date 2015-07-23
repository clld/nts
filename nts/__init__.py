from pyramid.config import Configurator
import re
from functools import partial
from path import path
from clld.interfaces import (
    IParameter, IMapMarker, IDomainElement, IValue, ILanguage, IBlog,
)
from clld.web.adapters.base import adapter_factory
from clld.web.app import menu_item

# we must make sure custom models are known at database initialization!
from nts import models
from nts.blog import Blog


def map_marker(ctx, req):
    """to allow for user-selectable markers, we have to look up a possible custom
    selection from the url params.
    """
    icon = None
    if IValue.providedBy(ctx):
        icon = ctx.domainelement.jsondata['icon']
    elif IDomainElement.providedBy(ctx):
        icon = ctx.jsondata['icon']
    elif ILanguage.providedBy(ctx):
        icon = ctx.family.jsondata['icon']
    if icon:
        return req.static_url('clld:web/static/icons/' + icon + '.png')


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

    utilities = [
        (map_marker, IMapMarker),
        (Blog(settings), IBlog),
    ]
    config = Configurator(settings=settings)
    config.include('clldmpg')
    config.register_menu(
        ('dataset', partial(menu_item, 'dataset', label='Home')),
        ('parameters', partial(menu_item, 'parameters', label='Features')),
        ('languages', partial(menu_item, 'languages')),
        ('sources', partial(menu_item, 'sources')),
        ('designers', partial(menu_item, 'contributions', label="Contributors")),
    )

    config.include('nts.adapters')
    config.include('nts.datatables')
    config.include('nts.maps')

    config.register_adapter(adapter_factory(
        'parameter/detail_tab.mako',
        mimetype='application/vnd.clld.tab',
        send_mimetype="text/plain",
        extension='tab',
        name='tab-separated values'), IParameter)

    return config.make_wsgi_app()
