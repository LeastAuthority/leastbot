import errno
from ConfigParser import RawConfigParser


def load(confdir):
    """
    @param confdir: A twisted FilePath for the config base dir.

    @returns a Configuration instance.

    @raises SystemExit - for usage errors.
    """
    def _read_and_parse_child(name, exampleconfig):
        childpath = confdir.child(name + '.conf')
        try:
            fp = childpath.open('r')
        except IOError, e:
            if e.errno == errno.ENOENT:
                raise SystemExit(ConfigMissingOutputTemplate % (childpath.path, exampleconfig))
            else:
                raise

        rcp = RawConfigParser()
        rcp.readfp(fp)
        return rcp

    secretrcp = _read_and_parse_child('secret', ExampleSecretConfig)
    publicrcp = _read_and_parse_child('public', ExamplePublicConfig)

    return ConfigStruct(
        secret = ConfigStruct(
            irc = ConfigStruct(
                password = secretrcp.get('irc client', 'password'),
                ),
            web = ConfigStruct(
                githubsecret = secretrcp.get('web server', 'githubsecret'),
                ),
            ),
        public = ConfigStruct(
            irc = ConfigStruct(
                host = publicrcp.get('irc client', 'host'),
                port = publicrcp.getint('irc client', 'port'),
                nick = publicrcp.get('irc client', 'nick'),
                channel = publicrcp.get('irc client', 'channel'),
                nickserv = publicrcp.get('irc client', 'nickserv'),
                ),
            web = ConfigStruct(
                port = publicrcp.getint('web server', 'port'),
                ),
            ),
        )


class ConfigStruct (object):
    def __init__(self, **attrs):
        for (n, v) in attrs.iteritems():
            setattr(self, n, v)


ConfigMissingOutputTemplate = """
# The config file %r is missing. This output is an example config file,
# which you can place at that path, then edit for your usage.

%s
"""

ExampleSecretConfig = """
[irc client]
password: fake-irc-password

[web server]
githubsecret: fake-github-secret
"""


ExamplePublicConfig = """
# Note: The irc client *always* uses ssl.
[irc client]
host: irc.example.com
port: 6667
nick: leastbot
channel: #leastbot-test

# This should be the nickname of a NickServ service bot:
nickserv: nickserv

[web server]
port: 8080
"""
