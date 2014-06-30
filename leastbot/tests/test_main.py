import os
import sys

from twisted.python.filepath import FilePath

from mock import call, sentinel

from leastbot.main import main, init_logging, parse_args, LogFormat, DateFormat
from leastbot.tests.logutil import LogMockingTestCase
from leastbot.tests.mockutil import ArgIsTypeWithAttrs


class LogInitializationTestCase (LogMockingTestCase):
    def setUp(self):
        LogMockingTestCase.setUp(self)

        self.m_basicConfig = self.patch('logging.basicConfig')
        self.m_PythonLoggingObserver = self.patch('twisted.python.log.PythonLoggingObserver')
        self.m_stdout = self.patch('sys.stdout')
        self.m_stderr = self.patch('sys.stderr')


class main_Tests (LogInitializationTestCase):
    def setUp(self):
        LogInitializationTestCase.setUp(self)

        self.m_reactor = self.make_mock()
        self.m_config_load = self.patch('leastbot.config.load')
        self.m_Client = self.patch('leastbot.irc.Client')
        self.m_WebServer = self.patch('leastbot.webserver.WebServer')

    def test_main_no_args(self):
        websecret = 'abc'
        webport = 8080
        irchost = 'irc.oftc.net'
        ircport = 6697
        nick = 'leastbot'
        password = '012345'
        nickserv = 'nickserv'
        channel = '#leastbot-test'

        m_config = self.m_config_load.return_value
        m_config.secret.irc.password = password
        m_config.secret.web.githubsecret = websecret
        m_config.public.irc.host = irchost
        m_config.public.irc.port = ircport
        m_config.public.irc.nick = nick
        m_config.public.irc.nickserv = nickserv
        m_config.public.irc.channel = channel
        m_config.public.web.port = webport

        main(args=[], reactor=self.m_reactor)

        self.assert_calls_equal(
            self.m_config_load,
            [call(ArgIsTypeWithAttrs(FilePath, path=os.path.expanduser('~/.leastbot')))])

        self.assert_calls_equal(
            self.m_Client,
            [call(self.m_reactor, irchost, ircport, nick, password, nickserv, channel),
             call().connect()])

        self.assert_calls_equal(
            self.m_WebServer,
            [call(self.m_reactor, webport, websecret, self.m_Client.return_value.handle_github_notification),
             call().listen()])

        self.assert_calls_equal(
            self.m_reactor,
            [call.run()])

    def test_main_args_is_UsageError(self):
        self.assertRaises(SystemExit, main, args=['foo'], reactor=self.m_reactor)

        # Assert no I/O subsystems were touched:
        for m in [self.m_reactor, self.m_config_load, self.m_WebServer, self.m_Client]:
            self.assert_calls_equal(m, [])



class parse_args_Tests (LogInitializationTestCase):
    def _assert_no_log_init(self):
        self.assert_calls_equal(self.m_basicConfig, [])
        self.assert_calls_equal(self.m_PythonLoggingObserver, [])

    def _assert_no_output_or_log_init(self):
        self.assert_calls_equal(self.m_stdout, [])
        self.assert_calls_equal(self.m_stderr, [])

    def test_no_args(self):
        parse_args([])
        self._assert_no_output_or_log_init()

    def test_log_level(self):
        parse_args(['--log-level', 'DEBUG'])
        self._assert_no_output_or_log_init()

    def test_help(self):
        self.assertRaises(SystemExit, parse_args, ['--help'])
        self._assert_no_log_init()
        self.failUnless(self.m_stdout.write.called)
        self.failIf(self.m_stderr.write.called)

    def test_unexpected_args(self):
        self.assertRaises(SystemExit, parse_args, ['bananas!'])
        self._assert_no_log_init()
        self.failIf(self.m_stdout.write.called)
        self.failUnless(self.m_stderr.write.called)


class init_logging_Tests (LogInitializationTestCase):
    def test_init_logging(self):
        init_logging(sentinel.A_LOG_LEVEL)

        self.assert_calls_equal(
            self.m_basicConfig,
            [call(stream=sys.stdout,
                  format=LogFormat,
                  datefmt=DateFormat,
                  level=sentinel.A_LOG_LEVEL)])
