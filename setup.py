from setuptools import setup, find_packages

requires = [
    'clld>=0.17',
    'clldmpg',
    'pyramid',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'zope.sqlalchemy',
    'gunicorn',
    'psycopg2',
    'waitress',
    ]

setup(name='nts',
      version='0.0',
      description='nts',
      long_description='',
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="nts",
      entry_points="""\
      [paste.app_factory]
      main = nts:main
      """,
      )
