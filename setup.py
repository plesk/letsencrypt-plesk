import codecs
import os
import re
import sys

from setuptools import setup
from setuptools import find_packages


def read_file(filename, encoding='utf8'):
    """Read unicode from given file."""
    with codecs.open(filename, encoding=encoding) as fd:
        return fd.read()

here = os.path.abspath(os.path.dirname(__file__))

# read version number (and other metadata) from package init
init_fn = os.path.join(here, 'letsencrypt_plesk', '__init__.py')
meta = dict(re.findall(r"""__([a-z]+)__ = '([^']+)""", read_file(init_fn)))

version = meta['version']

install_requires = [
    'acme',
    'certbot',
    'letsencrypt',  # backward compatibility of entry point
    'requests[security]==2.11.1', # workaround for #141
    'setuptools',  # pkg_resources
    'zope.interface',
    'pyopenssl==16.0.0', # workaround for #117
]

if sys.version_info < (2, 7):
    install_requires.append('mock<1.1.0')
else:
    install_requires.append('mock')

dev_extras = [
    # Pin astroid==1.3.5, pylint==1.4.2 as a workaround for #289
    'astroid==1.3.5',
    'pylint==1.4.2',  # upstream #248
    'twine',
    'wheel',
]

testing_extras = [
    'coverage',
    'nose',
    'nosexcover',
    'pep8',
    'tox',
]

setup(
    name='letsencrypt-plesk',
    version=version,
    description="Plesk plugin for Let's Encrypt client",
    url='https://github.com/plesk/letsencrypt-plesk',
    author='Eugene Kazakov',
    author_email='eugene.a.kazakov@gmail.com',
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],

    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'dev': dev_extras,
        'testing': testing_extras,
    },
    entry_points={
        'certbot.plugins': [
            'plesk = letsencrypt_plesk.configurator:PleskConfigurator',
        ],
    },
)
