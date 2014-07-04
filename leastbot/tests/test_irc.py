from twisted.internet import ssl
from twisted.trial import unittest

from mock import call

from leastbot.tests.logutil import LogMockingTestCase, ArgIsLogRecord
from leastbot.tests.mockutil import ArgIsType
from leastbot import irc



class ClientTests (LogMockingTestCase):
    def setUp(self):
        LogMockingTestCase.setUp(self)

        self.host = 'irc.fakehost.net'
        self.port = 6697
        nick = 'leastbot'
        password = 'blah'
        nickserv = 'ickservnay'
        channel = '#foo'
        self.m_reactor = self.make_mock()

        self.client = irc.Client(self.m_reactor, self.host, self.port, nick, password, nickserv, channel)

    def test_init_does_no_io(self):
        self.assert_calls_equal(
            self.m_reactor,
            [])

    def test_connect(self):
        self.client.connect()

        self.assert_calls_equal(
            self.m_reactor,
            [call.connectSSL(
                    self.host,
                    self.port,
                    ArgIsType(irc.ClientProtocolFactory),
                    ArgIsType(ssl.ClientContextFactory))])

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(ArgIsLogRecord(msg='Connecting to %s:%d...'))])

    def test_github_notification_delegation(self):
        m_factory = self.make_mock()

        # Poke behind the curtain:
        self.client._factory = m_factory

        eventid = 42
        eventname = 'blah-event'
        eventdict = {'fruit': 'apple', 'meat': 'pork'}

        self.client.handle_github_notification(eventid, eventname, eventdict)

        self.assert_calls_equal(
            m_factory,
            [call.handle_github_notification(eventid, eventname, eventdict)])


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

    def _test_msg_debug_log(self, *args):
        m_ircIRCClient = self.patch('twisted.words.protocols.irc.IRCClient')

        self.p.msg(*args)

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(
                    ArgIsLogRecord(
                        levelname='DEBUG',
                        msg=r'msg(user=%r, message=%r, length=%r)'))])

        expectedargs = args
        if len(expectedargs) == 2:
            expectedargs += (None,)

        # Ensure we delegate to the base library:
        self.assert_calls_equal(
            m_ircIRCClient,
            [call.msg(self.p, *expectedargs)])

    def test_msg_debug_log_no_length(self):
        self._test_msg_debug_log('bob', 'Hello, friend!')

    def test_msg_debug_log_with_None_length(self):
        self._test_msg_debug_log('bob', 'Hello, friend!', None)

    def test_msg_debug_log_with_length(self):
        self._test_msg_debug_log('bob', 'Hello, friend!', 42)

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

    def test_github_notification_triggers_say_with_github_formatting(self):
        m_say = self.patch('leastbot.irc.ClientProtocol.say')
        m_format_event = self.patch('leastbot.github.format_event')

        eventid = 42,
        eventtype = 'blah-event'
        eventinfo = {'fruit': 'apple', 'meat': 'pork'}

        self.p.handle_github_notification(eventid, eventtype, eventinfo)

        self.assert_calls_equal(
            m_format_event,
            [call(eventid, eventtype, eventinfo)])

        self.assert_calls_equal(
            m_say,
            [call(self.channel, m_format_event.return_value)])

    def test_github_notification_handles_swallowed_events(self):
        repetitions = 3

        m_say = self.patch('leastbot.irc.ClientProtocol.say')
        m_format_event = self.patch('leastbot.github.format_event')
        m_format_event.side_effect = [None] * repetitions # Indicates an unhandled event.

        eventid = 42,
        eventtype = 'blah-event'
        eventinfo = {'fruit': 'apple', 'meat': 'pork'}

        for i in range(repetitions):
            self.reset_mocks()

            self.p.handle_github_notification(eventid, eventtype, eventinfo)

            self.assert_calls_equal(
                m_format_event,
                [call(eventid, eventtype, eventinfo)])

            expectedevdesc = "I don't know how to describe github %r events. Event id: %r"
            expectedsaycalls = []

            if i == 0:
                # Ensure we say something the first time:

                expectedsaycalls.append(
                    call(
                        self.channel,
                        (expectedevdesc + '\nI will say no more about event type %r.') % (
                            eventtype,
                            eventid,
                            eventtype)))

            self.assert_calls_equal(
                m_say,
                expectedsaycalls)

            # Ensure we log swallowed events:
            self.assert_calls_equal(
                self.m_loghandler,
                [call.handle(ArgIsLogRecord(levelname='INFO', msg=expectedevdesc))])


class ClientProtocolFactoryTests (LogMockingTestCase):
    def test_protocol_is_irc_ClientProtocol(self):
        self.assertIs(irc.ClientProtocol, irc.ClientProtocolFactory.protocol)

    def test_buildProtocol_resets_backoff_counter(self):
        f = self._build_factory()

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

    GithubNotificationLogTmpl = 'github notification %sid:%r type:%s %r'

    def test_github_notification_without_connection_logs_info(self):
        f = self._build_factory()

        # Peek behind the curtain:
        self.assertIsNone(f._protoinstance)

        eventid = 42
        eventname = 'blah-event'
        eventdict = {'fruit': 'apple', 'meat': 'pork'}

        f.handle_github_notification(eventid, eventname, eventdict)

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(ArgIsLogRecord(levelname='INFO', msg=self.GithubNotificationLogTmpl))])

    def test_github_notification_with_connection_debug_logs_and_delegates(self):
        f = self._build_factory()

        m_addr = self.make_mock()

        f.buildProtocol(m_addr)

        # Peek behind the curtain:
        self.assertIsNotNone(f._protoinstance)

        m_protoinstance = self.make_mock()

        # Poke behind the curtain:
        f._protoinstance = m_protoinstance

        eventid = 42
        eventname = 'blah-event'
        eventdict = {'fruit': 'apple', 'meat': 'pork'}

        f.handle_github_notification(eventid, eventname, eventdict)

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(ArgIsLogRecord(levelname='DEBUG', msg=self.GithubNotificationLogTmpl))])

        self.assert_calls_equal(
            m_protoinstance,
            [call.handle_github_notification(eventid, eventname, eventdict)])

    def _build_factory(self):
        nick = 'leastbot'
        password = 'blah'
        nickserv = 'the-nickserv-user'
        channel = '#foo'
        self.m_reactor = self.make_mock()

        return irc.ClientProtocolFactory(self.m_reactor, nick, password, nickserv, channel)

    def _check_reconnects_with_backoff(self, methodname):
        f = self._build_factory()

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
            self.m_reactor,
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


