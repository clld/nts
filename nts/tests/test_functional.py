from path import path

from clld.tests.util import TestWithApp

import nts


class Tests(TestWithApp):
    __cfg__ = path(nts.__file__).dirname().joinpath('..', 'development.ini').abspath()
    __setup_db__ = False

    def test_home(self):
        self.app.get('/', status=200)

    def test_misc(self):
        self.app.get_html('/parameters/1')
        self.app.get_html('/parameters/1?z=5&lat=0.5&lng=0.5')
        self.app.get_html('/parameters/1?z=ff&lat=pp&lng=yy')
        self.app.get_json('/parameters/1.solr.json')
        self.app.get_json('/parameters/1.geojson?domainelement=1-1')
        self.app.get_html('/combinations/1_2')
        self.app.get_html('/languages')
        self.app.get_dt('/values?parameter=1')
        self.app.get_html('/languages.map.html?sEcho=1&sSearch_2=austro')
        self.app.get_dt('/parameters?sSearch_0=1&iSortingCols=1&iSortCol_0=0')
        self.app.get_dt('/parameters?sSearch_2=Aus&iSortingCols=1&iSortCol_0=2')
        self.app.get_html('/contributions')
        self.app.get_dt('/values?language=aau')