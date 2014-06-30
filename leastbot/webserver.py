from twisted.web import server

from leastbot import github


class WebServer (object):
    def __init__(self, reactor, port, secret, handle_event):
        self._reactor = reactor
        self._port = port
        self._site = server.Site(github.WebhookResource(secret, handle_event))

    def listen(self):
        self._reactor.listenTCP(self._port, self._site)
