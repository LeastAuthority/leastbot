from twisted.internet import ssl
from twisted.trial import unittest

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
                    ArgIsType(irc.ClientProtocolFactory),
                    ArgIsType(ssl.ClientContextFactory))])

        def check_record_arg(rec):
            """<Record.msg.find('Connecting') != -1>"""
            return rec.msg.find('Connecting') != -1

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(EqCallback(check_record_arg))])


class ClientProtocolFactoryTests (LogMockingTestCase):
    def test_protocol_is_irc_ClientProtocol(self):
        self.assertIs(irc.ClientProtocol, irc.ClientProtocolFactory.protocol)

    def test_buildProtocl_resets_backoff_counter(self):
        nick = 'leastbot'
        password = 'blah'
        channel = '#foo'
        m_reactor = self.make_mock()

        f = irc.ClientProtocolFactory(m_reactor, nick, password, channel)

        # Violate the interface abstraction to verify backoff behavior:
        m_delaytracker = self.make_mock()
        f._delaytracker = m_delaytracker # Overwrite the extant one.

        f.buildProtocol()

        self.assert_calls_equal(m_delaytracker, [call.reset()])

    def test_clientConnectionLost_reconnects_with_backoff(self):
        self._check_reconnects_with_backoff('clientConnectionLost')

    def test_clientConnectionFailed_reconnects_with_backoff(self):
        self._check_reconnects_with_backoff('clientConnectionFailed')

    def _check_reconnects_with_backoff(self, methodname):
        nick = 'leastbot'
        password = 'blah'
        channel = '#foo'
        m_reactor = self.make_mock()

        f = irc.ClientProtocolFactory(m_reactor, nick, password, channel)

        # Violate the interface abstraction to verify backoff behavior:
        m_delaytracker = self.make_mock()
        f._delaytracker = m_delaytracker # Overwrite the extant one.

        m_connector = self.make_mock()
        m_reason = self.make_mock()

        method = getattr(f, methodname)
        ret = method(m_connector, m_reason)

        self.assertIsNone(ret)

        self.assert_calls_equal(
            m_delaytracker,
            [call.increment()])

        def check_record_arg(rec):
            """<Record.msg.find('Reconnecting in') != -1>"""
            return rec.msg.find('Reconnecting in') != -1

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(EqCallback(check_record_arg))])

        self.assert_calls_equal(
            m_reactor,
            [call.callLater(m_delaytracker.increment.return_value, m_connector.connect)])


class BackoffDelayTrackerTests (unittest.TestCase):
    def test_backoff_delay(self):
        bdt = irc.BackoffDelayTracker()

        delay = bdt.increment()

        # There's 0 delay initially:
        self.assertEqual(0, delay)

        # The delay continues to increase on failure (for at least 20 cycles):
        for i in range(20):
            nextdelay = bdt.increment()
            self.assertGreater(nextdelay, delay)
            delay = nextdelay

        bdt.reset()

        # After a reset the delay drops back to 0:
        self.assertEqual(0, bdt.increment())


