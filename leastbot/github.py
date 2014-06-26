import hmac
import hashlib


class SignatureVerifier (object):
    def __init__(self, sharedsecret):
        self._sharedsecret = sharedsecret

    def _calculate_hmacsha1(self, body):
        m = hmac.HMAC(key=self._sharedsecret, msg=body, digestmod=hashlib.sha1)
        return m.hexdigest()
