from setuptools import setup, find_packages

version = '0.1'

setup(name='check_multi_url',
      version=version,
      description='Asynchronous Nagios Multi Url check',
      classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='icinga nagios monitoring commandline url http',
      author='James Powell',
      author_email='pydev@webscalability.com',
      url='http://www.webscalability.com',
      license='GPL3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      scripts=['scripts/check_multi_url'],
      setup_requires=["pytest-runner"],
      tests_require=["pytest"],
      include_package_data=True,
      zip_safe=True,
      install_requires=[
        'aiohttp' 
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
