import errno
from cStringIO import StringIO

from leastbot.tests.logutil import LogMockingTestCase
from leastbot import config



class ConfigTests (LogMockingTestCase):
    def setUp(self):
        LogMockingTestCase.setUp(self)

        self.m_basedir = self.make_mock()
        self.m_secretpath = self.make_mock()
        self.m_publicpath = self.make_mock()

        self.m_configdir.child.side_effect = {
            'secret.conf': self.m_secretpath,
            'public.conf': self.m_publicpath,
            }

        self.c = config.Config(self.m_basedir)

    def _load(self):
        return config.Config.load(self.m_basedir)

    def test_load_missing_secret_file_raises_SystemExit(self):
        self.m_secretpath.open.side_effect = IOError_ENOENT

        self.assertRaises(SystemExit, self._load)

    def test_load_unconfigured_secret_file_raises_SystemExit(self):
        self.m_secretpath.open.return_value = StringIO(config.SecretConfigExample)

        self.assertRaises(SystemExit, self._load)

    def test_load_missing_public_file_raises_SystemExit(self):
        self.m_secretpath.open.return_value = StringIO(ValidSecretConfig)
        self.m_publicpath.open.side_effect = IOError_ENOENT

        self.assertRaises(SystemExit, self._load)

    def test_load_unconfigured_public_file_raises_SystemExit(self):
        self.m_secretpath.open.return_value = StringIO(ValidSecretConfig)
        self.m_publicpath.open.return_value = StringIO(config.PublicConfigExample)

        self.assertRaises(SystemExit, self._load)

    def test_load_config_successfully(self):
        self.m_secretpath.open.return_value = StringIO(ValidSecretConfig)
        self.m_publicpath.open.return_value = StringIO(ValidPublicConfig)

        c = self._load()

        self.assertEqual(c.secret.irc.password, 'fake-irc-password')
        self.assertEqual(c.secret.web.githubsecret, 'fake-github-secret')
        self.assertEqual(c.public.irc.host, 'irc.example.com')
        self.assertEqual(c.public.irc.port, 6667)
        self.assertEqual(c.public.irc.nick, 'leastbot')
        self.assertEqual(c.public.irc.nickserv, 'nickserv')
        self.assertEqual(c.public.web.port, 8080)


IOError_ENOENT = IOError()
IOError_ENOENT.errno = errno.ENOENT

ValidSecretConfig = """
[irc client]
password: fake-irc-password

[web server]
githubsecret: fake-github-secret
"""

ValidPublicConfig = """
[irc client]
host: irc.example.com
port: 6667
nick: leastbot
nickserv: nickserv

[web server]
port: 8080
"""
