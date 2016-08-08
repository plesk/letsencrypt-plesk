"""PleskDeployer"""
import logging
import os
import sys
from tempfile import mkstemp

from certbot import errors

logger = logging.getLogger(__name__)


class PleskDeployer(object):
    """Class performs deploy operations within the Plesk configurator."""

    def __init__(self, plesk_api_client, domain):
        """Initialize Plesk Certificate Deployer"""
        self.plesk_api_client = plesk_api_client
        self.domain = domain
        self.data = {'cert': None, 'key': None, 'chain': None}
        self.cert_installed = self.cert_assigned = self.plesk_secured = False

    def cert_name(self):
        """Return name of the domain certificate in Plesk."""
        return "Lets Encrypt %s" % self.domain

    def get_certs(self):
        """Return list of certificates registered in Plesk."""
        request = {'packet': {
            'certificate': {
                'get-pool': {'filter': {'domain-name': self.domain}}
            }
        }}
        response = self.plesk_api_client.request(request)
        api_result = response['packet']['certificate']['get-pool']['result']
        if 'ok' != api_result['status'] \
                or 'certificates' not in api_result \
                or not isinstance(api_result['certificates'], dict) \
                or 'certificate' not in api_result['certificates']:
            return []
        certs = api_result['certificates']['certificate']
        if isinstance(certs, dict):
            certs = [certs]
        return [cert['name'] for cert in certs]

    def init_cert(self, cert_data, key_data, chain_data=None):
        """Initialize certificate data."""
        self.data = {'cert': cert_data, 'key': key_data, 'chain': chain_data}

    def _get_full_cert_data(self):
        return "{key}\n{cert}\n{chain}".format(
            key=self.data['key'],
            cert=self.data['cert'],
            chain=self.data['chain'] if self.data['chain'] else "")

    def install_cert(self):
        """Install certificate to the domain repository in Plesk."""
        request = {'packet': {
            'certificate': {
                'install': [
                    {'name': self.cert_name()},
                    {'site': self.domain},
                    {'content': [
                        {'csr': {}},
                        {'pvt': self.data['key']},
                        {'cert': self.data['cert']},
                        {'ca': self.data['chain'] if self.data['chain'] else {}},
                    ]}
                ]
            }
        }}
        response = self.plesk_api_client.request(request)
        api_result = response['packet']['certificate']['install']['result']
        if 'ok' != api_result['status']:
            error_text = str(api_result['errtext'])
            raise errors.PluginError(
                'Install certificate failure: %s' % error_text)
        self.cert_installed = True

    def assign_cert(self):
        """Assign certificate to the domain and enable SSL."""
        request = {'packet': {
            'site': {'set': [
                {'filter': {'name': self.domain}},
                {'values': {'hosting': {'vrt_hst': [
                    {'property': [
                        {'name': 'ssl'},
                        {'value': 'true'},
                    ]},
                    {'property': [
                        {'name': 'certificate_name'},
                        {'value': self.cert_name()},
                    ]},
                ]}}}
            ]}
        }}
        response = self.plesk_api_client.request(request)
        api_result = response['packet']['site']['set']['result']
        if 'ok' != api_result['status']:
            error_text = str(api_result['errtext'])
            raise errors.PluginError(
                'Assign certificate failure: %s' % error_text)
        self.cert_assigned = True

    def remove_cert(self):
        """Remove certificate from the domain repository in Plesk."""
        request = {'packet': {
            'certificate': {
                'remove': [
                    {'filter': {'name': self.cert_name()}},
                    {'site': self.domain},
                ]
            }
        }}
        response = self.plesk_api_client.request(request)
        api_result = response['packet']['certificate']['remove']['result']
        if 'ok' != api_result['status']:
            error_text = str(api_result['errtext'])
            raise errors.PluginError(
                'Remove certificate failure: %s' % error_text)

    def revert(self):
        """Revert changes in Plesk."""
        if self.cert_installed:
            self.remove_cert()
            self.cert_installed = False
        self.cert_assigned = False
        self.plesk_secured = False

    def save(self, secure_plesk=False):
        """Provision changes in Plesk."""
        if not self.cert_installed:
            if self.cert_name() in self.get_certs():
                self.remove_cert()
            self.install_cert()
        if not self.cert_assigned:
            self.assign_cert()
        if secure_plesk and not self.plesk_secured:
            self.secure_plesk()

    def secure_plesk(self):
        """Use the certificate to secure connections to Plesk."""
        fh, cert_tmp = mkstemp()
        with os.fdopen(fh, 'w') as tmp_file:
            tmp_file.write(self._get_full_cert_data())

        cert_cmd = os.path.join(self.plesk_api_client.BIN_PATH, "certmng")
        cert_args = ["--setup-cp-certificate", "--certificate=%s" % cert_tmp]
        if sys.platform == 'win32':
            cert_cmd = os.path.join(
                self.plesk_api_client.CLI_PATH, "extension.exe")
            cert_args = ["--exec", "letsencrypt", "certmng.php"] + cert_args

        try:
            self.plesk_api_client.execute(cert_cmd, cert_args)
        finally:
            os.unlink(cert_tmp)
        self.plesk_secured = True


class Plesk17Deployer(PleskDeployer):
    """Class performs deploy operations within the Plesk configurator."""

    def update_cert(self):
        """Update the certificate in Plesk."""
        request = {'packet': {
            'certificate': {
                'update': [
                    {'name': self.cert_name()},
                    {'site': self.domain},
                    {'content': [
                        {'csr': {}},
                        {'pvt': self.data['key']},
                        {'cert': self.data['cert']},
                        {'ca': self.data['chain'] if self.data['chain'] else {}},
                    ]}
                ]
            }
        }}
        response = self.plesk_api_client.request(request)
        api_result = response['packet']['certificate']['update']['result']
        if 'ok' != api_result['status']:
            error_text = str(api_result['errtext'])
            raise errors.PluginError(
                'Update certificate failure: %s' % error_text)
        self.cert_installed = True

    def save(self, secure_plesk=False):
        """Provision changes in Plesk."""
        if not self.cert_installed:
            if self.cert_name() in self.get_certs():
                self.update_cert()
            else:
                self.install_cert()
        if not self.cert_assigned:
            self.assign_cert()
        if secure_plesk and not self.plesk_secured:
            self.secure_plesk()
