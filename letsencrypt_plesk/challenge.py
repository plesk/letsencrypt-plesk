"""PleskChallenge"""
import logging
import os
from tempfile import mkstemp

from letsencrypt import errors

from letsencrypt_plesk import api_client

logger = logging.getLogger(__name__)


class PleskChallenge(object):
    """Class performs challenges within the Plesk configurator."""

    def __init__(self, domain, plesk_api_client):
        self.domain = domain
        self.plesk_api_client = plesk_api_client
        self.www_root = None
        self.ftp_login = None
        self.verify_path = None
        self.full_path = None

    def perform(self, achall):
        """Perform a challenge on Plesk."""
        response, validation = achall.response_and_validation()
        self._put_validation_file(
            domain=self.domain,
            file_path=achall.URI_ROOT_PATH,
            file_name=achall.chall.encode("token"),
            content=validation.encode())
        return response

    def _put_validation_file(self, domain, file_path, file_name, content):
        """Put file to the domain with validation content"""
        request = {'packet': {'site': {'get': [
            {'filter': {'name': domain}},
            {'dataset': {'hosting': {}}},
        ]}}}
        response = self.plesk_api_client.request(request)

        api_result = response['packet']['site']['get']['result']
        if 'ok' != api_result['status']:
            error_text = str(api_result['errtext'])
            raise errors.DvAuthError('Site get failure: %s' % error_text)

        hosting_props = api_result['data']['hosting']['vrt_hst']['property']
        self.www_root = next(
            x['value'] for x in hosting_props if 'www_root' == x['name'])
        self.ftp_login = next(
            x['value'] for x in hosting_props if 'ftp_login' == x['name'])

        self.verify_path = os.path.join(self.www_root, file_path)
        full_path = os.path.join(self.verify_path, file_name)
        self._create_file(full_path, content)

    def cleanup(self, achall):
        """Remove validation file and directories."""
        try:
            if self.www_root and self.ftp_login:
                file_name = achall.chall.encode("token")
                full_path = os.path.join(self.verify_path, file_name)
                self._remove_file(full_path)
        except api_client.PleskApiException as e:
            logger.debug(str(e))

    def _remove_file(self, full_path):
        if os.path.exists(full_path):
            self.plesk_api_client.filemng(
                [self.ftp_login, "rm", full_path])

        while self._is_sub_path(self.verify_path, self.www_root):
            if os.path.exists(self.verify_path):
                if len(os.listdir(self.verify_path)) > 0:
                    break
                self.plesk_api_client.filemng(
                    [self.ftp_login, "rmdir", self.verify_path])
            self.verify_path = os.path.dirname(self.verify_path)

    @staticmethod
    def _is_sub_path(child, parent):
        child = os.path.realpath(child)
        parent = os.path.join(os.path.realpath(parent), '')
        common = os.path.commonprefix([child, parent])
        return common == parent and not child == parent

    def _create_file(self, full_path, content):
        fh, tmp_path = mkstemp()
        with os.fdopen(fh, 'w') as tmp_file:
            tmp_file.write(str(content))
        try:
            if not os.path.exists(self.verify_path):
                self.plesk_api_client.filemng(
                    [self.ftp_login, "mkdir", self.verify_path, "-p"])
            self.plesk_api_client.filemng(
                [self.ftp_login, "cp2perm", tmp_path, full_path, "0644"])
        finally:
            os.unlink(tmp_path)
