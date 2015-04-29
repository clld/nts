from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from clld.db.models.common import ValueSet


@view_config(route_name='valueset', request_method='POST')
def comment(request):  # pragma: no cover
    """check whether a blog post for the datapoint does exist.

    if not, create one and redirect there.
    """
    vs = ValueSet.get(request.matchdict['id'])
    return HTTPFound(request.blog.post_url(vs, request, create=True) + '#comment')
