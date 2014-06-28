import sys
import pprint
import logging
import argparse

from twisted.internet import reactor
from twisted.python import log

from leastbot import irc
from leastbot import webserver


DESCRIPTION="""
An IRC bot written during Least Authority Fun Fridays.
"""



def main(args=sys.argv[1:], reactor=reactor):
    opts = parse_args(args)
    init_logging(getattr(logging, opts.loglevel))

    irchost = 'irc.oftc.net'
    ircport = 6697
    nick = 'leastbot'
    password = '012345'
    nickserv = 'nickserv'
    channel = '#leastbot-test'

    ircclient = irc.Client(reactor, irchost, ircport, nick, password, nickserv, channel)

    def handle_event(*a, **kw):
        pprint.pprint(('unhandled event:', a, kw))

    badsecret = 'abc'
    s = webserver.WebServer(reactor, badsecret, handle_event)
    s.listen(8080)

    ircclient.connect()

    reactor.run()


def parse_args(args):
    p = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('--log-level',
                   dest='loglevel',
                   default='DEBUG',
                   choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'],
                   help='Set logging level.')

    return p.parse_args(args)



LogFormat = '%(asctime)s %(levelname) 5s %(name)s | %(message)s'
DateFormat = '%Y-%m-%dT%H:%M:%S%z'

def init_logging(level):
    logging.basicConfig(
        stream=sys.stdout,
        format=LogFormat,
        datefmt=DateFormat,
        level=level)

    log.PythonLoggingObserver().start()


