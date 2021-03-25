from os.path import abspath, dirname, join
from setuptools import find_packages, setup


ENTRY_POINTS = '''
[crosscompute]
printers.run = crosscompute_prints.scripts.printers.run:RunPrinterScript
'''
APPLICATION_CLASSIFIERS = [
    'Programming Language :: Python :: 3',
]
APPLICATION_REQUIREMENTS = [
    'crosscompute',
    'pypdf2',
    'pyppeteer',
]
TEST_REQUIREMENTS = [
    'pytest-cov',
]
FOLDER = dirname(abspath(__file__))
DESCRIPTION = '\n\n'.join(open(join(FOLDER, x)).read().strip() for x in [
    'README.md',
    'CHANGES.md'])


setup(
    name='crosscompute-prints',
    version='0.0.1',
    description='Print documents',
    long_description=DESCRIPTION,
    long_description_content_type='text/markdown',
    classifiers=APPLICATION_CLASSIFIERS,
    author='CrossCompute Inc',
    author_email='support@crosscompute.com',
    url='https://github.com/crosscompute/crosscompute-prints',
    keywords='crosscompute',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    extras_require={'test': TEST_REQUIREMENTS},
    install_requires=APPLICATION_REQUIREMENTS,
    entry_points=ENTRY_POINTS)
