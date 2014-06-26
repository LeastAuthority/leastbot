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

    def _calculate_hmacsha1(self, body):
        m = hmac.HMAC(key=self._sharedsecret, msg=body, digestmod=hashlib.sha1)
        return m.hexdigest()
