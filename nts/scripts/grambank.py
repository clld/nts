from __future__ import unicode_literals
import re
from collections import OrderedDict
import io

from sqlalchemy import create_engine
from sqlalchemy.orm import joinedload, joinedload_all
import json

from clld.scripts.util import parsed_args
from clld.lib.dsv import reader, UnicodeWriter
from clld.db.meta import DBSession
from clld.db.models.common import Language, ValueSet, ValueSetReference, Value


class GBFeature(object):
    @staticmethod
    def yield_domainelements(s):
        try:
            for m in re.split('\s*,|;\s*', re.sub('^multistate\s+', '', s.strip())):
                if m.strip():
                    if m.startswith('As many'):
                        for i in range(100):
                            yield '%s' % i, '%s' % i
                    else:
                        number, desc = m.split(':')
                        yield number.strip(), desc.strip()
        except:
            print s
            raise

    def __init__(self, d):
        self.id = d['GramBank ID'].strip()
        self.name = d['Feature']
        self.domain = OrderedDict()
        for n, desc in self.yield_domainelements(d['Possible Values']):
            self.domain[n] = desc
        self.domain.update({'?': 'Not known'})

    def format_domain(self):
        return '; '.join('%s: %s' % item for item in self.domain.items() if item[0] != '?')


def row(gc, f, vs=None, value=None):
    return [
        gc,
        f.id,
        f.name,
        f.format_domain(),
        value or '',
        (vs.source or '') if vs else '',
        (vs.values[0].comment or '') if vs else '',
    ]


def export(args, lang, features, gc, ma):
    values = {k: row(gc, f) for k, f in features.items()}
    errors = []
    sources = {}
    n = 0
    for vs in DBSession.query(ValueSet).filter(ValueSet.language == lang).options(
        joinedload(ValueSet.parameter),
        joinedload_all(ValueSet.values, Value.domainelement),
        joinedload(ValueSet.references, ValueSetReference.source),
    ):
        if vs.parameter.id in features:
            n += 1
            f = features[vs.parameter.id]
            value = vs.values[0].domainelement.name
            if value == 'N/A':
                value = '?'
            assert value in f.domain
            values[vs.parameter.id] = row(gc, f, vs, value)
            for ref in vs.references:
                sources[ref.source.name] = ref.source

    print lang.id, ':', n, 'of', len(values)

    subdir = args.data_file('grambank', ma)
    if not subdir.exists():
        subdir.mkdir()
    path = lambda suffix: subdir.joinpath(gc + suffix)

    with UnicodeWriter(path('.tsv'), delimiter=b'\t') as writer:
        writer.writerow(['Language_ID', 'Feature_ID', 'Feature', 'Domain', 'Value', 'Source', 'Comment'])
        writer.writerows(sorted(values.values(), key=lambda r: r[1]))

    with open(path('.tsv-metadata.json'), 'wb') as fp:
        json.dump({
            'type': 'FeatureCollection',
            'features': [
                {
                    "type": "Feature",
                    "id": 'http://glottolog.org/resource/languoid/id/%s' % gc,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lang.longitude, lang.latitude]
                    },
                    "properties": {
                        'name': lang.name,
                        'glottocode': gc,
                        'iso-639-3': lang.iso_code,
                    },
                },
            ],
            'comment': 'Converted from NTS data',
            #'sources': {
            #    name: sources[name].bibtex().id for name in sorted(sources.keys())
            #}
        },
            fp,
            indent=4,
            #allow_unicode=True,
            #default_flow_style=False
        )

    with io.open(path('.bib'), 'w', encoding='utf8') as fp:
        for src in set(sources.values()):
            rec = src.bibtex()
            rec['key'] = src.name
            fp.write('%s\n\n' % rec)

    return errors


def main(args):
    features = reader(args.data_file('grambank_features.csv'), dicts=True, )
    features = [GBFeature(f) for f in features]
    features = {'%s' % int(f.id[2:]): f for f in features}
    errors = []

    db = create_engine('postgresql://robert@/glottolog3')

    for l in DBSession.query(Language):
        if l.id == 'qgr':
            continue

        gc = l.glottocode
        ma = db.execute("""
select
    m.id
from
    macroarea as m, languoidmacroarea as lm, language as l
where
    m.pk = lm.macroarea_pk and lm.languoid_pk = l.pk and l.id = '%s';""" % gc).fetchone()[0]

        if ma == 'pacific':
            ma = 'papunesia'

        errors.extend(export(args, l, features, gc, ma))

    with UnicodeWriter(args.data_file('na_errors.tsv'), delimiter=b'\t') as writer:
        writer.writerow(['Language', 'Feature', 'Value', 'Source', 'Comment'])
        writer.writerows(errors)


if __name__ == '__main__':
    main(parsed_args())
