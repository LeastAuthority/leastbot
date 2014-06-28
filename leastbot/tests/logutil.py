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

        # A monkeypatch hack to improve the diagnostic utility of
        # LogRecord mismatches in test failures:
        original_repr = logging.LogRecord.__repr__
        logging.LogRecord.__repr__ = logging.LogRecord.__str__

        self.addCleanup(setattr, logging.LogRecord, '__repr__', original_repr)


def ArgIsLogRecord(msg=None, levelname=None):
    fields = []
    if msg is not None:
        fields.append('msg=%r' % (msg,))
    if levelname is not None:
        fields.append('levelname=%r' % (levelname,))
    desc = 'ArgIsLogRecord(%s)' % (', '.join(fields),)

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

    return EqCallback(check_arg, desc)
