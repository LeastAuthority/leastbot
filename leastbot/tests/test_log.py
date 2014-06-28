from mock import call

from leastbot.log import LogMixin
from leastbot.tests.logutil import LogMockingTestCase, ArgIsLogRecord


class LogMixinTests (LogMockingTestCase):
    def test_LogMixin_subclass_nameless(self):

        class MyClass (LogMixin):
            def __init__(self):
                self._init_log()
                self._log.info('created')

        MyClass()

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(ArgIsLogRecord(msg='created'))])

