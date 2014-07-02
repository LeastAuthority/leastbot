========
leastbot
========

Scratching an itch.

Recommended Deployment on Debian-like
=====================================

#. Install system-wide recent `virtualenv` as per `these instructions`_.

    .. _`these instructions`: http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation

#. install C build stuff for dependencies:

    .. code::

        sudo apt-get install build-essential python-dev libffi-dev

#. Create a specific user:

    .. code::

        sudo adduser --disabled-password leastbot

#. Become that user:

    .. code::

        sudo su - leastbot

#. Create and activate a `virtualenv` for `leastbot` and its dependencies:

    .. code::

        mkdir ./leastbotvenv
        virtualenv ./leastbotvenv
        source ./leastbotvenv/bin/activate

#. Install `service_identity` for some weird reason I don't quite understand but seems related to the python `cryptography` package:

    .. code::

        pip install service_identity

#. Install `leastbot` from pypi (into the activated `virtualenv`):

    .. code::

        pip install leastbot

#. Run `leastbot` to see an error message about how the secret config file is missing:

    .. code::

        leastbot

#. Cut and paste the output of the last command into the path it specifies, then edit that file to fit your secret credentials (one for github, one for irc).

    (Also, you probably want to make this file readable only by the `leastbot` user.)

#. Repeat the "missing config" process for the public config:

    .. code::

        leastbot

#. Cut, paste, edit, public config.

#. Finally, run `leastbot`, which should succeed and connect to irc:

    .. code::

        leastbot

    .. warning:: The default commandline is equivalent to ``leastbot --log-level DEBUG`` which is *very verbose* and includes *all messages to a channel*.  Be aware of the confidentiality and space impact.  I *believe* that ``leastbot --log-level INFO`` will be relatively concise and privacy-preserving.  Caveat emptor.

#. Verify `leastbot` has joined the expected irc channel by viewing its log output and also by joining the channel with another irc client and observing the channel roster and/or join notifications.

#. Go configure github webhook notifications to point to your leastbot web port.  Test them by clicking test buttons.

    .. admonition:: TODO

        Improve this part of the instructions.
