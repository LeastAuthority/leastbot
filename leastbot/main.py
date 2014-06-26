from twisted.internet import reactor



def main(args, reactor=reactor):
    print 'Hello World!'
    reactor.run()
