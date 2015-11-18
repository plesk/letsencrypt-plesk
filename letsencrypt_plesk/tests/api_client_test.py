"""Test for letsencrypt_plesk.api_client."""
import unittest
import pkg_resources
import os

from letsencrypt import errors
from letsencrypt_plesk import api_client


class PleskApiClientTest(unittest.TestCase):
    TEST_DATA_PATH = pkg_resources.resource_filename(
        "letsencrypt_plesk.tests", "testdata")

    def setUp(self):
        super(PleskApiClientTest, self).setUp()
        self.plesk_api_client = api_client.PleskApiClient()

    def test_check_version_supported(self):
        self.plesk_api_client.PSA_PATH = os.path.join(
            self.TEST_DATA_PATH, 'psa')
        self.plesk_api_client.check_version()

    def test_check_version_not_supported(self):
        self.plesk_api_client.PSA_PATH = os.path.join(
            self.TEST_DATA_PATH, 'psa8')
        self.assertRaises(errors.NotSupportedError,
                          self.plesk_api_client.check_version)

    def test_check_version_not_installed(self):
        self.plesk_api_client.PSA_PATH = os.path.join(
            self.TEST_DATA_PATH, 'not_exists')
        self.assertRaises(errors.NoInstallationError,
                          self.plesk_api_client.check_version)

    def test_check_version_with_secret_key(self):
        self.plesk_api_client.PSA_PATH = 'unreachable'
        self.plesk_api_client.secret_key = '3c4941c1-890b-5690-0c44f037ed1c'
        self.plesk_api_client.check_version()

    def test_get_secret_key(self):
        self.plesk_api_client.secret_key = None
        self.plesk_api_client.CLI_PATH = os.path.join(
            self.TEST_DATA_PATH, 'psa', 'bin')
        self.assertEqual('3c4941c1-890b-5690-0c44f037ed1c',
                         self.plesk_api_client.get_secret_key())

if __name__ == "__main__":
    unittest.main()  # pragma: no cover
