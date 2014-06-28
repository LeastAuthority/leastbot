from twisted.words.protocols import irc
from twisted.internet import protocol, ssl

from leastbot.log import LogMixin


class Client (LogMixin):
    def __init__(self, reactor, host, port, nick, password, channel):
        self._init_log()
        self._reactor = reactor
        self._host = host
        self._port = port
        self._factory = ClientProtocolFactory(reactor, nick, password, channel)

    def connect(self):
        self._log.info('Connecting to %s:%d...', self._host, self._port)
        sslctx =  ssl.ClientContextFactory() # BUG: Verify security properties of this usage.
        self._reactor.connectSSL(self._host, self._port, self._factory, sslctx)


class ClientProtocol (irc.IRCClient):
    pass


class ClientProtocolFactory (LogMixin, protocol.ClientFactory):

    protocol = ClientProtocol

    def __init__(self, reactor, nick, password, channel):
        self._reactor = reactor
        self._nick = nick
        self._password = password
        self._channel = channel
        self._delaytracker = BackoffDelayTracker()
        self._init_log()

    def buildProtocol(self, addr):
        self._delaytracker.reset()
        return protocol.ClientFactory.buildProtocol(self, addr)

    def clientConnectionFailed(self, connector, reason):
        self._reconnect_with_backoff(connector)

    def clientConnectionLost(self, connector, reason):
        self._reconnect_with_backoff(connector)

    def _reconnect_with_backoff(self, connector):
        delay = self._delaytracker.increment()
        self._log.info('Reconnecting in %.2f seconds.', delay)
        self._reactor.callLater(delay, connector.connect)


class BackoffDelayTracker (object):
    def __init__(self):
        self._failures = 0

    def increment(self):
        self._failures += 1
        return max(0, 1.5 ** self._failures - 1.5)

    def reset(self):
        self._failures = 0
