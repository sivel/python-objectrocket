import requests
import unittest

from objectrocket import exceptions
from objectrocket import __version__
from objectrocket.client import Client

class TestSimple(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_no_api_key(self):
        client = Client()
        with self.assertRaises(exceptions.ObjectRocketNoApiKey):
            client.api_key
        self.assertEqual(client._session, None)

    def test_api_key_construct(self):
        client = Client('1234')
        self.assertEqual(client.api_key, '1234')
        self.assertNotEqual(client._session, None)

    def test_api_key_setter(self):
        client = Client()
        with self.assertRaises(exceptions.ObjectRocketNoApiKey):
            client.api_key
        client.api_key = '1234'
        self.assertEqual(client.api_key, '1234')
        self.assertNotEqual(client._session, None)

    def test_user_agent(self):
        client = Client()
        self.assertIn('ObjectRocket/%s' % __version__,
                      client._create_user_agent())

    def test_requests_session(self):
        client = Client('1234')
        self.assertIsInstance(client._session, requests.Session)
        headers = client._session.headers
        self.assertEqual(headers['Accept'], 'text/plain,application/json')
        self.assertEqual(headers['User-Agent'], client._create_user_agent())

    def test_post_data(self):
        client = Client('1234')
        self.assertEqual(client._post_data(), {'api_key': '1234'})
        self.assertEqual(client._post_data(dict(doc={})),
                         {'api_key': '1234', 'doc': '{}'})

    def test_parse_data(self):
        client = Client('1234')
        good = {
            'data': 'test',
            'rc': 0
        }
        bad_msg = {
            'msg': 'fail',
            'rc': 1
        }
        bad_data = {
            'data': '1234',
            'rc': 1
        }

        self.assertEqual(client._parse_data(good), good['data'])

        with self.assertRaises(exceptions.ObjectRocketNonZeroRC) as e:
            client._parse_data(bad_msg)
        self.assertEqual(e.exception.errno, 1)
        self.assertEqual(e.exception.strerror, 'fail')

        with self.assertRaises(exceptions.ObjectRocketNonZeroRC) as e:
            client._parse_data(bad_data)
        self.assertEqual(e.exception.errno, 1)
        self.assertEqual(e.exception.strerror, 'No msg provided (1234)')

    def test_add_user_type(self):
        client = Client('1234')
        self.assertEqual(client.add_user, client.add_database)
