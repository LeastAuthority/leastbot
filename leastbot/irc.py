from twisted.words.protocols import irc
from twisted.internet import protocol, ssl

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


class ClientProtocol (LogMixin, irc.IRCClient):
    def __init__(self, nick, password, nickserv, channel):
        self._nick = nick
        self._password = password
        self._nickserv = nickserv
        self._channel = channel
        self._init_log()

        self.nickname = nick # Ugh...  base class uses a partially-side-effect-dependent API.

    # Logging passthrough layer:
    def handleCommand(self, command, prefix, params):
        self._log.debug('handleCommand(command=%r, prefix=%r, params=%r)', command, prefix, params)
        irc.IRCClient.handleCommand(self, command, prefix, params)

    def msg(self, user, message):
        self._log.debug('msg(user=%r, message=%r)', user, message)
        irc.IRCClient.msg(self, user, message)

    # Logging event responders:
    def connectionMade(self):
        self._log.info('Connected as %r.', self.nickname)
        irc.IRCClient.connectionMade(self)

    def signedOn(self):
        self.msg(self._nickserv, 'identify %s' % (self._password,))

    def privmsg(self, user, channel, message):
        if user == self._nickserv and channel is None:
            if message == 'You are successfully identified as \x02%s\x02.' % (self._nick,):
                self._log.info(
                    'Successfully authenticated with %r; joining %r',
                    self._nickserv,
                    self._channel)
                self.join(self._channel)
                return

        # Temporary hack for interactive testing:
        self._log.warning('Unexpected privmsg: user=%r, channel=%r, message=%r', user, channel, message)


class ClientProtocolFactory (LogMixin, protocol.ClientFactory):

    protocol = ClientProtocol

    def __init__(self, reactor, nick, password, nickserv, channel):
        self._reactor = reactor
        self._nick = nick
        self._password = password
        self._nickserv = nickserv
        self._channel = channel
        self._delaytracker = BackoffDelayTracker()
        self._init_log()

    def buildProtocol(self, addr):
        """overrides protocol.ClientFactory.buildProtocol."""
        self._delaytracker.reset()
        return self.protocol(self._nick, self._password, self._nickserv, self._channel)

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
