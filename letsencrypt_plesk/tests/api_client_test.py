"""Test for letsencrypt_plesk.api_client."""
import unittest
import mock
import pkg_resources
import os

from certbot import errors
from letsencrypt_plesk import api_client


class PleskApiClientTest(unittest.TestCase):
    TEST_DATA_PATH = pkg_resources.resource_filename(
        "letsencrypt_plesk.tests", "testdata")

    def setUp(self):
        super(PleskApiClientTest, self).setUp()
        self.api_client = api_client.PleskApiClient()
        self.api_client.PSA_PATH = os.path.join(
            self.TEST_DATA_PATH, 'psa')
        self.api_client.CLI_PATH = os.path.join(
            self.TEST_DATA_PATH, 'psa', 'bin')

    def test_ssl_port_found(self):
        uri = self.api_client.get_api_uri(
            os.path.join(self.TEST_DATA_PATH, 'conf/plesk.ssl.conf.txt'))
        self.assertEqual(uri, "https://127.0.0.1:1234/enterprise/control/agent.php")

    def test_ssl_port_priority(self):
        uri = self.api_client.get_api_uri(
            os.path.join(self.TEST_DATA_PATH, 'conf/plesk.ssl-priority.conf.txt'))
        self.assertEqual(uri, "https://127.0.0.1:1234/enterprise/control/agent.php")

    def test_non_ssl_port_found(self):
        uri = self.api_client.get_api_uri(
            os.path.join(self.TEST_DATA_PATH, 'conf/plesk.conf.txt'))
        self.assertEqual(uri, "http://127.0.0.1:5678/enterprise/control/agent.php")

    def test_no_config_found(self):
        uri = self.api_client.get_api_uri(
            os.path.join(self.TEST_DATA_PATH, 'conf/plesk.empty.conf.txt'))
        self.assertEqual(uri, "https://127.0.0.1:8443/enterprise/control/agent.php")

    def test_no_config_file_found_leads_to_default_port(self):
        uri = self.api_client.get_api_uri(
            os.path.join(self.TEST_DATA_PATH, 'conf/plesk.non-existing.conf.txt'))
        self.assertEqual(uri, "https://127.0.0.1:8443/enterprise/control/agent.php")

    def test_check_version_supported(self):
        self.api_client.check_version()

    def test_check_version_not_supported(self):
        self.api_client.PSA_PATH = os.path.join(
            self.TEST_DATA_PATH, 'psa8')
        self.assertRaises(errors.NotSupportedError,
                          self.api_client.check_version)

    def test_check_version_not_installed(self):
        self.api_client.PSA_PATH = os.path.join(
            self.TEST_DATA_PATH, 'not_exists')
        self.assertRaises(errors.NoInstallationError,
                          self.api_client.check_version)

    def test_check_version_with_secret_key(self):
        self.api_client.PSA_PATH = 'unreachable'
        self.api_client.secret_key = '3c4941c1-890b-5690-0c44f037ed1c'
        self.api_client.check_version()

    def test_get_secret_key(self):
        self.api_client.secret_key = None
        self.assertEqual('3c4941c1-890b-5690-0c44f037ed1c',
                         self.api_client.get_secret_key())
        self.assertTrue(self.api_client.secret_key_created)

    def test_get_secret_key_existing(self):
        self.api_client.execute = mock.MagicMock()
        self.api_client.secret_key = '3c4941c1-890b-5690-0c44f037ed1c'
        self.assertEqual('3c4941c1-890b-5690-0c44f037ed1c',
                         self.api_client.get_secret_key())
        self.assertFalse(self.api_client.secret_key_created)
        self.api_client.execute.assert_not_called()

    def test_execute(self):
        self.api_client.execute(
            os.path.join(self.api_client.CLI_PATH, 'secret_key'), arguments=['--help'])

    def test_execute_error(self):
        self.assertRaises(api_client.PleskApiException, self.api_client.execute,
                          os.path.join(self.api_client.CLI_PATH, 'secret_key'),
                          arguments=['--invalid-argument'])

    def test_cleanup(self):
        self.api_client.secret_key = '3c4941c1-890b-5690-0c44f037ed1c'
        self.api_client.secret_key_created = True
        self.api_client.cleanup()
        self.assertEquals(None, self.api_client.secret_key)
        self.assertFalse(self.api_client.secret_key_created)

    def test_cleanup_error(self):
        self.api_client.secret_key = '3c4941c1-890b-5690-0c44f037ed1c'
        self.api_client.secret_key_created = True
        self.api_client.execute = mock.MagicMock(side_effect=api_client.PleskApiException)
        self.api_client.cleanup()

    @mock.patch('requests.post')
    def test_request(self, post_mock):
        self.api_client.secret_key = '3c4941c1-890b-5690-0c44f037ed1c'
        self.api_client.get_api_uri = mock.MagicMock(return_value='https://plesk/api')
        post_mock.return_value = mock.MagicMock(text='<?xml version="1.0" ?><packet>ok</packet>')
        request = {'packet': 'test'}
        expected_request = '<?xml version="1.0" ?><packet>test</packet>'
        response = self.api_client.request(request)
        self.assertEqual('ok', response['packet'])
        post_mock.assert_called_once_with('https://plesk/api', data=expected_request,
                                          headers=mock.ANY, verify=mock.ANY)

    def test_dict_to_xml(self):
        request = {'packet': {'test': [{'a': '123'}, {'b': '456'}, {'c': None}]}}
        expected_request = '<?xml version="1.0" ?>' \
                           '<packet><test><a>123</a><b>456</b><c/></test></packet>'
        self.assertEqual(expected_request, api_client.DictToXml(request).__str__())

    def test_xml_to_dict(self):
        response = """<?xml version="1.0" ?>
        <packet>
            <result>
                <status>error</status>
                <code/>
                <error>
                    1
                    2
                    3
                </error>
            </result>
        </packet>"""
        actual_response = api_client.XmlToDict(response)
        self.assertEqual('error', actual_response['packet']['result']['status'])
        self.assertEqual({}, actual_response['packet']['result']['code'])
        self.assertTrue(actual_response['packet']['result']['error'].find('1'))
        self.assertTrue(actual_response['packet']['result']['error'].find('2'))
        self.assertTrue(actual_response['packet']['result']['error'].find('3'))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
