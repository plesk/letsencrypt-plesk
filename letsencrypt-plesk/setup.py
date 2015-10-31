from setuptools import setup
from setuptools import find_packages

setup(
    name='letsencrypt-plesk',
    packages=find_packages(),
    install_requires=[
        'acme',
        'letsencrypt',
        'requests',
        'zope.interface',
    ],
    entry_points={
        'letsencrypt.plugins': [
            'plesk = letsencrypt_plesk.configurator:PleskConfigurator',
        ],
    },
    include_package_data=True,
)
