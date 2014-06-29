import errno
from ConfigParser import RawConfigParser


def load(confdir):
    """
    @param confdir: A twisted FilePath for the config base dir.

    @returns a Configuration instance.

    @raises SystemExit - for usage errors.
    """
    def _read_and_parse_child(name):
        childpath = confdir.child(name + '.conf')
        try:
            fp = childpath.open('r')
        except IOError, e:
            if e.errno == errno.ENOENT:
                raise SystemExit(
                    'Config file %r does not exist. Try running `leastbot init-config --help`.' % (
                        childpath.path,
                        )
                    )
            else:
                raise

        rcp = RawConfigParser()
        rcp.readfp(fp)

        if rcp.has_option('unconfigured', 'unconfigured'):
            raise SystemExit(
                'Config file %r has not been properly configured yet.' % (
                    childpath.path,
                    )
                )

        return rcp

    secretrcp = _read_and_parse_child('secret')
    publicrcp = _read_and_parse_child('public')

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


SecretConfigExample = """
# Remove the "unconfigured" section and parameter, or else leastbot will
# assume you have not edited # this file properly:
[unconfigured]
unconfigured: true

[irc client]
password: fake-irc-password

[web server]
githubsecret: fake-github-secret
"""


PublicConfigExample = """
# Remove the "unconfigured" section and parameter, or else leastbot will
# assume you have not edited # this file properly:
[unconfigured]
unconfigured: true

# Note: The irc client *always* uses ssl.
[irc client]
host: irc.example.com
port: 6667
nick: leastbot

# This should be the nickname of a NickServ service bot:
nickserv: nickserv

[web server]
port: 8080
"""
