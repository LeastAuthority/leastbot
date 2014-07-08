from twisted.trial import unittest

from leastbot.formatutil import dedent


class dedentTests (unittest.TestCase):
    def test_dedent_basic(self):
        self.assertEqual(
            'foo\nbar\n',
            dedent('''
                foo
                bar
            '''))

    def test_dedent_malformed(self):
        self.assertRaises(
            AssertionError,
            dedent,
            '''
                foo
              The first non-empty line defines the minimum indent.
            ''')


