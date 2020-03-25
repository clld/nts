from pathlib import Path
from clld.web.assets import environment

import nts


environment.append_path(
    str(Path(nts.__file__).parent.joinpath('static')), url='/nts:static/')
environment.load_path = list(reversed(environment.load_path))
