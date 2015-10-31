import sys

from setuptools import setup
from setuptools import find_packages


version = '0.1.0.dev0'

install_requires = [
    'acme',
    'letsencrypt',
    'requests',
    'setuptools',  # pkg_resources
    'zope.interface',
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

docs_extras = [
    'Sphinx>=1.0',  # autodoc_member_order = 'bysource', autodoc_default_flags
    'sphinx_rtd_theme',
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
    url='https://github.com/plesk/letsencrypt-plugin',
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
        'docs': docs_extras,
        'testing': testing_extras,
    },
    entry_points={
        'letsencrypt.plugins': [
            'plesk = letsencrypt_plesk.configurator:PleskConfigurator',
        ],
    },
)
