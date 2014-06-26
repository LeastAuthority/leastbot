import sys
import logging
from types import FunctionType

from mock import call

from leastbot.main import main, parse_args, LogFormat, DateFormat
from leastbot.tests.mockutil import MockingTestCase, ArgIsType


class main_Tests (MockingTestCase):
    def test_main_twisted_setup(self):
        m_reactor = self.make_mock()
        m_WebServer = self.patch('leastbot.webserver.WebServer')

        main(args=[], reactor=m_reactor)

        expectedsecret = 'Not a very good secret.'
        expectedport = 8080

        self.assert_calls_equal(
            m_WebServer,
            [call(m_reactor, expectedsecret, ArgIsType(FunctionType)),
             call().listen(expectedport)])

        self.assert_calls_equal(
            m_reactor,
            [call.run()])


class parse_args_Tests (MockingTestCase):
    def test_help(self):
        self.assertRaises(SystemExit, parse_args, ['--help'])

    def test_no_args(self):
        m_basicConfig = self.patch('logging.basicConfig')

        parse_args([])

        self.assert_calls_equal(
            m_basicConfig,
            [call(stream=sys.stdout, format=LogFormat, datefmt=DateFormat, level=logging.INFO)])

    def test_log_level(self):
        m_basicConfig = self.patch('logging.basicConfig')

        parse_args(['--log-level', 'DEBUG'])

        self.assert_calls_equal(
            m_basicConfig,
            [call(stream=sys.stdout, format=LogFormat, datefmt=DateFormat, level=logging.DEBUG)])
