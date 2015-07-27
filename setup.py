from setuptools import setup, find_packages

requires = [
    'clld>=1.1.0',
    'clldmpg>=1.0.0',
    'clld-glottologfamily-plugin>=0.4',
]

tests_require = [
    'WebTest',
    'mock==1.0',
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
      tests_require=tests_require,
      test_suite="nts",
      entry_points="""\
      [paste.app_factory]
      main = nts:main
      """,
      )
