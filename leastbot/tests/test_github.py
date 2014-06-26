import json

from twisted.trial import unittest
from mock import call

from leastbot.tests.mockutil import MockingTestCase
from leastbot import github



class WebhookResourceTests (MockingTestCase):
    def setUp(self):
        MockingTestCase.setUp(self)

        self.f_secret = 'fake secret'
        self.m_handle_event = self.make_mock()
        self.m_request = self.make_mock()
        self.res = github.WebhookResource(self.f_secret, self.m_handle_event)

    def test_render_GET(self):
        self.res.render_GET(self.m_request)

        self.assert_calls_equal(
            self.m_handle_event,
            [])

        self.assert_calls_equal(
            self.m_request,
            [call.setResponseCode(403, 'FORBIDDEN'),
             call.finish()])

    def test_render_POST_ping(self):
        message = {
            u'hook': {
                u'active': True,
                u'config': {
                    u'content_type': u'json',
                    u'insecure_ssl': u'0',
                    u'secret': self.f_secret,
                    u'url': u'http://fake_hook_url/',
                    },
                u'created_at': u'2014-06-26T02:47:58Z',
                u'events': [u'*'],
                u'id': 2484169,
                u'last_response': {
                    u'code': None,
                    u'message': None,
                    u'status': u'unused',
                    },
                u'name': u'web',
                u'test_url': u'https://api.github.com/repos/:FAKE_GH_ACCT:/:FAKE_REPO:/hooks/2484169/test',
                u'updated_at': u'2014-06-26T02:47:58Z',
                u'url': u'https://api.github.com/repos/:FAKE_GH_ACCT:/:FAKE_REPO:/hooks/2484169',
                },
            u'hook_id': 2484169,
            u'zen': u'Keep it logically awesome.',
            }

        body = json.dumps(message)
        sigver = github.SignatureVerifier(self.f_secret)
        expsig = sigver._calculate_hmacsha1(body)

        self.m_request.requestHeaders = {
            'X-Github-Event': 'ping',
            'X-Github-Delivery': 'a fake unique id',
            'X-Hub-Signature': 'sha1-' + expsig,
            }

        self.res.render_POST(self.m_request)

        self.assert_calls_equal(
            self.m_request,
            [call.setResponseCode(200, 'OK'),
             call.finish()])

        self.assert_calls_equal(
            self.m_handle_event,
            [('ping', message)])


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


