# coding: utf8
from __future__ import unicode_literals
import sys
import transaction
from itertools import groupby
from collections import Counter
from io import open
import re
import socket
import getpass
import csv
from functools import partial

from pytz import utc
from datetime import date, datetime

from clld.scripts.util import (
    initializedb, Data, gbs_func, bibtex2source, glottocodes_by_isocode,
    add_language_codes,
)
from clld.db.meta import DBSession
from clld.db.models import common
from clld.db.util import compute_language_sources
from clld.lib.bibtex import unescape, Record
from clld.lib.dsv import reader
from clld.util import slug

from nts import models

import issues


import codecs
def savu(txt, fn):
    f = codecs.open(fn, 'w', encoding = "utf-8")
    f.write(txt)
    f.close()
    return

def ktfbib(s):
    rs = [z.split(":::") for z in s.split("|||")]
    [k, typ] = rs[0]
    return k, (typ, dict(rs[1:]))


def _dtab(dir_, fn):
    lpd = []
    for d in reader(dir_.joinpath(fn), dicts=True, quoting=csv.QUOTE_NONE):
        lpd.append({
            k.replace('\ufeff', ''): (v or '').strip()
            for k, v in d.items() + [("fromfile", fn)]})
    return lpd


def grp2(l):
    return [
        (k, [_i[1] for _i in i]) for k, i in
        groupby(sorted((a, b) for a, b in l), key=lambda t: t[0])]


def paths_to_d(pths):
    if pths == [()] or pths == [[]]:
        return None
    return {i: paths_to_d(v) for i, v in grp2([(p[0], p[1:]) for p in pths])}


def paths(d):
    if not d:
        return set([])
    assert not isinstance(d, basestring)
    l = set([(k,) for (k, v) in d.items() if not v])
    return l.union([(k,) + p for (k, v) in d.items() if v for p in paths(v)])


def _lines(dir_, fn):
    with open(dir_.joinpath(fn), encoding='utf8') as fp:
        return fp.readlines()


def treetxt(txt):
    reisobrack = re.compile("\[([a-z][a-z][a-z]|NOCODE\_[A-Z][^\s\]]+)\]")
    r = set()
    thisclf = None
    for l in [l.strip() for l in txt if l.strip()]:
        o = reisobrack.search(l)
        if o:
            r.add(thisclf + (o.group(0)[1:-1],))
        else:
            thisclf = tuple(l.split(", "))

    return paths_to_d(r)


def mergeds(ds):
    """Merge a list of dictionaries by aggregating keys and taking the longest value for
    each key.

    :param ds: an iterable of dictionaries
    :return: the merged dictionary.
    """
    return {k: vs.next()[1] for k, vs in groupby(sorted(
        [(k, v) for d in ds for (k, v) in d.items()],
        key=lambda t: (t[0], len(t[1])),
        reverse=True),
        key=lambda t: t[0])}

def longest(ss):
    return max([(len(s), s) for s in ss])[1]

def dp_dict(ld):
    assert 'language_id' in ld and ld.get('feature_alphanumid')
    return {
        k: v.replace(".", "-") if k in ['feature_alphanumid', 'value'] else v
        for (k, v) in ld.iteritems()}


