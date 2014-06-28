import re
import logging

from leastbot.tests.mockutil import MockingTestCase, EqCallback


class LogMockingTestCase (MockingTestCase):
    def setUp(self):
        MockingTestCase.setUp(self)

        self.m_loghandler = self.make_mock()
        self.m_loghandler.level = logging.DEBUG

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(self.m_loghandler)

        self.addCleanup(root.removeHandler, self.m_loghandler)


def ArgIsLogRecord(msg=None, levelname=None):
    if msg is not None:
        msg = re.compile(msg)

    def check_arg(x):
        # Gauntlet style: Any early return is False, only passing every test gives True:
        if not isinstance(x, logging.LogRecord):
            return False

        if levelname is not None and x.levelname != levelname:
            return False

        if msg is not None and msg.match(x.msg) is None:
            return False

        return True

    desc = 'ArgIsLogRecord()'

    return EqCallback(check_arg, desc)
