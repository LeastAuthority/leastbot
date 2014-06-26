from twisted.trial import unittest
from mock import call

from leastbot.tests.mockutil import MockingTestCase
from leastbot import github



class WebhookResourceTests (MockingTestCase):
    def test_render_GET(self):
        m_handle_event = self.make_mock()
        m_request = self.make_mock()

        res = github.WebhookResource(m_handle_event)
        res.render_GET(m_request)

        self.assert_calls_equal(
            m_handle_event,
            [])

        self.assert_calls_equal(
            m_request,
            [call.setResponseCode(403, 'FORBIDDEN'),
             call.finish()])




class SignatureVerifierTests (unittest.TestCase):
    def test_hmac_vector(self):
        sigver = github.SignatureVerifier(sharedsecret=XHubSignatureTestVector.sharedsecret)

        # Note: We verify this private method because we want to bypass
        # the time-invariant comparison layer (and we don't want to
        # mock here):
        sig = sigver._calculate_hmacsha1(XHubSignatureTestVector.body)
        self.assertEqual(XHubSignatureTestVector.expectedsig, sig)


# I did not find test vectors for the X-HUB-SIGNATURE algorithm, so I
# made this one by hand:
class XHubSignatureTestVector (object):
    # This is just a "namespace class", not to be instantiated.

    sharedsecret='abc'

    body='{"zen":"Keep it logically awesome.","hook":{"url":"https://api.github.com/repos/nejucomo/leastbot/hooks/2483695","test_url":"https://api.github.com/repos/nejucomo/leastbot/hooks/2483695/test","id":2483695,"name":"web","active":true,"events":["*"],"config":{"secret":"abc","url":"http://con.struc.tv:12388/foo","content_type":"json","insecure_ssl":"0"},"last_response":{"code":null,"status":"unused","message":null},"updated_at":"2014-06-26T00:34:21Z","created_at":"2014-06-26T00:34:21Z"},"hook_id":2483695}'

    expectedsig='91bc104310ed46d5633a249e0240dd98a37435cf'