def main(args):
    data = Data(
        created=utc.localize(datetime(2013, 11, 15)),
        updated=utc.localize(datetime(2013, 12, 12)))
    icons = issues.Icons()

    dtab = partial(_dtab, args.data_file())
    lines = partial(_lines, args.data_file())

    dburi = args.glottolog_dburi
    if not dburi and socket.gethostname() == 'astroman' and getpass.getuser() == 'robert':
        dburi = 'postgresql://robert@/glottolog3'
    glottocodes = glottocodes_by_isocode(dburi)

    #Languages
    coords = {d['iso-639-3']: d for d in dtab("dp.tab")}
    coords['qgr'] = dict(lat=-6.21, lon=145.25)

    tabfns = ['%s' % fn.basename() for fn in args.data_file().files('nts_*.tab')]
    args.log.info("Sheets found: %s" % tabfns)
    ldps = []
    lgs = {}
    nfeatures = Counter()
    nlgs = Counter()

    for fn in tabfns:
        for ld in dtab(fn):
            if not ld.has_key(u"feature_alphanumid"):
                args.log.info("NO FEATUREID %s %s" % (len(ld), ld))
            if not ld["feature_alphanumid"].startswith("DRS") \
                    and ld["feature_alphanumid"].find(".") == -1:
                ldps.append(dp_dict(ld))
                lgs[ld['language_id']] = ld['language_name']
                if ld["value"] != "?":
                    nfeatures.update([ld['language_id']])
                    nlgs.update([ld['feature_alphanumid']])

    ldps = sorted(ldps, key=lambda d: d['feature_alphanumid'])

    lgs["ygr"] = "Hua"
    lgs["qgr"] = "Yagaria"
    #lgs["dba"] = "Bangime"
    lgs = dict([(lg, unescape(lgname)) for (lg, lgname) in lgs.iteritems()])

    #Families
    txt = lines('lff.txt') + lines('lof.txt')
    lg_to_fam = {p[-1]: p[0].replace("_", " ") for p in paths(treetxt(txt))}
    lg_to_fam['qgr'] = "Nuclear Trans New Guinea"

    lg_to_ma = {d['language_id']: d['macro_area'] for d in dtab("macroareas.tab")}
    lg_to_ma['qgr'] = "Papua"

    for fam, icon in icons.iconizeall(grp2([(lg_to_fam[lg], lg) for lg in lgs.keys()])):
        data.add(models.Family, fam, id=slug(fam), name=fam, jsondata={"icon": icon})
    DBSession.flush()

    for lgid in lgs:
        lang = data.add(
            models.ntsLanguage, lgid,
            id=lgid,
            name=unescape(lgs[lgid]),
            family=data["Family"][lg_to_fam[lgid]],
            representation=nfeatures.get(lgid, 0),
            latitude=float(coords[lgid]['lat']),
            longitude=float(coords[lgid]['lon']),
            macroarea=lg_to_ma[lgid])
        add_language_codes(data, lang, isocode=lgid, glottocodes=glottocodes)
    DBSession.flush()

    #Domains
    for domain in set(ld['feature_domain'] for ld in ldps):
        data.add(models.FeatureDomain, domain, name=domain)
    DBSession.flush()

    #Designers
    for i, info in enumerate(dtab("ntscontributions.tab") + dtab("ntscontacts.tab")):
        designer_id = str(i + 1)
        data.add(
            models.Designer, info['designer'],
            id=designer_id,
            name=designer_id,
            domain=info["domain"],
            contributor=info['designer'],
            pdflink=info["pdflink"],
            citation=info["citation"])
    DBSession.flush()

    #Sources
    for k, (typ, bibdata) in [
        ktfbib(bibsource) for ld in ldps
        if ld.get(u'bibsources') for bibsource in ld['bibsources'].split(",,,")
    ]:
        if k not in data["Source"]:
            data.add(common.Source, k, _obj=bibtex2source(Record(typ, k, **bibdata)))
    DBSession.flush()

    #Features
    fs = [(fid, mergeds(lds)) for fid, lds in
          groupby(ldps, key=lambda d: d['feature_alphanumid'])]

    fvdesc = [(fid, [(ld.get("feature_possible_values"), ld.get("fromfile")) for ld in lds if ld.get("feature_possible_values")]) for fid, lds in groupby(ldps, key=lambda d: d['feature_alphanumid'])]
    fvdt = [(fid, grp2(vdescs)) for (fid, vdescs) in fvdesc]
    fvmis = [(fid, vdescs) for (fid, vdescs) in fvdt if len(vdescs) > 1]
    for (fid, vdescs) in fvmis:
        print fid, "DIFF VDESC"
        for (vd, fromf) in vdescs:
            print vd, set(fromf)

    for _, dfsids in groupby(
            sorted((f.get('feature_name', fid), fid) for fid, f in fs),
            key=lambda t: t[0]):
        assert len(list(dfsids)) == 1

    for fid, f in fs:
        if not fid.isdigit():
            args.log.info("NO INT FID %s" % f)           
        feature = data.add(
            models.Feature, fid,
            id=fid,
            name=f.get('feature_name', f['feature_alphanumid']),
            doc=f.get('feature_information', ""),
            vdoc=f.get('feature_possible_values', ""),
            representation=nlgs.get(fid, 0),
            designer=data["Designer"][f['designer']],
            dependson=f.get("depends_on", ""),
            abbreviation=f.get("abbreviation", ""),
            featuredomain=data['FeatureDomain'][f["feature_domain"]],
            name_french=f.get('francais', ""),
            clarification=f.get("draft of clarifying comments to outsiders (hedvig + dunn + harald + suzanne)", ""),
            alternative_id=f.get("old feature number", ""),
            jl_relevant_unit=f.get("relevant unit(s)", ""),
            jl_function=f.get("function", ""),
            jl_formal_means=f.get("formal means", ""),
            sortkey_str="",
            sortkey_int=int(fid))

        vdesclist = [veq.split("==") for veq in feature.vdoc.split("||")]
        vdesc = {v.replace(".", "-"): desc for [v, desc] in vdesclist}
        vdesc.setdefault('?', 'Not known')
        if 'N/A' not in vdesc and feature.dependson:
            vdesc["N/A"] = "Not Applicable"
        vi = {v: i for (i, v) in enumerate(sorted(vdesc.keys()))}
        vicons = icons.iconize(vi.keys())
        for v, desc in vdesc.items():
            data.add(
                common.DomainElement, (fid, v),
                id='%s-%s' % (fid, v),
                name=v,
                description=desc,
                jsondata={"icon": vicons[v]},
                number=vi[v],
                parameter=feature)
    DBSession.flush()

    for ((f, lg), ixs) in grp2(
            [((ld['feature_alphanumid'], ld['language_id']), i)
             for i, ld in enumerate(ldps)]):
        ixvs = set([ldps[ix]['value'] for ix in ixs])
        if len(ixvs) == 1:
            continue
        args.log.warn(
            "Dup value %s %s %s" %
            (f, lg, [(ldps[ix]['value'], ldps[ix]['fromfile']) for ix in ixs]))
        print "Dup value %s %s %s" % (f, lg, [(ldps[ix]['value'], ldps[ix]['fromfile'], ldps[ix].get('provenance')) for ix in ixs])
    errors = {}
    done = set()
    for ld in ldps:
        parameter = data['Feature'][ld['feature_alphanumid']]
        language = data['ntsLanguage'][ld['language_id']]
        
        id_ = '%s-%s' % (parameter.id, language.id)
        if id_ in done:
            continue

        if (ld['feature_alphanumid'], ld['value']) not in data['DomainElement']:
            if not ld["value"].strip():
                continue
            info = (
                ld['feature_alphanumid'],
                ld.get('feature_name', "[Feature Name Lacking]"),
                ld['language_id'],
                ld['value'],
                ld['fromfile'])
            msg = u"%s %s %s %s %s not in the set of legal values ({0})" % info
            args.log.error(msg.format(sorted(
                [y for (x, y) in data['DomainElement'].keys()
                 if x == ld['feature_alphanumid']])))
            print msg.format(sorted(
                [y for (x, y) in data['DomainElement'].keys()
                 if x == ld['feature_alphanumid']]))
            errors[(ld['feature_alphanumid'], ld['language_id'])] = info
            continue

        vs = common.ValueSet(
            id=id_,
            language=language,
            parameter=parameter,
            source=ld["source"] or None,
            contribution=parameter.designer)
        models.ntsValue(
            id=id_,
            domainelement=data['DomainElement'][(ld['feature_alphanumid'], ld['value'])],
            jsondata={"icon": data['DomainElement'][(ld['feature_alphanumid'], ld['value'])].jsondata},
            comment=ld["comment"],
            valueset=vs,
            contributed_datapoint=ld["contributor"])
        done.add(id_)

        if not ld.get('bibsources'):
            if 'bibsources' not in ld:
                args.log.warn("no bibsource %s" % ld)
            continue
        for k, _ in [ktfbib(bibsource) for bibsource in ld['bibsources'].split(",,,")]:
            common.ValueSetReference(valueset=vs, source=data['Source'][k])
    DBSession.flush()

    #To CLDF
    cldf = {}
    for ld in ldps:
        parameter = data['Feature'][ld['feature_alphanumid']]
        language = data['ntsLanguage'][ld['language_id']]
        id_ = '%s-%s' % (parameter.id, language.id)
        if not id_ in done:
            continue
        dt = (lgs[ld['language_id']], "ygr" if ld['language_id'] == 'qgr' else ld['language_id'], ld['feature_alphanumid'] + ". " + ld['feature_name'], ld["value"])
        cldf[dt] = None

    tab = lambda rows: u''.join([u'\t'.join(row) + u"\n" for row in rows])
    savu(tab([("Language", "iso-639-3", "Feature", "Value")] + cldf.keys()), "nts.cldf")
        
    args.log.info('%s Errors' % len(errors))

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

    for i, contributor in enumerate([
        common.Contributor(
            id="Harald Hammarstrom",
            name="Harald Hammarstrom",
            email="harald.hammarstroem@mpi.nl"),
        common.Contributor(
            id="Suzanne van der Meer",
            name="Suzanne van der Meer",
            email="suzanne.vandermeer@mpi.nl"),
        common.Contributor(
            id="Hedvig Skirgard",
            name="Hedvig Skirgard",
            email="hedvig.skirgard@mpi.nl")
    ]):
        common.Editor(dataset=dataset, contributor=contributor, ord=i)

    DBSession.add(dataset)


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
