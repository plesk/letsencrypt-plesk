"""Plesk Configuration"""
import logging

import os
import zope.interface

from pkg_resources import parse_version

from acme import challenges

from certbot import interfaces
from certbot import errors

from certbot.plugins import common

from letsencrypt_plesk import api_client
from letsencrypt_plesk import challenge
from letsencrypt_plesk import deployer

logger = logging.getLogger(__name__)


class PleskConfigurator(common.Plugin):
    """Plesk Configurator"""
    zope.interface.implements(interfaces.IAuthenticator, interfaces.IInstaller)
    zope.interface.classProvides(interfaces.IPluginFactory)

    description = "Plesk"

    @classmethod
    def add_parser_arguments(cls, add):
        add("secret-key", default=os.getenv('LE_PLESK_SECRET_KEY'),
            help="Plesk API-RPC authentication secret key.")
        add("secure-panel", action="store_true",
            help="Use the certificate to secure connections to Plesk.")

    def __init__(self, *args, **kwargs):
        """Initialize Plesk Configurator."""
        super(PleskConfigurator, self).__init__(*args, **kwargs)

        self.plesk_challenges = {}
        self.plesk_deployers = {}
        # This will be set in the prepare function
        self.plesk_api_client = None

    def prepare(self):
        """Prepare the authenticator/installer."""
        if self.plesk_api_client is None:
            self.plesk_api_client = api_client.PleskApiClient(
                secret_key=self.conf('secret-key'))
        self.plesk_api_client.check_version()

    @staticmethod
    def more_info():
        """Human-readable string to help understand the module"""
        return "Configures Plesk to authenticate and install SSL certificate."

    # Authenticator methods below

    @staticmethod
    def get_chall_pref(unused_domain):
        """Return list of challenge preferences."""
        return [challenges.HTTP01]

    def perform(self, achalls):
        """Perform the configuration related challenge."""
        responses = []
        for x in achalls:
            self.plesk_challenges[x.domain] = challenge.PleskChallenge(
                x.domain, self.plesk_api_client)

        for x in achalls:
            domain = x.domain
            if domain.startswith("www."):
                if domain[4:] in self.plesk_challenges:
                    domain = domain[4:]
            responses.append(self.plesk_challenges[domain].perform(x))
        return responses

    def cleanup(self, achalls):
        """Revert all challenges."""
        for x in achalls:
            domain = x.domain
            if domain.startswith("www."):
                if domain[4:] in self.plesk_challenges:
                    domain = domain[4:]
            if domain in self.plesk_challenges:
                self.plesk_challenges[domain].cleanup(x)
        self.plesk_api_client.cleanup()

    # Installer methods below

    def get_all_names(self):
        """Returns all names that may be authenticated."""
        request = {'packet': [
            {'webspace': {'get': [
                {'filter': {}},
                {'dataset': {'gen_info': {}}},
            ]}},
            {'site': {'get': [
                {'filter': {}},
                {'dataset': {'gen_info': {}}},
            ]}},
        ]}
        response = self.plesk_api_client.request(request)
        return self._compact_names([
            self._get_names(response['packet']['webspace']['get']['result']),
            self._get_names(response['packet']['site']['get']['result']),
        ])

    def _get_names(self, api_result):
        if isinstance(api_result, list):
            return [self._get_names(x) for x in api_result]
        if 'ok' != api_result['status'] or 'data' not in api_result:
            return None
        return api_result['data']['gen_info']['ascii-name']

    def _compact_names(self, names):
        compact = []
        for name in names:
            if isinstance(name, list):
                compact += self._compact_names(name)
            elif name is None:
                continue
            else:
                compact.append(name)
        return compact

    @staticmethod
    def enhance(unused_domain, unused_enhancement, unused_options=None):
        """No enhancements are supported now."""
        raise errors.NotSupportedError('No enhancements are supported now.')

    @staticmethod
    def supported_enhancements():
        """Returns a list of supported enhancements."""
        return []

    @staticmethod
    def get_all_certs_keys():
        """No ability to retrieve certificate data from Plesk."""
        return []

    def deploy_cert(self, domain, cert_path, key_path, chain_path=None,
                    fullchain_path=None):  # pylint: disable=unused-argument
        """Initialize deploy certificate in Plesk via API."""
        if domain.startswith("www."):
            if domain[4:] in self.plesk_deployers:
                return
        elif "www." + domain in self.plesk_deployers:
            del self.plesk_deployers["www." + domain]

        if self.is_certificate_update_available():
            plesk_deployer = deployer.Plesk17Deployer(self.plesk_api_client, domain)
        else:
            plesk_deployer = deployer.PleskDeployer(self.plesk_api_client, domain)

        with open(cert_path) as cert_file:
            cert_data = cert_file.read()
        with open(key_path) as key_file:
            key_data = key_file.read()
        if chain_path:
            with open(chain_path) as chain_file:
                chain_data = chain_file.read()
        else:
            chain_data = None

        plesk_deployer.init_cert(cert_data, key_data, chain_data)
        self.plesk_deployers[domain] = plesk_deployer

    def save(self, unused_title=None, temporary=False):
        """Push Plesk to deploy certificate."""
        if temporary:
            return
        for domain in self.plesk_deployers:
            self.plesk_deployers[domain].save(
                secure_plesk=self.conf('secure-panel'))

    @staticmethod
    def rollback_checkpoints(unused_rollback=1):
        """Revert deployer state to the previous."""
        raise errors.NotSupportedError()

    def recovery_routine(self):
        """Revert deployer changes."""
        for domain in self.plesk_deployers:
            self.plesk_deployers[domain].revert()

    @staticmethod
    def view_config_changes():
        """No ability to preview configs generated by Plesk."""
        raise errors.NotSupportedError(
            'No ability to preview configs generated by Plesk')

    @staticmethod
    def config_test():
        """Plesk configuration is always valid."""
        pass  # pragma: no cover

    def restart(self):
        """Web server has already restarted. Cleanup only."""
        self.plesk_api_client.cleanup()

    def is_certificate_update_available(self):
        """Checks availability of certificate/update API method"""
        request = {'packet': {
            'server': {'get_protos': {}},
        }}
        response = self.plesk_api_client.request(request)
        api_result = response['packet']['server']['get_protos']['result']
        if 'ok' != api_result['status']:
            return False
        protos = api_result['protos']['proto']
        for proto in protos:
            if parse_version('1.6.8.0') <= parse_version(proto):
                return True
        return False
