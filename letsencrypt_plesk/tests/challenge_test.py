"""Test for letsencrypt_plesk.challenge."""
import unittest
import mock

from letsencrypt_plesk import challenge
from letsencrypt_plesk.tests import api_mock


class PleskChallengeTest(unittest.TestCase):
    def setUp(self):
        super(PleskChallengeTest, self).setUp()
        self.challenge = challenge.PleskChallenge("example.com",
                                                  api_mock.PleskApiMock())

    def test_perform(self):
        self.challenge.plesk_api_client.expects_request(
            'request_site_get_one')
        self.challenge.plesk_api_client.will_response(
            'response_site_get_one_ok')

        achall = mock.MagicMock(URI_ROOT_PATH='.well-known')
        response = mock.MagicMock()
        validation = mock.MagicMock(encode=lambda: '123')
        achall.response_and_validation.return_value = (response, validation)
        self.challenge.perform(achall)
        self.challenge.plesk_api_client.assert_called()
        self.assertEqual(self.challenge.ftp_login, 'username')
        self.assertEqual(self.challenge.www_root,
                         '/var/www/vhosts/example.com/httpdocs')

if __name__ == "__main__":
    unittest.main()  # pragma: no cover
