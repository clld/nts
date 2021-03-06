import re
import pathlib
from itertools import cycle

import nts


class Icons(object):
    filename_pattern = re.compile('(?P<spec>(c|d|s|f|t)[0-9a-f]{3})\.png')
    graytriangle = "tcccccc"

    @staticmethod
    def id(spec):
        """translate old wals icon id into clld icon id c0a9 -> c00aa99
        """
        return ''.join(c if i == 0 else c + c for i, c in enumerate(spec))

    def __init__(self):
        self._icons = []
        for name in sorted(
            pathlib.Path(nts.__file__).parent.joinpath('static', 'icons').files()
        ):
            m = self.filename_pattern.match(name.splitall()[-1])
            if m:
                self._icons.append(Icons.id(m.group('spec')))

    def __iter__(self):
        return iter(self._icons)

    def iconize(self, xs, t="c"):
        icons_t = sorted([icon for icon in self._icons if icon.startswith(t)])
        icons_selection = [icons_t[i] for i in range(0, len(icons_t), len(icons_t)/len(xs))] if len(xs) < len(icons_t) else cycle(icons_t)
        return dict(zip(xs, icons_selection))
