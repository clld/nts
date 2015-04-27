# coding: utf8
from __future__ import unicode_literals
import sys
import transaction

from pytz import utc
from datetime import date, datetime
#import MySQLdb

from clld.scripts.util import initializedb, Data, gbs_func, bibtex2source, glottocodes_by_isocode
from clld.db.meta import DBSession
from clld.db.models import common
from clld.db.util import compute_language_sources
from clld.db.util import get_distinct_values
from clld.lib.bibtex import unescape
from clld.lib.bibtex import EntryType, Record
from clld.util import slug

import nts
from nts import models

import issues

import re
import os
reline = re.compile("[\\n\\r]")
refield = re.compile("\\t")


def ktfbib(s):
    rs = [z.split(":::") for z in s.split("|||")]
    [k, typ] = rs[0]
    return (k, (typ, dict(rs[1:])))

def dtab(fn = "nts_test.tab", encoding = "utf-8"):
    lines = reline.split(loadunicode(fn, encoding = encoding))
    lp = [[x.strip() for x in refield.split(l)] for l in lines if l.strip()]
    topline = lp[0]
    lpd = [dict(zip(topline, l) + [("fromfile", fn)]) for l in lp[1:]]
    return lpd

def opv(d, func):
    n = {}
    for (i, v) in d.iteritems():
        n[i] = func(v)
    return n

def setd(ds, k1, k2, v = None):
    if ds.has_key(k1):
        ds[k1][k2] = v
    else:
        ds[k1] = {k2: v}
    return

def grp2(l):
    r = {}
    for (a, b) in l:
        setd(r, a, b)
    return opv(r, lambda x: x.keys())

def paths_to_d(pths):
    if pths == [()] or pths == [[]]:
        return None
    z = grp2([(p[0], p[1:]) for p in pths])
    return opv(z, paths_to_d)

def paths(d):
    if not d:
        return set([])
    if type(d) == type(""):
        print d
    l = set([(k,) for (k, v) in d.iteritems() if not v])
    return l.union([(k,) + p for (k, v) in d.iteritems() if v for p in paths(v)])


def loadunicode(fn, encoding = "utf-8"):
    f = open(DATA_DIR.joinpath(fn), "r")
    a = f.read()
    f.close()
    utxt = unicode(a, encoding)
    if utxt.startswith(u'\ufeff'):
        return utxt[1:]
    return utxt

reisobrack = re.compile("\[([a-z][a-z][a-z]|NOCODE\_[A-Z][^\s\]]+)\]")
def treetxt(txt):
    ls = [l.strip() for l in txt.split("\n") if l.strip()]
    r = {}
    thisclf = None
    for l in ls:
        o = reisobrack.search(l)
        if o:
            r[thisclf + (o.group(0)[1:-1],)] = None
        else:
            thisclf = tuple(l.split(", "))

    return paths_to_d(r.iterkeys())

def mergeds(ds):
    kvs = grp2([(k, v) for d in ds for (k, v) in d.iteritems()])
    kv = opv(kvs, lambda vs: max([(len(v), v) for v in vs])[1])
    return kv

from path import path

