from clld.web.assets import environment
from clldutils.path import Path

import nts


environment.append_path(
    str(Path(nts.__file__).parent.joinpath('static')), url='/nts:static/')
environment.load_path = list(reversed(environment.load_path))
