import json

from twisted.trial import unittest
from twisted.web.server import NOT_DONE_YET
from mock import call

from leastbot.tests.logutil import LogMockingTestCase, ArgIsLogRecord
from leastbot import github



class WebhookResourceTests (LogMockingTestCase):
    secret = 'fake secret'

    pingmessage = {
        u'hook': {
            u'active': True,
            u'config': {
                u'content_type': u'json',
                u'insecure_ssl': u'0',
                u'secret': secret,
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

    def setUp(self):
        LogMockingTestCase.setUp(self)

        self.pingbody = json.dumps(self.pingmessage)
        sigver = github.SignatureVerifier(self.secret)
        self.pingexpsig = sigver._calculate_hmacsha1(self.pingbody)

        self.m_handle_event = self.make_mock()
        self.m_request = self.make_mock()
        self.m_request.content.getvalue.return_value = self.pingbody

        headers = {
            'X-Github-Event': 'ping',
            'X-Github-Delivery': 'a fake unique id',
            'X-Hub-Signature': 'sha1=' + self.pingexpsig,
            }
        self.m_request.getHeader.side_effect = headers.get

        self.res = github.WebhookResource(self.secret, self.m_handle_event)

    def test_isLeaf_resource(self):
        self.assertEqual(True, github.WebhookResource.isLeaf)

    def test_render_GET(self):
        r = self.res.render_GET(self.m_request)

        self.assertEqual(NOT_DONE_YET, r)
        self.assert_calls_equal(
            self.m_handle_event,
            [])

        self.assert_calls_equal(
            self.m_request,
            [call.setResponseCode(403, 'FORBIDDEN'),
             call.finish()])

    def test_render_POST_ping(self):
        r = self.res.render_POST(self.m_request)

        self.assertEqual(NOT_DONE_YET, r)
        self.assert_calls_equal(
            self.m_request,
            [call.getHeader('X-Hub-Signature'),
             call.content.getvalue(),
             call.getHeader('X-Github-Event'),
             call.getHeader('X-Github-Delivery'),
             call.setResponseCode(200, 'OK'),
             call.finish()])

        self.assert_calls_equal(
            self.m_handle_event,
            [call('a fake unique id', 'ping', self.pingmessage)])

        self.assert_calls_equal(
            self.m_loghandler,
            [])

    def test_render_POST_ping_tampered(self):
        tweakedmessage = self.pingmessage.copy()
        tweakedmessage['hook_id'] += 1

        self.m_request.content.getvalue.return_value = json.dumps(tweakedmessage)

        r = self.res.render_POST(self.m_request)

        self.assertEqual(NOT_DONE_YET, r)
        self.assert_calls_equal(
            self.m_request,
            [call.getHeader('X-Hub-Signature'),
             call.content.getvalue(),
             call.setResponseCode(403, 'FORBIDDEN'),
             call.finish()])

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(ArgIsLogRecord(levelname='WARNING'))])

class SignatureVerifierTests (unittest.TestCase):
    def setUp(self):
        self.sigver = github.SignatureVerifier(
            sharedsecret=XHubSignatureTestVector.sharedsecret,
            )

    def test_vector_positive(self):
        self.failUnless(
            self.sigver(
                allegedsig=XHubSignatureTestVector.expectedsig,
                message=XHubSignatureTestVector.body,
                ),
            )

    def test_vector_negative_tampered_sig(self):
        self.failIf(
            self.sigver(
                allegedsig=XHubSignatureTestVector.expectedsig[:-1] + '8',
                message=XHubSignatureTestVector.body,
                ),
            )

    def test_vector_negative_tampered_body(self):
        self.failIf(
            self.sigver(
                allegedsig=XHubSignatureTestVector.expectedsig,
                message=XHubSignatureTestVector.body + ' ',
                ),
            )

    def test_hmac_vector(self):
        # Note: We verify this private method because we want to bypass
        # the time-invariant comparison layer (and we don't want to
        # mock here):
        sig = 'sha1=' + self.sigver._calculate_hmacsha1(XHubSignatureTestVector.body)
        self.assertEqual(XHubSignatureTestVector.expectedsig, sig)


# I did not find test vectors for the X-HUB-SIGNATURE algorithm, so I
# made this one by hand:
class XHubSignatureTestVector (object):
    # This is just a "namespace class", not to be instantiated.

    sharedsecret='abc'

    body='{"zen":"Keep it logically awesome.","hook":{"url":"https://api.github.com/repos/nejucomo/leastbot/hooks/2483695","test_url":"https://api.github.com/repos/nejucomo/leastbot/hooks/2483695/test","id":2483695,"name":"web","active":true,"events":["*"],"config":{"secret":"abc","url":"http://con.struc.tv:12388/foo","content_type":"json","insecure_ssl":"0"},"last_response":{"code":null,"status":"unused","message":null},"updated_at":"2014-06-26T00:34:21Z","created_at":"2014-06-26T00:34:21Z"},"hook_id":2483695}'

    expectedsig='sha1=91bc104310ed46d5633a249e0240dd98a37435cf'



class EventFormatterTests (unittest.TestCase):
    Vectors = [
        dict(
            id = 42,
            name = '! MAGICAL TEST EVENT !',
            info = {'fruit': 'banana', 'meat': 'mutton'},
            expectedlines = [
                "No formatter for github event type '! MAGICAL TEST EVENT !' with id 42.",
                ],
            ),
        dict( # A push with the expected parameters:
            id = 'abcd-1234-ef09-cafe',
            name = 'push',
            info = {
                u'repository': {u'url': u'https://github.com/fakeuser/leastbot'},
                u'pusher': {u'email': u'fakeuser@example.com'},
                u'compare': u'https://github.com/fakeuser/leastbot/compare/74cdf0cb7cd8...0343bc046082',
                u'ref': u'refs/heads/master',
                u'commits': [None] * 12, # Note - only the length is used.
                },
            expectedlines = [
                "'fakeuser@example.com' pushed 12 commits to 'refs/heads/master' of 'https://github.com/fakeuser/leastbot'",
                "Push diff: https://github.com/fakeuser/leastbot/compare/74cdf0cb7cd8...0343bc046082",
                ],
            ),
        dict( # A push with some missing parameters:
            id = 'abcd-1234-ef09-cafe',
            name = 'push',
            info = {
                u'repository': {u'info': 'Whee!'},
                # u'pusher' is missing.
                u'compare': u'https://github.com/fakeuser/leastbot/compare/74cdf0cb7cd8...0343bc046082',
                u'ref': u'refs/heads/master',
                # u'commits' is misisng.
                },
            expectedlines = [
                "<Missing pusher> pushed 4294967295 commits to 'refs/heads/master' of <Missing repository/url>",
                "Push diff: https://github.com/fakeuser/leastbot/compare/74cdf0cb7cd8...0343bc046082",
                ],
            ),
        dict(
            id = 'abcd-1234-ef09-cafe',
            name = 'issues',
            info = {
                u'sender': {u'login': u'exampleuser'},
                u'action': u'opened',
                u'issue': {
                    u'title': u'An example issue title.',
                    u'number': 42,
                    u'html_url': u'https://github.com/fakeuser/leastbot/issues/42',
                    },
                },
            expectedlines = [
                "'exampleuser' opened issue 42: 'An example issue title.'",
                "Issue: https://github.com/fakeuser/leastbot/issues/42",
                ],
            ),
        dict( # Updating a short comment:
            id = 'abcd-1234-ef09-cafe',
            name = 'issue_comment',
            info = {
                u'sender': {u'login': u'exampleuser'},
                u'action': u'created',
                u'issue': { u'number': 42 },
                u'comment': {
                    u'body': 'A very short comment.',
                    u'id': 97,
                    u'html_url': u'https://github.com/fakeuser/leastbot/issues/42#issuecomment-97',
                    },
                },
            expectedlines = [
                "'exampleuser' created issue 42 comment 97: 'A very short comment.'",
                "Comment: https://github.com/fakeuser/leastbot/issues/42#issuecomment-97",
                ],
            ),
        dict( # Updating a long comment:
            id = 'abcd-1234-ef09-cafe',
            name = 'issue_comment',
            info = {
                u'sender': {u'login': u'exampleuser'},
                u'action': u'created',
                u'issue': { u'number': 42 },
                u'comment': {
                    u'body': """

This is a very long comment, with lots of whitespace.  Additionally the first line is longer than 120 characters, which will be the cutoff enforced by formatting.

  Also, it uses crazy markup like:

    user!foo.example@blah

 And ugly whitespace which should not bork irc clients:
\r\n

# TODO: read up on irc protocol and put scary stuff here.
""",
                    u'id': 97,
                    u'html_url': u'https://github.com/fakeuser/leastbot/issues/42#issuecomment-97',
                    },
                },
            expectedlines = [
                u"'exampleuser' created issue 42 comment 97: 'This is a very long comment, with lots of whitespace.  Additionally the first line is longer than 120 characters, which '\u2026 (truncated)".encode('utf8'),
                'Comment: https://github.com/fakeuser/leastbot/issues/42#issuecomment-97',
                ],
            ),
        ]

    def test_all_vectors(self):
        for evspec in self.Vectors:
            evid = evspec['id']
            evtype = evspec['name']
            evinfo = evspec['info']
            expectedformat = '\n'.join(evspec['expectedlines'])

            result = github.format_event(evid, evtype, evinfo)

            self.assertEqual(result, expectedformat)
