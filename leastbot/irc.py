from twisted.internet import protocol, ssl

from leastbot.log import LogMixin


class Client (LogMixin):
    def __init__(self, reactor, host, port, nick, password, channel):
        self._init_log()
        self._reactor = reactor
        self._host = host
        self._port = port
        self._factory = ClientFactory(nick, password, channel)

    def connect(self):
        self._log.info('Connecting to %s:%d...', self._host, self._port)
        sslctx =  ssl.ClientContextFactory() # BUG: Verify security properties of this usage.
        self._reactor.connectSSL(self._host, self._port, self._factory, sslctx)


class ClientFactory (protocol.ClientFactory):
    def __init__(self, nick, password, channel):
        self._nick = nick
        self._password = password
        self._channel = channel
