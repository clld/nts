from clld.tests.util import TestWithSelenium

import nts


class Tests(TestWithSelenium):
    app = nts.main({}, **{'sqlalchemy.url': 'postgres://robert@/nts'})
