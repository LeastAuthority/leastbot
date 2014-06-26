import hmac
import hashlib

from twisted.web import resource



class WebhookResource (resource.Resource):
    def __init__(self, handle_event):
        resource.Resource.__init__(self)
        self._handle_event = handle_event

    def render_GET(self, request):
        request.setResponseCode(403, 'FORBIDDEN')
        request.finish()


class SignatureVerifier (object):
    def __init__(self, sharedsecret):
        self._sharedsecret = sharedsecret

    def __call__(self, allegedsig, message):
        expectedsig = self._calculate_hmacsha1(message)
        return constant_time_compare(allegedsig, expectedsig)

    def _calculate_hmacsha1(self, body):
        m = hmac.HMAC(key=self._sharedsecret, msg=body, digestmod=hashlib.sha1)
        return m.hexdigest()


def constant_time_compare(a, b):
    # Use Nate Lawson's constant time compare:
    # http://rdist.root.org/2010/01/07/timing-independent-array-comparison/

    if len(a) != len(b):
        return False

    result = 0
    for (x, y) in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0
