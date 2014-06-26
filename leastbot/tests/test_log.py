import logging

from mock import call

from leastbot.log import LogMixin
from leastbot.tests.mockutil import MockingTestCase, EqCallback


class LogMixinTests (MockingTestCase):
    def setUp(self):
        MockingTestCase.setUp(self)

        self.m_handler = self.make_mock()
        self.m_handler.level = logging.DEBUG

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(self.m_handler)

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
            self.m_handler,
            [call.handle(EqCallback(check_record_arg))])

