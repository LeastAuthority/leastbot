from mock import call

from leastbot.log import LogMixin
from leastbot.tests.mockutil import EqCallback
from leastbot.tests.logutil import LogMockingTestCase


class LogMixinTests (LogMockingTestCase):
    def test_LogMixin_subclass_nameless(self):

        class MyClass (LogMixin):
            def __init__(self):
                self._init_log()
                self._log.info('created')

        MyClass()

        def check_record_arg(rec):
            """<Record.msg == 'created'>"""
            return rec.msg == 'created'

        self.assert_calls_equal(
            self.m_loghandler,
            [call.handle(EqCallback(check_record_arg))])

