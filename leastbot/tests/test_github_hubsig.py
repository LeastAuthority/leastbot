import unittest

from leastbot.github.hubsig import SignatureVerifier


class SignatureVerifierTests (unittest.TestCase):

    def test_hmac_vector(self):
        sigver = SignatureVerifier(sharedsecret=XHubSignatureTestVector.sharedsecret)

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


