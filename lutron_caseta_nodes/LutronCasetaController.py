import polyinterface

import json
import re
import requests
import socket
import ssl

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from urllib.parse import urlencode
from lutron_caseta_nodes import LutronCasetaSmartBridge


LOGGER = polyinterface.LOGGER

LOGIN_SERVER = "device-login.lutron.com"
APP_CLIENT_ID = ("e001a4471eb6152b7b3f35e549905fd8589dfcf57eb680b6fb37f20878c"
                 "28e5a")
APP_CLIENT_SECRET = ("b07fee362538d6df3b129dc3026a72d27e1005a3d1e5839eed5ed18"
                     "c63a89b27")
APP_OAUTH_REDIRECT_PAGE = "lutron_app_oauth_redirect"
CERT_SUBJECT = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Pennsylvania"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Coopersburg"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME,
                       "Lutron Electronics Co., Inc."),
    x509.NameAttribute(NameOID.COMMON_NAME, "Lutron Caseta App")
])

BASE_URL = "https://%s/" % LOGIN_SERVER
REDIRECT_URI = "https://%s/%s" % (LOGIN_SERVER, APP_OAUTH_REDIRECT_PAGE)

AUTHORIZE_URL = ("%soauth/authorize?%s" % (BASE_URL,
                                           urlencode({
                                               "client_id": APP_CLIENT_ID,
                                               "redirect_uri": REDIRECT_URI,
                                               "response_type": "code"
                                           })))



class LutronCasetaController(polyinterface.Controller):
    def __init__(self, polyglot):
        self.check_params()
        self.private_key = self.get_priv_key()
        self.certificate = self.get_certificate()

        super().__init__(polyglot)

    def get_priv_key(self):
        try:
            with open('caseta.key', 'rb') as f:
                private_key = load_pem_private_key(f.read(), None, default_backend())
        except FileNotFoundError:
            private_key = rsa.generate_private_key(public_exponent=65537,
                                                        key_size=2048,
                                                        backend=default_backend())
            with open('caseta.key', 'wb') as f:
                f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        return private_key

    def get_cert(self):
        try:
            with open('caseta.crt', 'rb') as f:
            certificate = x509.load_pem_x509_certificate(f.read(),
                                                         default_backend())
        except FileNotFoundError:
            csr = (x509.CertificateSigningRequestBuilder()
                   .subject_name(CERT_SUBJECT)
                   .sign(private_key, hashes.SHA256(), default_backend()))

            if not self.oauth_code:
                return None

            token = requests.post("%soauth/token" % BASE_URL, data={
                "code": oauth_code,
                "client_id": APP_CLIENT_ID,
                "client_secret": APP_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code"}).json()

            if token["token_type"] != "bearer":
                raise ("Received invalid token %s. Try generating a new code "
                       "(one time use).") % token

            access_token = token["access_token"]

            pairing_request_content = {
                "remote_signs_app_certificate_signing_request":
                csr.public_bytes(serialization.Encoding.PEM).decode('ASCII')
            }

            pairing_response = requests.post(
                "%sapi/v1/remotepairing/application/user" % BASE_URL,
                json=pairing_request_content,
                headers={
                    "X-DeviceType": "Caseta,RA2Select",
                    "Authorization": "Bearer %s" % access_token
                }
            ).json()

            app_cert = pairing_response["remote_signs_app_certificate"]
            remote_cert = pairing_response["local_signs_remote_certificate"]

            with open('caseta.crt', 'wb') as f:
                f.write(app_cert.encode('ASCII'))
                f.write(remote_cert.encode('ASCII'))

            # TODO Don't open new filehandle to read cert back
            with open('caseta.crt', 'rb') as f:
            certificate = x509.load_pem_x509_certificate(f.read(),
                                                         default_backend())

        return certificate

    def start(self):
        LOGGER.info('Started LutronCaseta NodeServer')
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_socket = ssl.wrap_socket(raw_socket, keyfile='caseta.key',
                                     certfile='caseta.crt',
                                     ssl_version=ssl.PROTOCOL_TLSv1_2)
        ssl_socket.connect((self.luron_bridge_ip, 8081))

        ca_der = ssl_socket.getpeercert(True)
        ca_cert = x509.load_der_x509_certificate(ca_der, default_backend())
        with open('caseta-bridge.crt', 'wb') as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

        ssl_socket.send(("%s\r\n" % json.dumps({
            "CommuniqueType": "ReadRequest",
            "Header": {"Url": "/server/1/status/ping"}
        })).encode('UTF-8'))

        while True:
            buffer = b''
            while not buffer.endswith(b'\r\n'):
                buffer += ssl_socket.read()

            leap_response = json.loads(buffer.decode('UTF-8'))
            if leap_response['CommuniqueType'] == 'ReadResponse':
                break

        ssl_socket.close()
        LOGGER.info("Successfully connected to bridge, running LEAP Server version %s" %
                    leap_response['Body']['PingResponse']['LEAPVersion']



    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def query(self):
        """
        Optional.
        By default a query to the control node reports the FULL driver set for ALL
        nodes back to ISY. If you override this method you will need to Super or
        issue a reportDrivers() to each node manually.
        """
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def delete(self):
        """
        Example
        This is sent by Polyglot upon deletion of the NodeServer. If the process is
        co-resident and controlled by Polyglot, it will be terminiated within 5 seconds
        of receiving this message.
        """
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter config={}".format(config));
        LOGGER.info("process_config: Exit");

    def check_params(self):
        default_luron_bridge_ip = "192.168.1.100"
        if 'luron_bridge_ip' in self.polyConfig['customParams']:
            self.luron_bridge_ip = self.polyConfig['customParams']['luron_bridge_ip']
        else:
            self.luron_bridge_ip = default_luron_bridge_ip
            LOGGER.error('check_params: luron_bridge_ip not defined in customParams, please add it.  Using {}'.format(self.luron_bridge_ip))
            st = False

        self.oauth_code = self.polyConfig.get('customParams',{}).get('oauth_code')

        if not oauth_code:
            LOGGER.error("check_params: oauth_code not defined in customParams. Open Browser and login at %s" % AUTHORIZE_URL)
            st = False

        # Make sure they are in the params
        self.addCustomParam({'lutron_bridge_ip': self.lutron_bridge_ip, 'oauth_code': self.oauth_code})

        if not st:
            self.addNotice('Please set proper user and password in configuration page, and restart this nodeserver')

        # This one passes a key to test the new way.
        self.addNotice('This is a test','test')

    def remove_notice_test(self,command):
        LOGGER.info('remove_notice_test: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNotice('test')

    def remove_notices_all(self,command):
        LOGGER.info('remove_notices_all: notices={}'.format(self.poly.config['notices']))
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self,command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    id = 'LutronCasetaController'

    # TODO setup commands and drivers
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all,
        'REMOVE_NOTICE_TEST': remove_notice_test
    }
    drivers = []
