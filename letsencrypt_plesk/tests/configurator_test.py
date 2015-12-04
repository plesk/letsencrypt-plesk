"""Test for letsencrypt_plesk.configurator."""
import unittest
import mock
import pkg_resources
import os

from letsencrypt import errors
from letsencrypt_plesk import configurator
from letsencrypt_plesk.tests import api_mock
from acme import challenges


class PleskConfiguratorTest(unittest.TestCase):
    def setUp(self):
        super(PleskConfiguratorTest, self).setUp()
        self.configurator = configurator.PleskConfigurator(
            config=mock.MagicMock(),
            name="plesk")
        self.configurator.plesk_api_client = api_mock.PleskApiMock()
        self.configurator.prepare()

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

    def test_get_all_certs_keys(self):
        self.assertEqual([], self.configurator.get_all_certs_keys())

    def test_get_chall_pref(self):
        self.assertEqual([challenges.HTTP01],
                         self.configurator.get_chall_pref('example.com'))

    @mock.patch('letsencrypt_plesk.challenge.PleskChallenge')
    def test_perform(self, challenge_mock):
        challenge_mock().perform = mock.MagicMock()
        achalls = [
            self._mock_achall('example.com'),
            self._mock_achall('www.example.com'),
        ]
        responses = self.configurator.perform(achalls)
        self.assertEqual(len(achalls), len(responses))
        challenge = self.configurator.plesk_challenges['example.com']
        challenge.perform.assert_has_calls([mock.call(a) for a in achalls])

    @staticmethod
    def _mock_achall(domain):
        achall = mock.MagicMock()
        achall.domain = domain
        return achall

    def test_deploy_cert(self):
        self.configurator.deploy_cert('example.com',
                                      self._mock_file('test.crt'),
                                      self._mock_file('test.key'))
        with open(self._mock_file('test.crt')) as cert_file:
            self.assertEqual(
                cert_file.read(),
                self.configurator.plesk_deployers['example.com'].cert_data)
        with open(self._mock_file('test.key')) as key_file:
            self.assertEqual(
                key_file.read(),
                self.configurator.plesk_deployers['example.com'].key_data)

    def test_deploy_cert_www(self):
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

    @staticmethod
    def _mock_file(name):
        return pkg_resources.resource_filename(
            "letsencrypt_plesk.tests", os.path.join("testdata", name))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
