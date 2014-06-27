from twisted.internet import ssl

from mock import call

from leastbot.tests.logutil import LogMockingTestCase
from leastbot.tests.mockutil import ArgIsType, EqCallback
from leastbot import irc



class ClientTests (LogMockingTestCase):
    def setUp(self):
        LogMockingTestCase.setUp(self)

    def test_connect(self):
        host = 'irc.fakehost.net'
        port = 6697
        nick = 'leastbot'
        password = 'blah'
        channel = '#foo'
        m_reactor = self.make_mock()

        client = irc.Client(m_reactor, host, port, nick, password, channel)

        self.assert_calls_equal(
            m_reactor,
            [])

        client.connect()

        self.assert_calls_equal(
            m_reactor,
            [call.connectSSL(
                    host,
                    port,
                    ArgIsType(irc.ClientFactory),
                    ArgIsType(ssl.ClientContextFactory))])

        def check_record_arg(rec):
            """<Record.msg.find('Connecting') != -1>"""
            return rec.msg.find('Connecting') != -1

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(EqCallback(check_record_arg))])