DATA_DIR = path('data')
def main(args):
    #http://clld.readthedocs.org/en/latest/extending.html
    data = Data(created=utc.localize(datetime(2013, 11, 15)), updated=utc.localize(datetime(2013, 12, 12)))
    #fromdb=MySQLdb.connect(user="root", passwd="blodig1kuk", db="linc")
    icons = issues.Icons()

    glottocodes = glottocodes_by_isocode(args.glottolog_dburi)

    #Languages
    dp = dtab("dp.tab")
    lons = dict([(d['iso-639-3'], d['lon']) for d in dp])
    lats = dict([(d['iso-639-3'], d['lat']) for d in dp])

    tabfns = [fn.basename() for fn in DATA_DIR.listdir('nts_*.tab')]
    print "Sheets found", tabfns
    ldps = [ld for fn in tabfns for ld in dtab(fn) if not ld["feature_alphanumid"].startswith("DRS") and ld["feature_alphanumid"].find(".") == -1]
    ldps = [dict([(k, v.replace(".", "-") if k in ['feature_alphanumid', 'value'] else v) for (k, v) in ld.iteritems()]) for ld in ldps]
    for ld in ldps:
        if not ld.has_key('language_id') or not ld.has_key('feature_alphanumid'):
            print "MISSING FEATURE OR LANGUAGE", ld
    lgs = dict([(ld['language_id'], ld['language_name']) for ld in ldps])
    nfeatures = opv(grp2([(ld['language_id'], ld['feature_alphanumid']) for ld in ldps if ld["value"] != "?"]), len)
    lgs["ygr"] = "Hua"
    lgs["qgr"] = "Yagaria"


    #Families
    fp = treetxt(loadunicode('lff.txt') + loadunicode('lof.txt'))
    ps = paths(fp)
    lg_to_fam = dict([(p[-1], p[0].replace("_", " ")) for p in ps])
    lg_to_fam['qgr'] = "Nuclear Trans New Guinea"

    lats['qgr'] = -6.21
    lons['qgr'] = 145.25

    mas = dtab("macroareas.tab")
    lg_to_ma = dict([(d['language_id'], d['macro_area']) for d in mas])
    lg_to_ma['qgr'] = "Papua"
 

    families = grp2([(lg_to_fam[lg], lg) for lg in lgs.keys()])
    ficons = dict(icons.iconizeall([f for (f, ntslgs) in families.iteritems() if len(ntslgs) != 1]).items() + [(f, icons.graytriangle) for (f, ntslgs) in families.iteritems() if len(ntslgs) == 1])
    for family in families.iterkeys():
        data.add(models.Family, family, id=slug(family), name=family, jsondata={"icon": ficons[family]})
    DBSession.flush()

    for lgid in lgs.iterkeys():
        lang = data.add(models.ntsLanguage, lgid, id=lgid, name=unescape(lgs[lgid]), family=data["Family"][lg_to_fam[lgid]], representation = nfeatures.get(lgid, 0), latitude = float(lats[lgid]), longitude = float(lons[lgid]), macroarea = lg_to_ma[lgid])
        if not lgid.startswith('NOCODE'):
            iso = data.add(
                common.Identifier, lgid,
                id=lgid, name=lgid, type=common.IdentifierType.iso.value, description=lgs[lgid])
            data.add(common.LanguageIdentifier, lgid, language=lang, identifier=iso)
        if lgid in glottocodes:
            gc = glottocodes[lgid]
            gc = data.add(
                common.Identifier, 'gc' + lgid,
                id=gc, name=gc, type=common.IdentifierType.glottolog.value, description=lgs[lgid])
            data.add(common.LanguageIdentifier, lgid, language=lang, identifier=gc)
    DBSession.flush()

    #Domains
    domains = dict([(ld['feature_domain'], ld) for ld in ldps])
    for domain in domains.iterkeys():
        #print domain
        data.add(models.FeatureDomain, domain, pk=domain, name=domain)
    DBSession.flush()

    #Designers
    #for dd in (dtab("ntscontributions.tab") + dtab("ntscontacts.tab")):
    #    print dd, dd["designer"]
    designer_info = dict([(dd['designer'], dd) for dd in (dtab("ntscontributions.tab") + dtab("ntscontacts.tab"))])
    #designers = dict([(ld['designer'], ld['feature_domain']) for ld in ldps])
    for (designer_id, designer) in enumerate(designer_info.iterkeys()):
        #print domain
        #print designer_info[designer]
        #print designer_id, designer_info[designer]
        data.add(models.Designer, designer, pk=designer_id, name=designer_id, domain=designer_info[designer]["domain"], contributor=designer, pdflink=designer_info[designer]["pdflink"], citation=designer_info[designer]["citation"])
    DBSession.flush()



    #Features
    #prefer = set(['feature_name']) #feature_information',  vdoc=f['feature_possible_values'], representation=nlgs.get(fid, 0), designer=data["Designer"][f['designer']], dependson = f["depends_on"], abbreviation=f["abbreviation"], featuredomain = data['FeatureDomain'][f["feature_domain"
    #fslds = grp2([(ld['feature_alphanumid'], (len(prefer.intersection(ld.keys())), i)) for (i, ld) in enumerate(ldps)])

    for (i, ld) in enumerate(ldps):
        if not ld['feature_alphanumid']:
            print "ILLEGAL FID", i, ld

    fslds = grp2([(ld['feature_alphanumid'], i) for (i, ld) in enumerate(ldps)])
    fs = opv(fslds, lambda lis: mergeds([ldps[i] for i in lis]))
    #print fs[u"162"]
    #print fslds[u"162"]
    #for (f, fld) in fs.iteritems():
    #    if not fld.has_key('feature_name'):
    #        print fld, fslds[fld['feature_alphanumid']]
    nameclash_fs = grp2([(f.get('feature_name', fid), fid) for (fid, f) in fs.iteritems()])
    fnamefix = {}
    for (dfeature, dfsids) in nameclash_fs.iteritems():
        if len(dfsids) != 1:
            print "Feature name clash", "|%s|" % dfeature, sorted(dfsids)
            for dfsid in dfsids:
                fnamefix[dfsid] = dfeature + " [%s]" % dfsid
        #if dfeature.find(".") != -1:
        #    print "Dot in name", dfeature
        #    for dfsid in dfsids:
        #        fnamefix[dfsid] = dfeature.replace("vs.", "versus").replace("Cf.", "Cf")

    nlgs = opv(grp2([(ld['feature_alphanumid'], ld['language_id']) for ld in ldps if ld["value"] != "?"]), len)
    for (fid, f) in fs.iteritems():
        #if int(fid) == 162:
        #    print fid, fnamefix.get(fid, f.get('feature_name', f['feature_alphanumid'])), f
        #    raise AttributeError
        param = data.add(models.Feature, fid, id=fid, name=fnamefix.get(fid, f.get('feature_name', f['feature_alphanumid'])), doc=f.get('feature_information', ""), vdoc=f.get('feature_possible_values', ""), representation=nlgs.get(fid, 0), designer=data["Designer"][f['designer']], dependson = f.get("depends_on", ""), abbreviation=f.get("abbreviation", ""), featuredomain = data['FeatureDomain'][f["feature_domain"]], name_french = f.get('francais', ""), clarification=f.get("draft of clarifying comments to outsiders (hedvig + dunn + harald + suzanne)", ""), alternative_id = f.get("old feature number", ""), jl_relevant_unit = f.get("relevant unit(s)", ""), jl_function = f.get("function", ""), jl_formal_means = f.get("formal means", ""), sortkey_str="", sortkey_int=int(fid))



    #Families
    DBSession.flush()

    fvs = opv(grp2([(ld['feature_alphanumid'], ld['feature_possible_values']) for ld in ldps]), lambda vs: max([(len(v), v) for v in vs])[1])
    for (fid, vs) in fvs.iteritems():
        vdesclist = [veq.split("==") for veq in vs.split("||")]
        try:
            vdesc = dict([(v.replace(".", "-"), desc) for [v, desc] in vdesclist])
        except ValueError:
            print "Faulty value desc", vdesclist, vs
        if not vdesc.has_key("?"):
            vdesc["?"] = "Not known"
        if not vdesc.has_key("N/A") and fs[fid].get("depends_on", ""):
            vdesc["N/A"] = "Not Applicable"
        vi = dict([(v, i) for (i, v) in enumerate(sorted(vdesc.keys()))])
        vicons = icons.iconize(vi.keys())
        #print data['Feature'][fid].pk, fid, vdesc.keys()
        for (v, desc) in vdesc.iteritems():
            data.add(
                common.DomainElement, (fid, v),
                id='%s-%s' % (fid, v),
                name=v,
                description=desc,
                jsondata={"icon": vicons[v]},
                number=vi[v],
                parameter=data['Feature'][fid])
    DBSession.flush()

    flg = grp2([((ld['feature_alphanumid'], ld['language_id']), i) for (i, ld) in enumerate(ldps)])
    for ((f, lg), ixs) in flg.iteritems():
        ixvs = set([ldps[ix]['value'] for ix in ixs])
        if len(ixvs) == 1:
            continue
        print "Dup value", f, lg, [(ldps[ix]['value'], ldps[ix]['fromfile']) for ix in ixs]
        #for ix in ixs:
        #    print ldps[ix] 
        #print "\n\n"


    errors = {}
    done = {}
    for ld in ldps:
        #if not data['Feature'].has_key(ld['feature_alphanumid']) or not data['Language'].has_key(ld['language_id']):
        #    continue
        parameter = data['Feature'][ld['feature_alphanumid']]
        language = data['ntsLanguage'][ld['language_id']]
        
        id_ = '%s-%s' % (parameter.id, language.id)

        if done.has_key(id_):
            continue

        if not data['DomainElement'].has_key((ld['feature_alphanumid'], ld['value'])):
            print ld['feature_alphanumid'], ld.get('feature_name', "[Feature Name Lacking]"), ld['language_id'], ld['value'], ld['fromfile'], "not in the set of legal values", "(%s)" % sorted([y for (x, y) in data['DomainElement'].iterkeys() if x == ld['feature_alphanumid']])
            errors[(ld['feature_alphanumid'], ld['language_id'])] = (ld['feature_alphanumid'], ld.get('feature_name', "[Feature Name Lacking]"), ld['language_id'], ld['value'], ld['fromfile'])
            continue

        valueset = data.add(
            common.ValueSet,
            id_,
            id=id_,
            language=language,
            parameter=parameter,
            source=ld["source"] or None,
            contribution=parameter.designer
        )
        data.add(
            models.ntsValue,
            id_,
            id=id_,
            domainelement=data['DomainElement'][(ld['feature_alphanumid'], ld['value'])],
            jsondata={"icon": data['DomainElement'][(ld['feature_alphanumid'], ld['value'])].jsondata},
            comment=ld["comment"],
            valueset=valueset,
            contributed_datapoint=ld["contributor"]
        )
        done[id_] = None
    DBSession.flush()

    #Domains/Chapters

    #Errors
    def s2(d, reverse=True):
        return [(a, d[a]) for (b, a) in sorted([(b, a) for (a, b) in d.iteritems()], reverse=reverse)]
    def ps2(d, reverse=True):
        return ''.join(["%s:  %s\n" % x for x in s2(d, reverse=reverse)])

    print len(errors), "Errors"
    #print ps2(opv(grp2([(err[0], err) for err in errors.values()]), len))
    #print ps2(opv(grp2([(err[2], err) for err in errors.values()]), len))
    #print ps2(opv(grp2([(err[4], err) for err in errors.values()]), len))

    #Sources
    sources = [ktfbib(bibsource) for ld in ldps if ld.get(u'bibsources') for bibsource in ld[u'bibsources'].split(",,,")]
    for (k, (typ, bibdata)) in sources:
        rec = Record(typ, k, **bibdata)
        if not data["Source"].has_key(k):
            data.add(common.Source, k, _obj=bibtex2source(rec))
    DBSession.flush()

    #ValueSetReference
    #migrate(
    #    'datapoint_reference'
    #    common.ValueSetReference,
    #    lambda r: dict(
    #        valueset=data['ValueSet'][r['datapoint_id']],
    #        source=data['Source'][r['reference_id']],
    #        description=r['note']))
    for ld in ldps:
        if not ld.has_key("bibsources"):
             print "no bibsource", ld
        sources = [ktfbib(bibsource) for bibsource in ld[u'bibsources'].split(",,,") if ld.get(u'bibsources')]
        parameter = data['Feature'][ld['feature_alphanumid']]
        language = data['ntsLanguage'][ld['language_id']]
        id_ = '%s-%s' % (parameter.id, language.id)
        if not data["ValueSet"].has_key(id_):
            #print "Skip source for", id_, "because no valueset"
            continue
        #print "Add src for", id_, k 
        for (k, (typ, bibdata)) in sources:    
            data.add(
                common.ValueSetReference,
                "%s-%s" % (id_, k),
                valueset=data["ValueSet"][id_],
                source=data['Source'][k])
    DBSession.flush()




    #Stats
    #Languages
    #Features
    #Datapoints
    dataset = common.Dataset(
        id="NTS",
        name='Nijmegen Typological Survey',
        publisher_name="Max Planck Institute for Psycholinguistics",
        publisher_place="Nijmegen",
        publisher_url="http://www.mpi.nl",
        description="""Dataset on Typological Features, collected 2013-2014 in the Language and Cognition Department at the Max Planck Institute for Psycholinguistics, Max-Planck Gesellschaft, and a European Research Council's Advanced Grant (269484 "INTERACT") to Stephen C. Levinson.""",
        domain='http://nts.clld.org',
        published=date(2014, 2, 20),
        contact='harald.hammarstroem@mpi.nl',
        license='http://creativecommons.org/licenses/by-nc-nd/2.0/de/deed.en',
        jsondata={
            'license_icon': 'http://wals.info/static/images/cc_by_nc_nd.png',
            'license_name': 'Creative Commons Attribution-NonCommercial-NoDerivs 2.0 Germany'})
    DBSession.add(dataset)
    DBSession.flush()

    editor = data.add(common.Contributor, "Harald Hammarstrom", id="Harald Hammarstrom", name="Harald Hammarstrom", email = "harald.hammarstroem@mpi.nl")
    common.Editor(dataset=dataset, contributor=editor, ord=0)
    editor = data.add(common.Contributor, "Suzanne van der Meer", id="Suzanne van der Meer", name="Suzanne van der Meer", email = "suzanne.vandermeer@mpi.nl")
    common.Editor(dataset=dataset, contributor=editor, ord=1)
    editor = data.add(common.Contributor, "Hedvig Skirgard", id="Hedvig Skirgard", name="Hedvig Skirgard", email = "hedvig.skirgard@mpi.nl")
    common.Editor(dataset=dataset, contributor=editor, ord=2)

    DBSession.flush()

















def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """

    compute_language_sources()
    transaction.commit()
    transaction.begin()

    gbs_func('update', args)

if __name__ == '__main__':
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)





