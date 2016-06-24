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
        # pylint: disable=protected-access
        self.challenge._init_domain_props = mock.MagicMock()
        self.challenge._create_file = mock.MagicMock()
        self.challenge.www_root = '/www'
        self.challenge.perform(self._mock_achall())
        self.assertEqual(self.challenge.verify_path, '/www/.well-known')
        self.challenge._create_file.assert_has_calls([
            mock.call('/www/.well-known/.htaccess', mock.ANY),
            mock.call('/www/.well-known/abc', '123')])

    @mock.patch('sys.platform', 'win32')
    def test_perform_win32(self):
        # pylint: disable=protected-access
        self.challenge._init_domain_props = mock.MagicMock()
        self.challenge._create_file = mock.MagicMock()
        self.challenge.www_root = 'C:/inetpub'
        self.challenge.perform(self._mock_achall())
        self.assertEqual(self.challenge.verify_path, 'C:/inetpub/.well-known')
        self.challenge._create_file.assert_has_calls([
            mock.call('C:/inetpub/.well-known/web.config', mock.ANY),
            mock.call('C:/inetpub/.well-known/abc', '123')])

    def test_cleanup(self):
        # pylint: disable=protected-access
        self.challenge._remove_file = mock.MagicMock()
        self.challenge.verify_path = '/www/.well-known'
        self.challenge.www_root = '/www'
        self.challenge.ftp_login = 'ftp_user'
        self.challenge.cleanup(self._mock_achall())
        self.challenge._remove_file.assert_has_calls([
            mock.call('/www/.well-known/web.config'),
            mock.call('/www/.well-known/.htaccess'),
            mock.call('/www/.well-known/abc')])

    def test_cleanup_error(self):
        # pylint: disable=protected-access
        self.challenge._remove_file = mock.MagicMock()
        self.challenge._remove_file.side_effect = api_mock.api_client.PleskApiException
        self.challenge.verify_path = '/www/.well-known'
        self.challenge.www_root = '/www'
        self.challenge.ftp_login = 'ftp_user'
        self.challenge.cleanup(self._mock_achall())

    @staticmethod
    def _mock_achall():
        achall = mock.MagicMock(URI_ROOT_PATH='.well-known')
        achall.chall.encode.return_value = 'abc'
        response = mock.MagicMock()
        validation = mock.MagicMock()
        validation.encode.return_value = '123'
        achall.response_and_validation.return_value = (response, validation)
        return achall

    def test_init_domain_props(self):
        # pylint: disable=protected-access
        self.challenge.plesk_api_client.expects_request(
            'request_site_get_one')
        self.challenge.plesk_api_client.will_response(
            'response_site_get_one_ok')

        self.challenge._init_domain_props()
        self.challenge.plesk_api_client.assert_called()
        self.assertEqual(self.challenge.ftp_login, 'username')
        self.assertEqual(self.challenge.www_root, '/var/www/vhosts/example.com/httpdocs')

    def test_init_domain_props_error(self):
        # pylint: disable=protected-access
        self.challenge.plesk_api_client.expects_request(
            'request_site_get_one')
        self.challenge.plesk_api_client.will_response(
            'response_site_get_one_error')

        self.assertRaises(challenge.PleskAuthError, self.challenge._init_domain_props)
        self.challenge.plesk_api_client.assert_called()

    def test_init_domain_props_without_hosting(self):
        # pylint: disable=protected-access
        self.challenge.plesk_api_client.expects_request(
            'request_site_get_one')
        self.challenge.plesk_api_client.will_response(
            'response_site_get_one_without_hosting')

        self.assertRaises(challenge.PleskAuthError, self.challenge._init_domain_props)
        self.challenge.plesk_api_client.assert_called()

    def test_filemng(self):
        # pylint: disable=protected-access
        plesk_api_mock = self.challenge.plesk_api_client
        plesk_api_mock.BIN_PATH = '/bin'
        self.challenge.ftp_login = 'ftp_user'
        self.challenge._filemng('test')
        plesk_api_mock.execute.assert_called_once_with('/bin/filemng',
                                                       arguments=['ftp_user', 'test'])

    def test_filemng_with_user(self):
        # pylint: disable=protected-access
        plesk_api_mock = self.challenge.plesk_api_client
        plesk_api_mock.BIN_PATH = '/bin'
        self.challenge._filemng('test', user='psaadm')
        plesk_api_mock.execute.assert_called_once_with('/bin/filemng',
                                                       arguments=['psaadm', 'test'])

    def test_ls(self):
        # pylint: disable=protected-access
        self.challenge._filemng = mock.MagicMock()
        self.challenge._filemng.return_value = """
..	1439971863	4096	root	root	755
favicon.ico	1214575941	2862	root	root	644
index.html	1364580529	2241	root	root	644
.	1364580529	4096	root	root	755
"""
        self.assertEqual(['favicon.ico', 'index.html'], self.challenge._ls('/www'))
        self.challenge._filemng.assert_called_once_with('list', 'both', '/www', stdout=True)

    def test_is_sub_path(self):
        # pylint: disable=protected-access
        self.assertTrue(self.challenge._is_sub_path('/a/b/c/d', '/a/b'))
        self.assertFalse(self.challenge._is_sub_path('/a/b/c/d', '/c/d'))
        self.assertFalse(self.challenge._is_sub_path('/a/b', '/a/b'))

    def test_remove_file(self):
        # pylint: disable=protected-access
        self.challenge.verify_path = '/www/.well-known'
        self.challenge.www_root = '/www'
        self.challenge.ftp_login = 'ftp_user'
        self.challenge._filemng = mock.MagicMock()
        self.challenge._exists = mock.MagicMock(return_value=True)
        self.challenge._ls = mock.MagicMock(return_value=[])

        self.challenge._remove_file('/www/.well-known/abc')
        self.challenge._filemng.assert_has_calls([
            mock.call('rm', '/www/.well-known/abc'),
            mock.call('rmdir', '/www/.well-known')])

    def test_remove_file_not_empty_dir(self):
        # pylint: disable=protected-access
        self.challenge.verify_path = '/www/.well-known'
        self.challenge.www_root = '/www'
        self.challenge.ftp_login = 'ftp_user'
        self.challenge._filemng = mock.MagicMock()
        self.challenge._exists = mock.MagicMock(return_value=True)
        self.challenge._ls = mock.MagicMock(return_value=['zxc', 'asd', 'qwe'])

        self.challenge._remove_file('/www/.well-known/abc')
        self.challenge._filemng.assert_called_once_with('rm', '/www/.well-known/abc')

    def test_exists(self):
        # pylint: disable=protected-access
        self.challenge._filemng = mock.MagicMock(return_value='0')
        self.assertTrue(self.challenge._exists('/www/test-exists'))
        self.challenge._filemng.assert_called_once_with('file_exists', '/www/test-exists',
                                                        stdout=True)

    def test_not_exists(self):
        # pylint: disable=protected-access
        self.challenge._filemng = mock.MagicMock(return_value='1')
        self.assertFalse(self.challenge._exists('/www/test-not-exists'))
        self.challenge._filemng.assert_called_once_with('file_exists', '/www/test-not-exists',
                                                        stdout=True)

    def test_create_file(self):
        # pylint: disable=protected-access
        self.challenge._filemng = mock.MagicMock()
        self.challenge._exists = mock.MagicMock(return_value=False)
        self.challenge.verify_path = '/www/.well-known'
        self.challenge._create_file('/www/.well-known/abc', '123')
        self.challenge._filemng.assert_has_calls([
            mock.call("mkdir", "-p", "/www/.well-known"),
            mock.call("cp2perm", mock.ANY, "/www/.well-known/abc", "0644")])

    @mock.patch('sys.platform', 'win32')
    def test_create_file_win32(self):
        # pylint: disable=protected-access
        self.challenge._filemng = mock.MagicMock(return_value='C:/tmp')
        self.challenge._exists = mock.MagicMock(return_value=False)
        self.challenge.verify_path = 'C:/inetpub/.well-known'
        self.challenge._create_file('C:/inetpub/.well-known/abc', '123')
        self.challenge._filemng.assert_has_calls([
            mock.call("mkdir", "-p", "C:/inetpub/.well-known"),
            mock.call("--temp-file", mock.ANY, stdout=True),
            mock.call("cp", mock.ANY, 'C:/tmp', user="root"),
            mock.call("cp", 'C:/tmp', "C:/inetpub/.well-known/abc")])

if __name__ == "__main__":
    unittest.main()  # pragma: no cover
