from mock import call
from leastbot.main import main
from leastbot.tests.mockutil import MockingTestCase


class mainTests (MockingTestCase):
    def test_main_twisted_setup(self):
        m_reactor = self.make_mock()

        main(args=[], reactor=m_reactor)

        self.assert_calls_equal(
            m_reactor,
            [call.run()])
