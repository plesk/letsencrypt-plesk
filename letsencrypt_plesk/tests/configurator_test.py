"""Test for letsencrypt_plesk.configurator."""
import unittest
import mock
import pkg_resources
import os

from certbot import errors
from letsencrypt_plesk import configurator
from letsencrypt_plesk.tests import api_mock
from acme import challenges


class PleskConfiguratorTest(unittest.TestCase):
    # pylint: disable=too-many-public-methods
    def setUp(self):
        super(PleskConfiguratorTest, self).setUp()
        self.configurator = configurator.PleskConfigurator(
            config=mock.MagicMock(),
            name="plesk")
        self.configurator.plesk_api_client = api_mock.PleskApiMock()
        self.configurator.prepare()

    def test_add_parser_arguments(self):
        add = mock.MagicMock()
        configurator.PleskConfigurator.add_parser_arguments(add)
        self.assertTrue(0 < add.call_count)

    @mock.patch('letsencrypt_plesk.api_client.PleskApiClient')
    def test_prepare(self, plesk_api_client):
        configurator.PleskConfigurator(
            config=mock.MagicMock(plesk_secret_key='test-key'),
            name="plesk").prepare()
        plesk_api_client.assert_called_once_with(secret_key='test-key')

    def test_more_info(self):
        self.assertTrue(self.configurator.more_info())

    def test_get_all_names_none(self):
        self.configurator.plesk_api_client.expects_request(
            'request_site_get_all')
        self.configurator.plesk_api_client.will_response(
            'response_site_get_all_none')
        names = self.configurator.get_all_names()
        self.configurator.plesk_api_client.assert_called()
        self.assertEqual(names, [])

    def test_get_all_names_one(self):
        self.configurator.plesk_api_client.expects_request(
            'request_site_get_all')
        self.configurator.plesk_api_client.will_response(
            'response_site_get_all_one')
        names = self.configurator.get_all_names()
        self.configurator.plesk_api_client.assert_called()
        self.assertEqual(names, ['first.example.com', 'second.example.com'])

    def test_get_all_names_many(self):
        self.configurator.plesk_api_client.expects_request(
            'request_site_get_all')
        self.configurator.plesk_api_client.will_response(
            'response_site_get_all_many')
        names = self.configurator.get_all_names()
        self.configurator.plesk_api_client.assert_called()
        self.assertEqual(names, [
            'first.example.com', 'second.example.com', 'xn--d1abbgf6aiiy.xn--p1ai',
            'third.example.com', 'fourth.example.com'])

    def test_supported_enhancements(self):
        self.assertEqual([], self.configurator.supported_enhancements())

    def test_enhance(self):
        self.assertRaises(errors.NotSupportedError, self.configurator.enhance,
                          'example.com', 'redirect')

    def test_view_config_changes(self):
        self.assertRaises(errors.NotSupportedError,
                          self.configurator.view_config_changes)

    def test_rollback_checkpoints(self):
        self.assertRaises(errors.NotSupportedError,
                          self.configurator.rollback_checkpoints, 1)

    def test_get_all_certs_keys(self):
        self.assertEqual([], self.configurator.get_all_certs_keys())

    def test_get_chall_pref(self):
        self.assertEqual([challenges.HTTP01],
                         self.configurator.get_chall_pref('example.com'))

    @mock.patch('letsencrypt_plesk.challenge.PleskChallenge')
    def test_perform(self, challenge_mock):
        challenge_mock.perform = mock.MagicMock()
        achalls = [self._mock_achall('example.com'), self._mock_achall('www.example.com')]
        responses = self.configurator.perform(achalls)
        self.assertEqual(len(achalls), len(responses))
        challenge = self.configurator.plesk_challenges['example.com']
        challenge.perform.assert_has_calls([mock.call(a) for a in achalls])

    def test_cleanup(self):
        achalls = [self._mock_achall('example.com'), self._mock_achall('www.example.com')]
        self.configurator.plesk_challenges = {'example.com': mock.MagicMock(),
                                              'www.example.com': mock.MagicMock()}
        self.configurator.cleanup(achalls)
        self.configurator.plesk_api_client.cleanup.assert_called_once_with()
        self.configurator.plesk_challenges['example.com'].cleanup.assert_has_calls(
            [mock.call(a) for a in achalls])
        self.configurator.plesk_challenges['www.example.com'].cleanup.assert_not_called()

    @staticmethod
    def _mock_achall(domain):
        achall = mock.MagicMock()
        achall.domain = domain
        return achall

    @mock.patch('letsencrypt_plesk.deployer.Plesk17Deployer')
    def test_deploy_cert(self, unused_mock_deployer):
        self._deploy_cert(True)

    @mock.patch('letsencrypt_plesk.deployer.PleskDeployer')
    def test_deploy_cert_legacy(self, unused_mock_deployer):
        self._deploy_cert(False)

    def _deploy_cert(self, is_certificate_update_available):
        cert_file = self._mock_file('test.crt')
        with open(cert_file) as fd:
            cert_data = fd.read()
        key_file = self._mock_file('test.key')
        with open(key_file) as fd:
            key_data = fd.read()
        chain_file = self._mock_file('ca.crt')
        with open(chain_file) as fd:
            chain_data = fd.read()
        full_file = self._mock_file('full.crt')

        self.configurator.is_certificate_update_available = mock.MagicMock(
            return_value=is_certificate_update_available)
        self.configurator.deploy_cert('example.com', cert_file, key_file, chain_file, full_file)
        self.assertTrue('example.com' in self.configurator.plesk_deployers)
        deployer = self.configurator.plesk_deployers['example.com']
        deployer.init_cert.assert_called_with(cert_data, key_data, chain_data)

    def test_deploy_cert_www(self):
        self.configurator.is_certificate_update_available = mock.MagicMock(return_value=True)
        self.configurator.deploy_cert('www.example.com',
                                      self._mock_file('test.crt'),
                                      self._mock_file('test.key'))
        self.configurator.deploy_cert('example.com',
                                      self._mock_file('test.crt'),
                                      self._mock_file('test.key'))
        self.configurator.deploy_cert('www.example.com',
                                      self._mock_file('test.crt'),
                                      self._mock_file('test.key'))
        self.assertTrue('example.com' in self.configurator.plesk_deployers)
        self.assertFalse('www.example.com' in self.configurator.plesk_deployers)

    def test_save(self):
        mock_deployer = mock.MagicMock()
        self.configurator.config.plesk_secure_panel = True
        self.configurator.plesk_deployers = {'example.com': mock_deployer}
        self.configurator.save()
        mock_deployer.save.assert_called_once_with(secure_plesk=True)

    def test_save_temporary(self):
        mock_deployer = mock.MagicMock()
        self.configurator.plesk_deployers = {'example.com': mock_deployer}
        self.configurator.save(temporary=True)
        mock_deployer.save.assert_not_called()

    def test_recovery_routine(self):
        mock_deployer = mock.MagicMock()
        self.configurator.plesk_deployers = {'example.com': mock_deployer}
        self.configurator.recovery_routine()
        mock_deployer.revert.assert_called_once_with()

    def test_restart(self):
        self.configurator.restart()
        self.configurator.plesk_api_client.cleanup.assert_called_once_with()

    def test_is_certificate_update_available(self):
        self.configurator.plesk_api_client.expects_request(
            'request_server_get_protos')
        self.configurator.plesk_api_client.will_response(
            'response_server_get_protos_ok')
        self.assertTrue(self.configurator.is_certificate_update_available())
        self.configurator.plesk_api_client.assert_called()

    def test_is_certificate_update_available_legacy(self):
        self.configurator.plesk_api_client.expects_request(
            'request_server_get_protos')
        self.configurator.plesk_api_client.will_response(
            'response_server_get_protos_legacy')
        self.assertFalse(self.configurator.is_certificate_update_available())
        self.configurator.plesk_api_client.assert_called()

    def test_is_certificate_update_available_error(self):
        self.configurator.plesk_api_client.expects_request(
            'request_server_get_protos')
        self.configurator.plesk_api_client.will_response(
            'response_server_get_protos_error')
        self.assertFalse(self.configurator.is_certificate_update_available())
        self.configurator.plesk_api_client.assert_called()

    @staticmethod
    def _mock_file(name):
        return pkg_resources.resource_filename(
            "letsencrypt_plesk.tests", os.path.join("testdata", name))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
