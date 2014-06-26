from twisted.web import server

from leastbot import github


class WebServer (object):
    def __init__(self, reactor, secret, handle_event):
        self._reactor = reactor
        self._site = server.Site(github.WebhookResource(secret, handle_event))

    def listen(self, port):
        self._reactor.listenTCP(port, self._site)
