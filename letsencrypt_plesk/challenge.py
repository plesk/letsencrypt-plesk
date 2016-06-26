"""PleskChallenge"""
import logging
import sys
import os
from tempfile import mkstemp

from certbot import errors

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

    def perform(self, achall):
        """Perform a challenge on Plesk."""
        response, validation = achall.response_and_validation()
        if not self.www_root or not self.ftp_login:
            self._init_domain_props()

        self.verify_path = os.path.join(self.www_root, achall.URI_ROOT_PATH)

        if sys.platform == 'win32':
            web_config_path = os.path.join(self.verify_path, "web.config")
            self._create_file(web_config_path, self._get_web_config())
        else:
            htaccess_path = os.path.join(self.verify_path, ".htaccess")
            self._create_file(htaccess_path, self._get_htaccess())

        full_path = os.path.join(self.verify_path, achall.chall.encode("token"))
        self._create_file(full_path, validation.encode())

        return response

    def _init_domain_props(self):
        """Put file to the domain with validation content"""
        request = {'packet': {'site': {'get': [
            {'filter': {'name': self.domain}},
            {'dataset': {'hosting': {}}},
        ]}}}
        response = self.plesk_api_client.request(request)

        api_result = response['packet']['site']['get']['result']
        if 'ok' != api_result['status']:
            error_text = str(api_result['errtext'])
            raise PleskAuthError(
                'Site "%s" get failure: %s' % (self.domain, error_text))

        if 'vrt_hst' not in api_result['data']['hosting']:
            raise PleskAuthError(
                'Cannot authenticate domain "%s" without hosting' % self.domain)

        hosting_props = api_result['data']['hosting']['vrt_hst']['property']
        self.www_root = next(
            x['value'] for x in hosting_props if 'www_root' == x['name'])
        self.ftp_login = next(
            x['value'] for x in hosting_props if 'ftp_login' == x['name'])

    def cleanup(self, achall):
        """Remove validation file and directories."""
        try:
            if self.www_root and self.ftp_login:
                file_name = achall.chall.encode("token")

                web_config_path = os.path.join(self.verify_path, "web.config")
                self._remove_file(web_config_path)

                htaccess_path = os.path.join(self.verify_path, ".htaccess")
                self._remove_file(htaccess_path)

                full_path = os.path.join(self.verify_path, file_name)
                self._remove_file(full_path)
        except api_client.PleskApiException as e:
            logger.debug(str(e))

    def _remove_file(self, full_path):
        if self._exists(full_path):
            self._filemng("rm", full_path)

        while self._is_sub_path(self.verify_path, self.www_root):
            if self._exists(self.verify_path):
                if len(self._ls(self.verify_path)) > 0:
                    break
                self._filemng("rmdir", self.verify_path)
            self.verify_path = os.path.dirname(self.verify_path)

    @staticmethod
    def _is_sub_path(child, parent):
        child = os.path.realpath(child)
        parent = os.path.join(os.path.realpath(parent), '')
        common = os.path.commonprefix([child, parent])
        return common == parent and not child == parent

    def _ls(self, path):
        ls_data = []
        ls_out = self._filemng("list", "both", path, stdout=True)
        for entry in ls_out.splitlines():
            if 0 == len(entry.strip()):
                continue
            name, _ = entry.split(None, 1)
            if name not in ['.', '..']:
                ls_data.append(name)
        return ls_data

    def _exists(self, path):
        return "0" == self._filemng("file_exists", path, stdout=True).strip()

    def _create_file(self, full_path, content):
        fh, tmp_path = mkstemp()
        with os.fdopen(fh, 'w') as tmp_file:
            tmp_file.write(str(content))
        try:
            if not self._exists(self.verify_path):
                self._filemng("mkdir", "-p", self.verify_path)

            if sys.platform == 'win32':
                tmp_dir = os.path.join(self.plesk_api_client.PSA_PATH, "tmp")
                tmp_source = self._filemng("--temp-file",
                                           "--destination=" + tmp_dir,
                                           stdout=True).strip()
                self._filemng("cp", tmp_path, tmp_source, user="root")
                self._filemng("cp", tmp_source, full_path)
            else:
                self._filemng("cp2perm", tmp_path, full_path, "0644")
        finally:
            os.unlink(tmp_path)

    def _filemng(self, *args, **kwargs):
        """File operations in Plesk are implemented in filemng util"""
        if 'user' in kwargs:
            arguments = [kwargs['user']]
            del kwargs['user']
        else:
            arguments = [self.ftp_login]
        arguments += list(args)
        return self.plesk_api_client.execute(
            os.path.join(self.plesk_api_client.BIN_PATH, "filemng"),
            arguments=arguments, **kwargs)

    @staticmethod
    def _get_htaccess():
        """Content of .htaccess file"""
        return """Satisfy any
<IfModule mod_rewrite.c>
    RewriteEngine off
</IfModule>
"""

    @staticmethod
    def _get_web_config():
        """Content of web.config file"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <staticContent>
            <mimeMap fileExtension="." mimeType="text/plain" />
        </staticContent>
    </system.webServer>
</configuration>
"""


class PleskAuthError(errors.PluginError):
    """Authentication error with specified domain name"""
