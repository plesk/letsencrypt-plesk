"""PleskApiClient"""

import os
import subprocess
import requests
import logging
from tempfile import mkstemp

from letsencrypt import errors
from xml.dom.minidom import Document, parseString

logger = logging.getLogger(__name__)


class PleskApiClient(object):
    """Class performs API-RPC requests to Plesk"""

    PSA_PATH = "/usr/local/psa/"
    CLI_PATH = os.path.join(PSA_PATH, "bin")
    BIN_PATH = os.path.join(PSA_PATH, "admin", "bin")

    def __init__(self, host='127.0.0.1', port=8443, secret_key=None):
        self.host = host
        self.port = port
        self.scheme = 'https' if port == 8443 else 'http'
        self.secret_key_created = False
        self.secret_key = secret_key

    def check_version(self):
        """Check Plesk installed and version is supported"""
        if self.secret_key:
            return
        version = os.path.join(self.PSA_PATH, "version")
        if not os.path.exists(version):
            raise errors.NoInstallationError('Plesk is not installed')
        with open(version, 'r') as f:
            version_data = f.read()
            if not version_data.startswith('12.'):
                raise errors.NotSupportedError(
                    'Plesk version is not supported: %s' % version_data)

    def request(self, request):
        """Perform API-RPC request to Plesk"""
        if isinstance(request, dict):
            request = str(DictToXml(request))
        logger.debug("Plesk API-RPC request: %s", request)
        headers = {
            'Content-type': 'text/xml',
            'HTTP_PRETTY_PRINT': 'TRUE',
            'KEY': self.get_secret_key(),
        }
        response = requests.post(
            "{scheme}://{host}:{port}/enterprise/control/agent.php".format(
                scheme=self.scheme,
                host=self.host,
                port=self.port),
            verify=False,
            headers=headers,
            data=request)
        logger.debug("Plesk API-RPC response: %s", response.text)
        return XmlToDict(response.text.encode('utf-8'))

    def get_secret_key(self):
        """Retrieve secret key for Plesk API or creates a new one"""
        if self.secret_key:
            return self.secret_key
        self.secret_key = self.execute(
            os.path.join(self.CLI_PATH, "secret_key"),
            ["--create", "-ip-address", "127.0.0.1", "-description", __name__],
            stdout=True)
        self.secret_key_created = True
        return self.secret_key

    def cleanup(self):
        """Remove secret key from Plesk if it was created"""
        if self.secret_key and self.secret_key_created:
            try:
                self.execute(
                    os.path.join(self.CLI_PATH, "secret_key"),
                    ["--delete", "-key", self.secret_key])
            except PleskApiException as e:
                logger.debug(str(e))
            self.secret_key = None
            self.secret_key_created = False

    @staticmethod
    def execute(command, arguments=None, stdout=False):
        """Execute CLI utility"""
        process_args = [command] + (arguments or [])
        logger.debug("Plesk exec: %s", " ".join(process_args))

        def _execute(**kwargs):
            try:
                subprocess.check_call(**kwargs)
            except subprocess.CalledProcessError as e:
                raise PleskApiException(e)

        if stdout:
            fh, out_tmp = mkstemp()
            try:
                with os.fdopen(fh, 'r+') as fd_out:
                    _execute(args=process_args, stdout=fd_out)
                    fd_out.seek(0)
                    return fd_out.read()
            finally:
                os.unlink(out_tmp)
        else:
            _execute(args=process_args)


class PleskApiException(errors.PluginError):
    """Plesk API execution error"""


class DictToXml(object):  # pylint: disable=too-few-public-methods
    """Map dictionary into XML"""

    def __init__(self, structure):
        self.doc = Document()

        root_name = str(structure.keys()[0])
        root = self.doc.createElement(root_name)

        self.doc.appendChild(root)
        self._build(root, structure[root_name])

    def _build(self, parent, structure):
        if isinstance(structure, dict):
            for node_name in structure:
                tag = self.doc.createElement(node_name)
                parent.appendChild(tag)
                self._build(tag, structure[node_name])
        elif isinstance(structure, list):
            for node_structure in structure:
                self._build(parent, node_structure)
        elif structure is None:
            return
        else:
            node_data = str(structure)
            tag = self.doc.createTextNode(node_data)
            parent.appendChild(tag)

    def __str__(self):
        # TODO implement separate method for pretty print
        return self.doc.toxml()


class XmlToDict(dict):  # pylint: disable=too-few-public-methods
    """Map XML into dictionary"""

    def __init__(self, data, force_array=False):
        dom = parseString(data)
        root = dom.documentElement
        root_name = root.tagName
        self.force_array = force_array
        structure = {
            root_name: self._get_children(root)
        }
        super(XmlToDict, self).__init__(structure)

    def _get_children(self, node):
        children = {}
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                children = self._get_text_child(children, child)
            elif self.force_array:
                children = self._get_list_children(children, child)
            else:
                children = self._get_dict_children(children, child)
        return children

    @staticmethod
    def _get_text_child(children, child):
        data = child.data
        if 0 == len(data.strip()):
            return children
        elif isinstance(children, list):
            return children + [data]
        elif isinstance(children, dict):
            return data
        else:
            return [children, data]

    def _get_list_children(self, children, child):
        child_name = child.tagName
        if isinstance(children, dict) and len(children) > 0:
            children = [children]
        if isinstance(children, list):
            children += [{child_name: self._get_children(child)}]
        else:
            children[child_name] = self._get_children(child)
        return children

    def _get_dict_children(self, children, child):
        child_name = child.tagName
        if child_name in children:
            if not isinstance(children[child_name], list):
                children[child_name] = [children[child_name]]
            children[child_name].append(self._get_children(child))
        else:
            children[child_name] = self._get_children(child)
        return children
