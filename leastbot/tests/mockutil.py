from pprint import pformat
from twisted.trial import unittest
import mock


class MockingTestCase (unittest.TestCase):
    def setUp(self):
        self._patchers = []

    def tearDown(self):
        for (p, _) in self._patchers:
            if p is not None:
                p.stop()

    def patch(self, name):
        p = mock.patch(name)
        mockobj = p.start()
        self._patchers.append( (p, mockobj) )
        return mockobj

    def make_mock(self):
        mockobj = mock.MagicMock()
        self._patchers.append( (None, mockobj) )
        return mockobj

    def reset_mocks(self):
        for (_, m) in self._patchers:
            m.reset_mock()

    def assert_calls_equal(self, mockobj, expectedcalls):
        mockcalls = mockobj._mock_mock_calls
        self.assertEqual(
            len(mockcalls), len(expectedcalls),
            'len(%s) == %r != len(%s) == %r' % (
                pformat(mockcalls), len(mockcalls),
                pformat(expectedcalls), len(expectedcalls)))

        for i, (mockcall, expectedcall) in enumerate(zip(mockcalls, expectedcalls)):
            try:
                self.assertEqual(
                    mockcall, expectedcall,
                    'Arg %d:\n%s\n  !=\n%s' % (i, pformat(mockcall), pformat(expectedcall)))
            except AssertionError, e:
                raise
            except Exception, e:
                e.args += ('Internal unittesting exception; vars:', i, mockcall, expectedcall)
                raise
