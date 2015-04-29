from unittest import TestCase
from collections import defaultdict

from mock import patch, Mock

from clld.db.models.common import ValueSet, Parameter, Language

from nts.blog import Blog


class Client(Mock):
    get_post_id_from_path = Mock(return_value=None)
    get_categories = Mock(
        return_value=[dict(name='Languages', id=1), dict(name='Features', id=2)])


class wordpress(Mock):
    Client = Client()


class Request(Mock):
    def resource_url(self, obj):
        return ''


class Tests(TestCase):
    def setUp(self):
        with patch('nts.blog.wordpress', new=wordpress()):
            self.blog = Blog(defaultdict(lambda: ''))
        self.vs = ValueSet(
            parameter=Parameter(id='p', name='P'),
            language=Language(id='l', name='L'))

    def test_url(self):
        self.assertEquals(self.blog.url(), '/')

    def test_slug(self):
        self.assertEquals(self.blog.slug(self.vs), 'datapoint-p-l/')

    def test_post_url(self):
        self.assertEquals(
            self.blog.post_url(self.vs, Request(), create=True), '/datapoint-p-l/')

    def test_feed_url(self):
        self.assertEquals(self.blog.feed_url(self.vs, None), '/datapoint-p-l/feed')
