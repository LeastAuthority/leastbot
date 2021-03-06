from twisted.trial import unittest

from leastbot.github.formatter import format_event



class EventFormatterTests (unittest.TestCase):
    Vectors = [
        # Unknown events:
        dict(
            id = 42,
            name = u'! MAGICAL TEST EVENT !',
            info = {
                u'sender': {u'login': u'exampleuser'},
                u'repository': {u'url': u'https://github.com/fakeuser/leastbot'},

                # Include some noise which should not affect announcement output:
                u'fruit': 'banana',
                'meat': 'mutton'
                },
            # Always log common fields of unknown events:
            expectedlines = [
                "github '! MAGICAL TEST EVENT !' event sent by 'exampleuser' in https://github.com/fakeuser/leastbot"
                ],
            ),

        dict( # An unknown event with missing common fields:
            id = 42,
            name = u'! MAGICAL TEST EVENT !',
            info = {
                u'repository': {u'url': u'https://github.com/fakeuser/leastbot'},

                # Include some noise which should not affect announcement output:
                u'fruit': 'banana',
                'meat': 'mutton'
                },
            # Always log common fields of unknown events:
            expectedlines = [
                "github '! MAGICAL TEST EVENT !' event sent by <Missing event.sender> in https://github.com/fakeuser/leastbot"
                ],
            ),

        # ping events:
        dict(
            id = 42,
            name = 'ping',
            info = {
                u'zen': u'If propaganda falls in an empty channel, does it make a mind control wave?'
                },
            expectedlines = [
                "Ping! 'If propaganda falls in an empty channel, does it make a mind control wave?'"
                ],
            ),

        # push events:
        dict( # A push with the expected parameters:
            id = 'abcd-1234-ef09-cafe',
            name = 'push',
            info = {
                u'repository': {u'url': u'https://github.com/fakeuser/leastbot'},
                u'pusher': {u'email': u'fakeuser@example.com', u'name': u'userA'},
                u'compare': u'https://github.com/fakeuser/leastbot/compare/74cdf0cb7cd8^...0343bc046082',
                u'ref': u'refs/heads/master',
                u'commits': [None] * 12, # Note - only the length is used.
                },
            expectedlines = [
                "'userA' pushed 12 commits to 'refs/heads/master' of https://github.com/fakeuser/leastbot",
                "Push diff: https://github.com/fakeuser/leastbot/compare/74cdf0cb7cd8%5E...0343bc046082",
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
                "<Missing event.pusher> pushed <Missing event.commits> commits to 'refs/heads/master' of <Missing event.repository.url>",
                "Push diff: https://github.com/fakeuser/leastbot/compare/74cdf0cb7cd8...0343bc046082",
                ],
            ),

        # issues events:
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

        # issue_comment events:
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

        # gollum
        dict(
            id = 'abcd-1234-ef09-cafe',
            name = 'gollum',
            info = {
                u'sender': {u'login': u'exampleuser'},
                u"pages": [
                    {
                        "title": "Home",
                        "action": "edited",
                        "html_url": "https://github.com/fakeuser/issues/wiki/Home"
                        },
                    ],
                },
            expectedlines = [
                u"'exampleuser' edited wiki pages: Home",
                'https://github.com/fakeuser/issues/wiki/Home',
                ],
            ),

        dict(
            id = 'abcd-1234-ef09-cafe',
            name = 'gollum',
            info = {
                u'sender': {u'login': u'exampleuser'},
                u"pages": [
                    {
                        "title": "Home",
                        "action": "edited",
                        "html_url": "https://github.com/fakeuser/issues/wiki/Home"
                        },
                    {
                        "title": "Bob's Page",
                        "action": "edited",
                        "html_url": "https://github.com/fakeuser/issues/wiki/Bob%27s%20Page",
                        },
                    ],
                },
            expectedlines = [
                u"'exampleuser' edited wiki pages: Home, Bob's Page",
                u'https://github.com/fakeuser/issues/wiki/Home',
                u'https://github.com/fakeuser/issues/wiki/Bob%27s%20Page',
                ],
            ),

        ]

    def test_all_vectors(self):
        for evspec in self.Vectors:
            evid = evspec['id']
            evtype = evspec['name']
            evinfo = evspec['info']
            expected = evspec['expectedlines']

            result = format_event(evid, evtype, evinfo)

            expectedformat = '\n'.join(expected) + '\n'
            self.assertEqual(result, expectedformat)
