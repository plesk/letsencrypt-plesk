#!/bin/bash -e

plesk bin extension --install-url https://ext.plesk.com/packages/f6847e61-33a7-4104-8dc9-d26a0183a8dd-letsencrypt/download

/usr/local/psa/var/modules/letsencrypt/venv/bin/pip install -U -e /vagrant[dev,testing] --no-deps

grep "venv" /home/vagrant/.bashrc || echo "source /usr/local/psa/var/modules/letsencrypt/venv/bin/activate" >> /home/vagrant/.bashrc
