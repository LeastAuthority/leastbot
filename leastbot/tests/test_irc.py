from twisted.internet import ssl
from twisted.trial import unittest

from mock import call

from leastbot.tests.logutil import LogMockingTestCase, ArgIsLogRecord
from leastbot.tests.mockutil import ArgIsType
from leastbot import irc



class ClientTests (LogMockingTestCase):
    def setUp(self):
        LogMockingTestCase.setUp(self)

    def test_connect(self):
        host = 'irc.fakehost.net'
        port = 6697
        nick = 'leastbot'
        password = 'blah'
        nickserv = 'ickservnay'
        channel = '#foo'
        m_reactor = self.make_mock()

        client = irc.Client(m_reactor, host, port, nick, password, nickserv, channel)

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

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(ArgIsLogRecord(msg='Connecting to %s:%d...'))])


class ClientProtocolTests (LogMockingTestCase):
    def setUp(self):
        LogMockingTestCase.setUp(self)

        self.nick = 'Nick'
        self.password = 'a password'
        self.nickserv = 'NickServ'
        self.channel = '#foo'

        self.p = irc.ClientProtocol(self.nick, self.password, self.nickserv, self.channel)

    def test_nickname_setattr(self):
        # The baseclass has an icky partially-mutation-based API.
        # Ensure we set .nickname:
        self.assertIs(self.p.nickname, self.nick)

    def test_handleCommand_debug_log(self):
        m_ircIRCClient = self.patch('twisted.words.protocols.irc.IRCClient')

        # Taken from a real world test run:
        command='NOTICE'
        prefix='weber.oftc.net'
        params=['AUTH', '*** Looking up your hostname...']

        self.p.handleCommand(command, prefix, params)

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(
                    ArgIsLogRecord(
                        levelname='DEBUG',
                        msg=r'handleCommand(command=%r, prefix=%r, params=%r)'))])

        # Ensure we delegate to the base library:
        self.assert_calls_equal(
            m_ircIRCClient,
            [call.handleCommand(self.p, command, prefix, params)])

    def test_msg_debug_log(self):
        m_ircIRCClient = self.patch('twisted.words.protocols.irc.IRCClient')

        to='bob'
        msg='I like bacon!'

        self.p.msg(to, msg)

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(
                    ArgIsLogRecord(
                        levelname='DEBUG',
                        msg=r'msg(user=%r, message=%r)'))])

        # Ensure we delegate to the base library:
        self.assert_calls_equal(
            m_ircIRCClient,
            [call.msg(self.p, to, msg)])


    def test_signedOn_triggers_nickserv_login(self):
        m_msg = self.patch('leastbot.irc.ClientProtocol.msg')

        self.p.signedOn()

        self.assert_calls_equal(
            m_msg,
            [call(self.nickserv, 'identify %s' % (self.password,))])

    def test_noticed_nickserv_login_success_triggers_channel_join(self):
        #  You are successfully identified as ${NICK}.
        user = '%s!services@services.oftc.net' % (self.nickserv,)
        m_join = self.patch('leastbot.irc.ClientProtocol.join')

        loginmsg = 'You are successfully identified as \x02%s\x02.' % (self.nick,)
        self.p.noticed(user, self.nick, loginmsg)

        self.assert_calls_equal(
            m_join,
            [call(self.channel)])


class ClientProtocolFactoryTests (LogMockingTestCase):
    def test_protocol_is_irc_ClientProtocol(self):
        self.assertIs(irc.ClientProtocol, irc.ClientProtocolFactory.protocol)

    def test_buildProtocol_resets_backoff_counter(self):
        nick = 'leastbot'
        password = 'blah'
        nickserv = 'the-nickserv-user'
        channel = '#foo'
        m_reactor = self.make_mock()

        f = irc.ClientProtocolFactory(m_reactor, nick, password, nickserv, channel)

        # Violate the interface abstraction to verify backoff behavior:
        m_delaytracker = self.make_mock()
        f._delaytracker = m_delaytracker # Overwrite the extant one.

        m_addr = self.make_mock()

        f.buildProtocol(m_addr)

        self.assert_calls_equal(m_delaytracker, [call.reset()])

    def test_clientConnectionLost_reconnects_with_backoff(self):
        self._check_reconnects_with_backoff('clientConnectionLost')

    def test_clientConnectionFailed_reconnects_with_backoff(self):
        self._check_reconnects_with_backoff('clientConnectionFailed')

    def _check_reconnects_with_backoff(self, methodname):
        nick = 'leastbot'
        password = 'blah'
        nickserv = 'the-nickserv-user'
        channel = '#foo'
        m_reactor = self.make_mock()

        f = irc.ClientProtocolFactory(m_reactor, nick, password, nickserv, channel)

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
            [call.handle(ArgIsLogRecord(msg='Connection %s: %r (Reconnecting in %.2f seconds.)'))])

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


