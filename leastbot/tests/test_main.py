from types import FunctionType

from mock import call

from leastbot.main import main
from leastbot.tests.mockutil import MockingTestCase, ArgIsType


class mainTests (MockingTestCase):
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
