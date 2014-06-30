import os
import sys
import logging
import argparse

from twisted.internet import reactor
from twisted.python import log
from twisted.python.filepath import FilePath

from leastbot import config
from leastbot import irc
from leastbot import webserver


DESCRIPTION="""
An IRC bot written during Least Authority Fun Fridays.
"""



def main(args=sys.argv[1:], reactor=reactor):
    opts = parse_args(args)
    init_logging(getattr(logging, opts.loglevel))

    c = config.load(FilePath(os.path.expanduser('~/.leastbot/')))

    ircclient = irc.Client(
        reactor,
        c.public.irc.host,
        c.public.irc.port,
        c.public.irc.nick,
        c.secret.irc.password,
        c.public.irc.nickserv,
        c.public.irc.channel)

    s = webserver.WebServer(
        reactor,
        c.public.web.port,
        c.secret.web.githubsecret,
        ircclient.handle_github_notification)

    s.listen()
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


