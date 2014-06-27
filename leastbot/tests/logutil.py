import logging

from leastbot.tests.mockutil import MockingTestCase


class LogMockingTestCase (MockingTestCase):
    def setUp(self):
        MockingTestCase.setUp(self)

        self.m_loghandler = self.make_mock()
        self.m_loghandler.level = logging.DEBUG

        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(self.m_loghandler)

    def tearDown(self):
        logging.getLogger().removeHandler(self.m_loghandler)
