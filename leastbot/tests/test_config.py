import errno
from cStringIO import StringIO

from leastbot.tests.logutil import LogMockingTestCase
from leastbot import config



class ConfigTests (LogMockingTestCase):
    def setUp(self):
        LogMockingTestCase.setUp(self)

        self.m_configdir = self.make_mock()
        self.m_secretpath = self.make_mock()
        self.m_publicpath = self.make_mock()

        self.m_configdir.child.side_effect = {
            'secret.conf': self.m_secretpath,
            'public.conf': self.m_publicpath,
            }.__getitem__

    def _load(self):
        return config.load(self.m_configdir)

    def _assert_load_SystemExit_has(self, s):
        try:
            self._load()
        except SystemExit, e:
            if e.args[0].find(s) == -1:
                self.fail('An example config not given: %r' % (e.args,))

    def test_load_missing_secret_file_raises_SystemExit(self):
        self.m_secretpath.open.side_effect = IOError_ENOENT

        self._assert_load_SystemExit_has(config.ExampleSecretConfig)

    def test_load_missing_public_file_raises_SystemExit(self):
        self.m_secretpath.open.return_value = StringIO(config.ExampleSecretConfig)
        self.m_publicpath.open.side_effect = IOError_ENOENT

        self._assert_load_SystemExit_has(config.ExamplePublicConfig)

    def test_load_config_successfully(self):
        self.m_secretpath.open.return_value = StringIO(config.ExampleSecretConfig)
        self.m_publicpath.open.return_value = StringIO(config.ExamplePublicConfig)

        c = self._load()

        self.assertEqual(c.secret.irc.password, 'fake-irc-password')
        self.assertEqual(c.secret.web.githubsecret, 'fake-github-secret')
        self.assertEqual(c.public.irc.host, 'irc.example.com')
        self.assertEqual(c.public.irc.port, 6667)
        self.assertEqual(c.public.irc.nick, 'leastbot')
        self.assertEqual(c.public.irc.nickserv, 'nickserv')
        self.assertEqual(c.public.irc.channel, '#leastbot-test')
        self.assertEqual(c.public.web.port, 8080)


IOError_ENOENT = IOError()
IOError_ENOENT.errno = errno.ENOENT

