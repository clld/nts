import codecs
from itertools import groupby

from sqlalchemy.orm import joinedload_all, joinedload
from path import path
from bs4 import BeautifulSoup as soup
from pyramid.httpexceptions import HTTPFound

from clld import RESOURCES
from clld.interfaces import IRepresentation
from clld.web.adapters import get_adapter
from clld.db.meta import DBSession
from clld.db.models.common import DomainElement, Contribution, ValueSet, Value
from clld.web.util.helpers import button, icon, JS_CLLD, get_referents, JS
from clld.web.util.multiselect import MultiSelect, CombinationMultiSelect
from clld.web.util.htmllib import HTML
from clld.web.icon import ICON_MAP

import nts
from nts.models import Feature, ntsLanguage
from nts.maps import CombinedMap


def comment_button(req, valueset, class_=''):
    return HTML.form(
        button(icon('comment'), type='submit', class_=class_, title='comment'),
        class_='inline',
        method='POST',
        action=req.resource_url(valueset))


def dataset_detail_html(context=None, request=None, **kw):
    return {
        'stats': context.get_stats([rsc for rsc in RESOURCES if rsc.name in ['language', 'parameter', 'value']]),
        'stats_datapoints': "TODO"
    }


def icons(req, param):
    icon_map = req.registry.settings['icons']
    td = lambda spec: HTML.td(
        HTML.img(
            src=req.static_url('clld:web/static/icons/' + icon_map[spec] + '.png'),
            height='20',
            width='20'),
        onclick='NTS.reload({"%s": "%s"})' % (param, spec))
    rows = [
        HTML.tr(*map(td, icons)) for c, icons in
        groupby(sorted(icon_map.keys()), lambda spec: spec[0])]
    return HTML.div(
        HTML.table(
            HTML.tbody(*rows),
            class_="table table-condensed"
        ),
        button('Close', **{'data-dismiss': 'clickover'}))


#def source_detail_html(context=None, request=None, **kw):
#    return {'referents': get_referents(context)}


def _valuesets(parameter):
    return DBSession.query(ValueSet)\
        .filter(ValueSet.parameter_pk == parameter.pk)\
        .options(
            joinedload(ValueSet.language),
            joinedload_all(ValueSet.values, Value.domainelement))


def parameter_detail_html(context=None, request=None, **kw):
    return dict(select=CombinationMultiSelect(request, selected=[context]))


def parameter_detail_tab(context=None, request=None, **kw):
    query = _valuesets(context).options(
        joinedload_all(ValueSet.language, ntsLanguage.family))
    return dict(datapoints=query)


def combination_detail_html(context=None, request=None, **kw):
    """feature combination view
    """
    return dict(
        select=CombinationMultiSelect(request, combination=context),
        map=CombinedMap(context, request))
