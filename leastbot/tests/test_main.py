import sys
from types import FunctionType

from mock import call, sentinel

from leastbot.main import main, init_logging, parse_args, LogFormat, DateFormat
from leastbot.tests.mockutil import MockingTestCase, ArgIsType


class LoggingPatcherTestCase (MockingTestCase):
    def setUp(self):
        MockingTestCase.setUp(self)

        self.m_basicConfig = self.patch('logging.basicConfig')
        self.m_PythonLoggingObserver = self.patch('twisted.python.log.PythonLoggingObserver')


class main_Tests (LoggingPatcherTestCase):
    def test_main_no_args(self):
        m_reactor = self.make_mock()
        m_Client = self.patch('leastbot.irc.Client')
        m_WebServer = self.patch('leastbot.webserver.WebServer')

        main(args=[], reactor=m_reactor)

        websecret = 'abc'
        webport = 8080
        irchost = 'irc.oftc.org'
        ircport = 6697
        nick = 'leastbot'
        password = '012345'
        nickserv = 'nickserv'
        channel = '#leastbot-test'


        self.assert_calls_equal(
            m_WebServer,
            [call(m_reactor, websecret, ArgIsType(FunctionType)),
             call().listen(webport)])

        self.assert_calls_equal(
            m_Client,
            [call(m_reactor, irchost, ircport, nick, password, nickserv, channel),
             call().connect()])

        self.assert_calls_equal(
            m_reactor,
            [call.run()])


class parse_args_Tests (LoggingPatcherTestCase):
    def setUp(self):
        LoggingPatcherTestCase.setUp(self)

        self.m_stdout = self.patch('sys.stdout')
        self.m_stderr = self.patch('sys.stderr')

    def assertNoOutputOrLogInit(self):
        self.assert_calls_equal(self.m_stdout, [])
        self.assert_calls_equal(self.m_stderr, [])
        self.assert_calls_equal(self.m_basicConfig, [])
        self.assert_calls_equal(self.m_PythonLoggingObserver, [])

    def test_help(self):
        self.assertRaises(SystemExit, parse_args, ['--help'])

        self.assert_calls_equal(self.m_stdout, [call.write(ArgIsType(str))])
        self.assert_calls_equal(self.m_stderr, [])
        self.assert_calls_equal(self.m_basicConfig, [])
        self.assert_calls_equal(self.m_PythonLoggingObserver, [])

    def test_no_args(self):
        parse_args([])
        self.assertNoOutputOrLogInit()

    def test_log_level(self):
        parse_args(['--log-level', 'DEBUG'])
        self.assertNoOutputOrLogInit()


class init_logging_Tests (LoggingPatcherTestCase):
    def test_init_logging(self):
        init_logging(sentinel.A_LOG_LEVEL)

        self.assert_calls_equal(
            self.m_basicConfig,
            [call(stream=sys.stdout,
                  format=LogFormat,
                  datefmt=DateFormat,
                  level=sentinel.A_LOG_LEVEL)])
