from zope.interface import implementer
from sqlalchemy import (
    Column,
    String,
    Unicode,
    Integer,
    ForeignKey,
)
from sqlalchemy.orm import relationship, backref

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin
from clld.db.versioned import Versioned
from clld.db.models.common import (
    Language,
    Parameter,
    Contribution,
    IdNameDescriptionMixin,
    Value,
)
from nts import interfaces as nts_interfaces


#-----------------------------------------------------------------------------
# specialized common mapper classes
#-----------------------------------------------------------------------------


@implementer(nts_interfaces.IFamily)
class Family(Base, IdNameDescriptionMixin, Versioned):
    pass


@implementer(interfaces.ILanguage)
class ntsLanguage(CustomModelMixin, Language):
    pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)
    family_pk = Column(Integer, ForeignKey('family.pk'))
    family = relationship(Family, backref=backref("languages", order_by="Language.name"))
    representation = Column(Integer)
    macroarea = Column(Unicode)


@implementer(interfaces.IValue)
class ntsValue(CustomModelMixin, Value):
    pk = Column(Integer, ForeignKey('value.pk'), primary_key=True)
    comment = Column(Unicode)
    example = Column(Unicode)
    contributed_datapoint = Column(Unicode)

    def __unicode__(self):
        return self.domainelement.description if self.domainelement else self.name or self.id


class FeatureDomain(Base, Versioned):
    name = Column(Unicode, unique=True)


@implementer(interfaces.IContribution)
class Designer(CustomModelMixin, Contribution, Versioned):
    """Contributions in NTS are designers. These comprise a set of
    features with corresponding values and a descriptive text.
    """
    pk = Column(Integer, ForeignKey('contribution.pk'), primary_key=True)
    domain = Column(Unicode)
    contributor = Column(Unicode)
    pdflink = Column(Unicode)
    citation = Column(Unicode)


@implementer(interfaces.IParameter)
class Feature(CustomModelMixin, Parameter, Versioned):
    """Parameters in NTS are called feature. They are always related to one Designer.
    """
    pk = Column(Integer, ForeignKey('parameter.pk'), primary_key=True)
    doc = Column(String)
    vdoc = Column(String)
    name_french = Column(String)
    clarification = Column(String)
    alternative_id = Column(String)
    representation = Column(Integer)
    featuredomain_pk = Column(Integer, ForeignKey('featuredomain.pk'))
    featuredomain = relationship(FeatureDomain, lazy='joined')
    designer_pk = Column(Integer, ForeignKey('designer.pk'))
    designer = relationship(Designer, lazy='joined', backref="features")
    dependson = Column(String)
    abbreviation = Column(String)
    sortkey_str = Column(String)
    sortkey_int = Column(Integer)
    jl_relevant_unit = Column(String)
    jl_function = Column(String)
    jl_formal_means = Column(String)

    def __solr__(self, req):
        res = Parameter.__solr__(self, req)
        res.update(featuredomain_t=self.featuredomain.name)
        return res
