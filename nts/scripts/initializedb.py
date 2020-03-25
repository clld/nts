import sys
from itertools import groupby
from collections import Counter
import csv
from functools import partial
import io
from datetime import date, datetime

import transaction
from pytz import utc

from clld.scripts.util import initializedb, Data, gbs_func, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.db.util import compute_language_sources
from clld.lib.bibtex import unescape, Record
from csvw.dsv import reader
from clld_glottologfamily_plugin.util import load_families, Family
from clld.lib import bibtex

from nts import models

from . import issues


NOCODE_TO_GLOTTOCODE = {
    'NOCODE_Apolista': 'apol1242',
    'NOCODE_Maipure': 'maip1246',
    'NOCODE_Ngala-Santandrea': 'ngal1296',
    'NOCODE_Nzadi': 'nzad1234',
    'NOCODE_Paunaca': 'paun1241',
    'NOCODE_Sisiqa': 'sisi1250',
    'pnk': 'paun1241'
}


def savu(txt, fn, encoding = "utf-8-sig"):
    with io.open(fn, 'w', encoding=encoding) as fp:
        fp.write(txt)


def ktfbib(s):
    rs = [z.split(":::") for z in s.split("|||")]
    [k, typ] = rs[0]
    return k, (typ, dict(rs[1:]))


def _dtab(dir_, fn):
    lpd = []
    for d in reader(dir_.joinpath(fn), dicts=True, delimiter='\t', quoting=csv.QUOTE_NONE):
        lpd.append({
            k.replace('\ufeff', ''): (v or '').strip()
            for k, v in d.items() + [("fromfile", fn)]})
    return lpd


def grp2(l):
    return [
        (k, [_i[1] for _i in i]) for k, i in
        groupby(sorted((a, b) for a, b in l), key=lambda t: t[0])]


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


def bibliographical_details(bibsources):
    ktfs = [ktfbib(bibsource) for bibsource in bibsources if bibsource.strip()]
    return u"; ".join([Record(t, k, **{k: bibtex.unescape(v) for (k, v) in f.iteritems()}).text() for (k, (t, f)) in ktfs])

def main(args):
    """
    The case is we have to codings for two different dialects (called hua and yagaria) of
    the same iso "qgr", both of which we want to keep and keep separately. I had missed
    that when making NTS, rigging everything so that the iso would be the id, which is not
    sufficient. Glottocodes in Grambank would have taken care of it except the dialect
    division for yaga1260 is wrong, having yagaria as overarching and Hua under it
    (reality has it that Hua and Yagaria are two dialects of the same language, which has
    no name). So a solution with glottocodes would have to wait until we fix that or need
    another fix later. So I guess, for now, let's ignore qgr (and its datapoints) and I'll
    fix on my end later.
    """
    data = Data(
        created=utc.localize(datetime(2013, 11, 15)),
        updated=utc.localize(datetime(2013, 12, 12)))
    icons = issues.Icons()

    dtab = partial(_dtab, args.data_file())

    #Languages
    tabfns = ['%s' % fn.name for fn in args.data_file().glob('nts_*.tab')]
    args.log.info("Sheets found: %s" % tabfns)
    ldps = []
    lgs = {}
    nfeatures = Counter()
    nlgs = Counter()

    for fn in tabfns:
        for ld in dtab(fn):
            if ld['language_id'] == 'qgr':
                continue
            if "feature_alphanumid" not in ld:
                args.log.info("NO FEATUREID %s %s" % (len(ld), ld))
            if not ld["feature_alphanumid"].startswith("DRS") \
                    and ld["feature_alphanumid"].find(".") == -1:
                ldps.append(dp_dict(ld))
                lgs[ld['language_id']] = unescape(ld['language_name'])
                if ld["value"] != "?":
                    nfeatures.update([ld['language_id']])
                    nlgs.update([ld['feature_alphanumid']])

    ldps = sorted(ldps, key=lambda d: d['feature_alphanumid'])

    lgs["ygr"] = "Hua"

    for lgid, lgname in lgs.items():
        data.add(
            models.ntsLanguage, lgid,
            id=lgid,
            name=lgname,
            representation=nfeatures.get(lgid, 0))
    DBSession.flush()

    load_families(data, [(NOCODE_TO_GLOTTOCODE.get(l.id, l.id), l) for l in data['ntsLanguage'].values()], isolates_icon='tcccccc')
    #glottolog = Glottolog()
    #for lg in data['ntsLanguage'].values():
    #    print lg.id, NOCODE_TO_GLOTTOCODE.get(lg.id, lg.id)
    #    gl_language = glottolog.languoid(NOCODE_TO_GLOTTOCODE.get(lg.id, lg.id))
    #    if not gl_language.family:
    #        family = data.add(Family, gl_language.id, id = gl_language.id, name = gl_language.name, description=common.Identifier(name=gl_language.id, type=common.IdentifierType.glottolog.value).url(), jsondata={"icon": 'tcccccc'})
    #        lg.family = family

    
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
        print(fid, "DIFF VDESC")
        for (vd, fromf) in vdescs:
            print(vd, set(fromf))

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
        dt = (lgs[ld['language_id']], ld['language_id'], ld['feature_alphanumid'] + ". " + ld['feature_name'], ld["value"]) #, ld["comment"], ld["source"], bibliographical_details(ld.get('bibsources', "").split(",,,"))
        cldf[dt] = None
        
        
    tab = lambda rows: u''.join([u'\t'.join(row) + u"\n" for row in rows])
    savu(tab([("Language", "iso-639-3", "Feature", "Value")] + cldf.keys()), "nts.cldf", encoding = "utf-8") #utf-16 "Comment", "Source", "Bibliographical Details"



    #cldf = {}
    #for ld in ldps:
    #    parameter = data['Feature'][ld['feature_alphanumid']]
    #    language = data['ntsLanguage'][ld['language_id']]
    #    id_ = '%s-%s' % (parameter.id, language.id)
    #    if not id_ in done:
    #        continue
    #    dt = (lgs[ld['language_id']], ld['language_id'], ld['feature_alphanumid'] + ". " + ld['feature_name'], ld["value"], ld["comment"], ld["source"], bibliographical_details(ld.get('bibsources', "").split(",,,")), ld.get("feature_information", ""), ld.get('feature_possible_values', ""), ld["designer"], ld.get("abbreviation", ""), ld["feature_domain"], ld.get('francais', ""), ld.get("dependencies", ""), ld.get("draft of clarifying comments to outsiders (hedvig + dunn + harald + suzanne)", ""))
    #    cldf[dt] = None
    
    #savu(tab([("Language", "iso-639-3", "Feature", "Value", "Comment", "Source", "Bibliographical Details", "Feature Information", "Feature Possible Values", "Feature Designer", "Feature Abbreviation", "Feature Domain", "Feature (French)", "Feature Dependencies", "Feature Clarifying Comments")] + cldf.keys()), "nts-with-metadata.tsv", encoding="utf-16")

    
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
