import pytest


@pytest.mark.parametrize(
    "method,path",
    [
        ('get_html', '/'),
        ('get_html', '/parameters/1'),
        ('get_html', '/parameters/1?z=5&lat=0.5&lng=0.5'),
        ('get_html', '/parameters/1?z=ff&lat=pp&lng=yy'),
        ('get', '/parameters/1.tab'),
        ('get_json', '/parameters/1.geojson?domainelement=1-1'),
        ('get_html', '/combinations/1_2'),
        ('get_html', '/languages'),
        ('get_dt', '/values?parameter=1'),
        ('get_html', '/languages.map.html?sEcho=1&sSearch_2=austro'),
        ('get_dt', '/parameters?sSearch_0=1&iSortingCols=1&iSortCol_0=0'),
        ('get_dt', '/parameters?sSearch_2=Aus&iSortingCols=1&iSortCol_0=2'),
        ('get_html', '/contributions'),
        ('get_dt', '/values?language=aau'),
    ])
def test_pages(app, method, path):
    getattr(app, method)(path)
