from twisted.words.protocols import irc
from twisted.internet import protocol, ssl

from leastbot import github
from leastbot.log import LogMixin


class Client (LogMixin):
    def __init__(self, reactor, host, port, nick, password, nickserv, channel):
        self._init_log()
        self._reactor = reactor
        self._host = host
        self._port = port
        self._factory = ClientProtocolFactory(reactor, nick, password, nickserv, channel)

    def connect(self):
        self._log.info('Connecting to %s:%d...', self._host, self._port)
        sslctx =  ssl.ClientContextFactory() # BUG: Verify security properties of this usage.
        self._reactor.connectSSL(self._host, self._port, self._factory, sslctx)

    def handle_github_notification(self, eventid, name, details):
        self._factory.handle_github_notification(eventid, name, details)


class ClientProtocol (LogMixin, irc.IRCClient):
    def __init__(self, nick, password, nickserv, channel):
        self.nickname = nick # NOTE: base class uses a partially-side-effect-dependent API.
        self._password = password
        self._nickserv = nickserv
        self._channel = channel
        self._init_log()

        self._nickservloginsuccess = 'You are successfully identified as \x02%s\x02.' % (self.nickname,)

    # Github notifications api:
    def handle_github_notification(self, eventid, name, details):
        message = github.format_event(eventid, name, details)
        self.say(self._channel, message)

    # Logging passthrough layer:
    def handleCommand(self, command, prefix, params):
        self._log.debug('handleCommand(command=%r, prefix=%r, params=%r)', command, prefix, params)
        irc.IRCClient.handleCommand(self, command, prefix, params)

    def msg(self, user, message, length=None):
        self._log.debug('msg(user=%r, message=%r, length=%r)', user, message, length)
        irc.IRCClient.msg(self, user, message, length)

    # Logging event responders:
    def connectionMade(self):
        self._log.info('Connected as %r.', self.nickname)
        irc.IRCClient.connectionMade(self)

    def signedOn(self):
        self.msg(self._nickserv, 'identify %s' % (self._password,))

    def noticed(self, user, channel, message):
        usershort = user.split('!', 1)[0]

        if (usershort, channel, message) == (self._nickserv, self.nickname, self._nickservloginsuccess):
            self._log.info(
                'Successfully authenticated with %r; joining %r',
                self._nickserv,
                self._channel)
            self.join(self._channel)
            return


class ClientProtocolFactory (LogMixin, protocol.ClientFactory):

    protocol = ClientProtocol

    def __init__(self, reactor, nick, password, nickserv, channel):
        self._reactor = reactor
        self._nick = nick
        self._password = password
        self._nickserv = nickserv
        self._channel = channel
        self._delaytracker = BackoffDelayTracker()
        self._protoinstance = None
        self._init_log()

    # Github notifications api:
    def handle_github_notification(self, eventid, name, details):
        if self._protoinstance is None:
            logfunc = self._log.info
            state = 'without connection '
            delegate = lambda eventid, eventname, eventdict: None
        else:
            logfunc = self._log.debug
            state = ''
            delegate = self._protoinstance.handle_github_notification

        logfunc('github notification %sid:%r type:%s %r', state, eventid, name, details)
        delegate(eventid, name, details)

    # Twisted event handlers:
    def buildProtocol(self, addr):
        """overrides protocol.ClientFactory.buildProtocol."""
        assert self._protoinstance is None, \
            'Invariant violation: self._protoinstance %r' % (self._protoinstance,)

        self._delaytracker.reset()
        self._protoinstance = self.protocol(self._nick, self._password, self._nickserv, self._channel)
        return self._protoinstance

    def clientConnectionFailed(self, connector, reason):
        self._reconnect_with_backoff(connector, 'failed', reason)

    def clientConnectionLost(self, connector, reason):
        self._reconnect_with_backoff(connector, 'lost', reason)

    def _reconnect_with_backoff(self, connector, event, reason):
        delay = self._delaytracker.increment()
        self._log.info('Connection %s: %r (Reconnecting in %.2f seconds.)', event, reason, delay)
        self._reactor.callLater(delay, connector.connect)


class BackoffDelayTracker (object):
    def __init__(self):
        self._failures = 0

    def increment(self):
        self._failures += 1
        return max(0, 1.5 ** self._failures - 1.5)

    def reset(self):
        self._failures = 0
