from sqlalchemy.orm import joinedload_all, joinedload

from clld import RESOURCES
from clld.db.meta import DBSession
from clld.db.models.common import ValueSet, Value
from clld.web.util.multiselect import CombinationMultiSelect

from nts.models import ntsLanguage
from nts.maps import CombinedMap


def dataset_detail_html(context=None, request=None, **kw):
    return {
        'stats': context.get_stats([rsc for rsc in RESOURCES if rsc.name in ['language', 'parameter', 'value']]),
        'stats_datapoints': "TODO"
    }


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
