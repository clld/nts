from sqlalchemy.orm import joinedload, joinedload_all

from clld.db.models import common
from clld.web import datatables
from clld.web.datatables.base import Col, LinkCol, DetailsRowLinkCol, IdCol, LinkToMapCol
from clld.web.datatables.value import Values, ValueNameCol
from clld_glottologfamily_plugin.datatables import FamilyCol, MacroareaCol

from nts.models import FeatureDomain, Feature, ntsLanguage, ntsValue, Designer
from nts.util import comment_button


class FeatureIdCol(IdCol):
    def search(self, qs):
        if self.model_col:
            return self.model_col.contains(qs)

    def order(self):
        return Feature.sortkey_str, Feature.sortkey_int


class Features(datatables.Parameters):
    def base_query(self, query):
        return query\
            .join(Designer).options(joinedload_all(Feature.designer))\
            .join(FeatureDomain).options(joinedload_all(Feature.featuredomain))

    def col_defs(self):
        return [
            FeatureIdCol(self, 'Id', sClass='left', model_col=Feature.id),
            LinkCol(self, 'Feature', model_col=Feature.name),
            Col(self, 'Abbreviation', model_col=Feature.abbreviation),
            Col(self, 'Morphosynunit', model_col=Feature.jl_relevant_unit),
            Col(self, 'Form', model_col=Feature.jl_formal_means),
            Col(self, 'Function', model_col=Feature.jl_function),
            Col(self,
                'Designer',
                model_col=Designer.contributor,
                get_object=lambda i: i.designer),
            Col(self, 'Languages', model_col=Feature.representation),
            DetailsRowLinkCol(self, 'd', button_text='Values'),
        ]


class Languages(datatables.Languages):
    def base_query(self, query):
        return query.outerjoin(ntsLanguage.family).options(joinedload(ntsLanguage.family))

    def col_defs(self):
        return [
            LinkCol(self, 'Name', model_col=ntsLanguage.name),
            IdCol(self, 'ISO-639-3', sClass='left', model_col=ntsLanguage.id),
            FamilyCol(self, 'Family', language_cls=ntsLanguage),
            MacroareaCol(self, 'Macro_Area', language_cls=ntsLanguage),
            Col(self, 'Features', model_col=ntsLanguage.representation),
            LinkToMapCol(self, 'm'),
        ]


class Designers(datatables.Contributions):
    def col_defs(self):
        return [
            Col(self, 'Designer', model_col=Designer.contributor),
            Col(self, 'Domain of Design', model_col=Designer.domain),
            Col(self, 'Citation', model_col=Designer.citation),
            Col(self, 'More Information', model_col=Designer.pdflink),
        ]


class CommentCol(Col):
    __kw__ = dict(bSortable=False, bSearchable=False)

    def format(self, item):
        return comment_button(self.dt.req, item.valueset)


class Datapoints(Values):
    def base_query(self, query):
        query = Values.base_query(self, query)
        if self.language:
            query = query.options(
                joinedload_all(common.Value.valueset, common.ValueSet.parameter),
                joinedload(common.Value.domainelement),
            )
        return query

    def col_defs(self):
        name_col = ValueNameCol(self, 'value')
        if self.parameter and self.parameter.domain:
            name_col.choices = [(de.name, de.description) for de in self.parameter.domain]

        cols = []
        if self.parameter:
            cols = [
                LinkCol(
                    self, 'Name',
                    model_col=common.Language.name,
                    get_object=lambda i: i.valueset.language),
                Col(
                    self, 'ISO-639-3',
                    model_col=common.Language.id,
                    get_object=lambda i: i.valueset.language)]
        elif self.language:
            cols = [
                LinkCol(
                    self, 'Feature',
                    model_col=common.Parameter.name,
                    get_object=lambda i: i.valueset.parameter),
                FeatureIdCol(
                    self, 'Feature Id',
                    sClass='left', model_col=common.Parameter.id,
                    get_object=lambda i: i.valueset.parameter)]

        cols = cols + [
            name_col,
            Col(self, 'Source',
                model_col=common.ValueSet.source,
                get_object=lambda i: i.valueset),
            Col(self, 'Comment', model_col=ntsValue.comment),
            CommentCol(self, '_'),
        ]
        return cols

    def get_options(self):
        if self.language or self.parameter:
            # if the table is restricted to the values for one language, the number of
            # features is an upper bound for the number of values; thus, we do not
            # paginate.
            return {'bLengthChange': False, 'bPaginate': False}


def includeme(config):
    config.register_datatable('contributions', Designers)
    config.register_datatable('values', Datapoints)
    config.register_datatable('languages', Languages)
    config.register_datatable('parameters', Features)
