from clld.web.assets import environment
from path import path

import nts


environment.append_path(
    path(nts.__file__).dirname().joinpath('static'), url='/nts:static/')
environment.load_path = list(reversed(environment.load_path))
