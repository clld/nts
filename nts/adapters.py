from __future__ import unicode_literals

from sqlalchemy.orm import joinedload, joinedload_all
from clld.interfaces import ILanguage, IParameter, IIndex
from clld.web.adapters.base import Index
from clld.web.adapters.geojson import (
    GeoJsonParameter,
    GeoJsonLanguages,
    GeoJsonCombinationDomainElement,
    pacific_centered_coordinates,
)
from clld.web.adapters.download import CsvDump
from clld.db.meta import DBSession
from clld.db.models.common import Value, ValueSet, DomainElement, Language, Parameter
from clld.web.maps import GeoJsonSelectedLanguages, SelectedLanguagesMap

from nts.models import ntsLanguage


class GeoJsonFeature(GeoJsonParameter):
    def feature_iterator(self, ctx, req):
        return DBSession.query(Value).join(DomainElement)\
            .filter(DomainElement.id == req.params.get('domainelement'))\
            .options(
                joinedload_all(Value.valueset, ValueSet.language),
                joinedload(Value.domainelement),
            )

    def get_language(self, ctx, req, value):
        return value.valueset.language

    def get_coordinates(self, language):
        return pacific_centered_coordinates(language)

    def feature_properties(self, ctx, req, value):
        return {
            'value_numeric': value.domainelement.number,
            'value_name': value.domainelement.name}


class GeoJsonCDE(GeoJsonCombinationDomainElement):
    def get_coordinates(self, language):
        return pacific_centered_coordinates(language)


class MapView(Index):
    extension = str('map.html')
    mimetype = str('text/vnd.clld.map+html')
    send_mimetype = str('text/html')
    template = 'language/map_html.mako'

    def template_context(self, ctx, req):
        languages = list(ctx.get_query(limit=8000))
        return {
            'map': SelectedLanguagesMap(
                ctx, req, languages, geojson_impl=GeoJsonSelectedLanguages),
            'languages': languages}


def includeme(config):
    config.register_adapter(GeoJsonFeature, IParameter)
    config.register_adapter(MapView, ILanguage, IIndex)
