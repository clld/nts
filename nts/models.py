from zope.interface import implementer
from sqlalchemy import (
    Column,
    String,
    Unicode,
    Integer,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin
from clld.db.versioned import Versioned
#from clld.db.models.common import Language
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

    def __unicode__(self):
        return self.domainelement.description if self.domainelement else self.name or self.id


class FeatureDomain(Base, Versioned):
    pk = Column(String, primary_key=True)
    name = Column(String, unique=True)


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
    #id = Column(Integer, unique=True)
    #sortkey = Column(Integer)
    #wp_slug = Column(Unicode)
    #area_pk = Column(Integer, ForeignKey('area.pk'))
    #area = relationship(Area, lazy='joined')


@implementer(interfaces.IParameter)
class Feature(CustomModelMixin, Parameter, Versioned):
    """Parameters in NTS are called feature. They are always related to one Designer.
    """
    #__table_args__ = (UniqueConstraint('contribution_pk', 'ordinal_qualifier'),)
    #__table_args__ = (UniqueConstraint('designer_pk'),)
    pk = Column(Integer, ForeignKey('parameter.pk'), primary_key=True)
    #contribution_pk = Column(Integer, ForeignKey('contribution.pk'))
    id = Column(String(50), unique=True)
    name = Column(String(600), unique=True)
    doc = Column(String)
    vdoc = Column(String)
    name_french = Column(String)
    clarification = Column(String)
    alternative_id = Column(String)
    representation = Column(Integer)
    featuredomain_pk = Column(String, ForeignKey('featuredomain.pk'))
    featuredomain = relationship(FeatureDomain, lazy='joined')
    designer_pk = Column(Integer, ForeignKey('designer.pk'))
    designer = relationship(Designer, lazy='joined', backref="features")
    dependson = Column(String)
    abbreviation = Column(String)
    sortkey_str = Column(String)
    sortkey_int = Column(Integer)
    #chapter = relationship(Chapter, lazy='joined', backref="features")
#CREATE table features(fid VARCHAR(600) BINARY NOT NULL, fdoc VARCHAR(1000), vdoc VARCHAR(1000), grp VARCHAR(1000), designer VARCHAR(100), dependson VARCHAR(600) references features(fid), PRIMARY KEY (fid(600)));

    def __solr__(self, req):
        res = Parameter.__solr__(self, req)
        res.update(featuredomain_t=self.featuredomain.name)
        return res





