import pprint

from twisted.internet import reactor

from leastbot import webserver



def main(args, reactor=reactor):

    def handle_event(*a, **kw):
        print 'unhandled event:'
        pprint.pprint(a, kw)

    badsecret = 'Not a very good secret.'
    s = webserver.WebServer(reactor, badsecret, handle_event)
    s.listen(8080)

    reactor.run()
