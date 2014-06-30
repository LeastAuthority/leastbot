from mock import call

from leastbot.tests.mockutil import MockingTestCase
from leastbot import webserver


class WebserverTests (MockingTestCase):
    def setUp(self):
        MockingTestCase.setUp(self)

        self.f_secret = 'fake secret'
        self.f_port = 1234
        self.m_reactor = self.make_mock()
        self.m_handle_event = self.make_mock()
        self.m_WebhookResource = self.patch('leastbot.github.WebhookResource')
        self.m_Site = self.patch('twisted.web.server.Site')

        self.s = webserver.WebServer(self.m_reactor, self.f_port, self.f_secret, self.m_handle_event)

    def test___init__(self):
        self.assert_calls_equal(self.m_reactor, [])
        self.assert_calls_equal(self.m_handle_event, [])
        self.assert_calls_equal(self.m_WebhookResource, [call(self.f_secret, self.m_handle_event)])
        self.assert_calls_equal(self.m_Site, [call(self.m_WebhookResource.return_value)])

    def test_listen(self):
        self.s.listen()

        self.assert_calls_equal(self.m_reactor, [call.listenTCP(self.f_port, self.m_Site.return_value)])
