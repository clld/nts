from zope.interface import implementer
from six import string_types

from clld.interfaces import IBlog
from clld.lib import wordpress


@implementer(IBlog)
class Blog(object):
    def __init__(self, settings, prefix='blog.'):
        self.host = settings[prefix + 'host']
        self.wp = wordpress.Client(
            self.host, settings[prefix + 'user'], settings[prefix + 'password'])

    def url(self, path=None):
        path = path or '/'
        if not path.startswith('/'):
            path = '/' + path
        return 'http://%s%s' % (self.host, path)

    def _set_category(self, **cat):
        return list(self.wp.set_categories([cat]).values())[0]

    @staticmethod
    def slug(vs):
        return 'datapoint-{0.parameter.id}-{0.language.id}/'.format(vs)

    def post_url(self, obj, req, create=False):
        res = self.url(self.slug(obj))
        if create and not self.wp.get_post_id_from_path(res):
            # create categories if missing:
            languageCat, featureCat = None, None

            for cat in self.wp.get_categories():
                if cat['name'] == 'Languages':
                    languageCat = cat['id']
                if cat['name'] == 'Features':
                    featureCat = cat['id']

            if languageCat is None:
                languageCat = self._set_category(name='Languages', slug='languages')
            if featureCat is None:
                featureCat = self._set_category(name='Features', slug='features')

            # now create the post:
            categories = [
                dict(name=obj.parameter.name, parent_id=featureCat),
                dict(name=obj.language.name, parent_id=languageCat)]
            self.wp.create_post(
                'Datapoint %s' % obj.name,
                'Discuss NTS Datapoint <a href="%s">%s</a>.' % (
                    req.resource_url(obj), obj.name),
                categories=categories,
                published=True,
                wp_slug=self.slug(obj))
        return res

    def feed_url(self, obj, req):
        return self.url(
            '%s/feed' % (obj if isinstance(obj, string_types) else self.slug(obj),))
