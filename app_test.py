import base64
import unittest

import flask_testing
import mock

from app import app

class AppTest(flask_testing.TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    def test_forbidden_if_no_credentials(self):
        resp = self.client.post('/log')
        self.assertEqual(403, resp.status_code)

    @mock.patch('settings.LOG_DRAIN_USERNAME', 'test-username')
    @mock.patch('settings.LOG_DRAIN_PASSWORD', 'test-password')
    @mock.patch('app._post_to_bigquery')
    def test_allowed_if_credentials_match(self, mock_post_to_bigquery):
        credentials = base64.b64encode('test-username:test-password')
        resp = self.client.post('/log', headers={'Authorization': 'Basic ' + credentials})
        self.assertEqual(200, resp.status_code)
        self.assertEqual('', resp.data)
        mock_post_to_bigquery.assert_not_called()

    @mock.patch('settings.LOG_DRAIN_USERNAME', 'test-username')
    @mock.patch('settings.LOG_DRAIN_PASSWORD', 'test-password')
    @mock.patch('app._post_to_bigquery')
    def test_single_record(self, mock_post_to_bigquery):
        body = '''403 <190>1 2017-08-22T23:39:51.262277+00:00 host app web.1 - json: {"duration": 0.027, "host": "test.com", "method": "GET", "path": "/", "referrer": "", "remote_addr": "11.11.222.333", "response_code": 200, "timestamp": "2017-08-22T23:39:51.261888+00:00", "url": "/", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36"}\n'''
        credentials = base64.b64encode('test-username:test-password')
        resp = self.client.post('/log', data=body, headers={'Authorization': 'Basic ' + credentials})
        self.assertEqual(200, resp.status_code)
        self.assertEqual('', resp.data)

        mock_post_to_bigquery.assert_called_once()
        log_records = mock_post_to_bigquery.call_args[0][0]
        self.assertEqual(1, len(log_records))
        expected_record = {
            'duration': 0.027,
            'host': 'test.com',
            'method': 'GET',
            'path': '/',
            'referrer': '',
            'remote_addr': '11.11.222.333',
            'response_code': 200,
            'timestamp': '2017-08-22T23:39:51.261888+00:00',
            'url': '/',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
        }
        self.assertEqual(expected_record, log_records[0])

    @mock.patch('settings.LOG_DRAIN_USERNAME', 'test-username')
    @mock.patch('settings.LOG_DRAIN_PASSWORD', 'test-password')
    @mock.patch('app._post_to_bigquery')
    def test_two_records(self, mock_post_to_bigquery):
        line1 = '''403 <190>1 2017-08-22T23:39:51.262277+00:00 host app web.1 - json: {"duration": 0.027, "host": "test.com", "method": "GET", "path": "/", "referrer": "", "remote_addr": "11.11.222.333", "response_code": 200, "timestamp": "2017-08-22T23:39:51.261888+00:00", "url": "/", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36"}'''
        line2 = '''390 <190>1 2017-08-30T23:39:51.000000+00:00 host app web.1 - json: {"host": "test.com", "method": "GET", "path": "/foo", "referrer": "", "remote_addr": "1.2.3.4", "response_code": 200, "timestamp": "2017-08-30T23:39:51.000000+00:00", "url": "/foo?bar=1", "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36"}'''
        body = '%s\n%s\n' % (line1, line2)
        credentials = base64.b64encode('test-username:test-password')
        resp = self.client.post('/log', data=body, headers={'Authorization': 'Basic ' + credentials})
        self.assertEqual(200, resp.status_code)
        self.assertEqual('', resp.data)

        mock_post_to_bigquery.assert_called_once()
        log_records = mock_post_to_bigquery.call_args[0][0]
        self.assertEqual(2, len(log_records))
        expected_record1 = {
            'duration': 0.027,
            'host': 'test.com',
            'method': 'GET',
            'path': '/',
            'referrer': '',
            'remote_addr': '11.11.222.333',
            'response_code': 200,
            'timestamp': '2017-08-22T23:39:51.261888+00:00',
            'url': '/',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
        }
        self.assertEqual(expected_record1, log_records[0])
        expected_record2 = {
            'host': 'test.com',
            'method': 'GET',
            'path': '/foo',
            'referrer': '',
            'remote_addr': '1.2.3.4',
            'response_code': 200,
            'timestamp': '2017-08-30T23:39:51.000000+00:00',
            'url': '/foo?bar=1',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
        }
        self.assertEqual(expected_record2, log_records[1])

    @mock.patch('settings.LOG_DRAIN_USERNAME', 'test-username')
    @mock.patch('settings.LOG_DRAIN_PASSWORD', 'test-password')
    @mock.patch('app._post_to_bigquery')
    def test_garbage_record(self, mock_post_to_bigquery):
        body = 'garbage'
        credentials = base64.b64encode('test-username:test-password')
        resp = self.client.post('/log', data=body, headers={'Authorization': 'Basic ' + credentials})
        self.assertEqual(200, resp.status_code)
        self.assertEqual('', resp.data)
        mock_post_to_bigquery.assert_not_called()

    @mock.patch('settings.LOG_DRAIN_USERNAME', 'test-username')
    @mock.patch('settings.LOG_DRAIN_PASSWORD', 'test-password')
    @mock.patch('app._post_to_bigquery')
    def test_malformed_record2(self, mock_post_to_bigquery):
        body = '100 foo'
        credentials = base64.b64encode('test-username:test-password')
        resp = self.client.post('/log', data=body, headers={'Authorization': 'Basic ' + credentials})
        self.assertEqual(200, resp.status_code)
        self.assertEqual('', resp.data)
        mock_post_to_bigquery.assert_not_called()

        body = '2 foo'
        credentials = base64.b64encode('test-username:test-password')
        resp = self.client.post('/log', data=body, headers={'Authorization': 'Basic ' + credentials})
        self.assertEqual(200, resp.status_code)
        self.assertEqual('', resp.data)
        mock_post_to_bigquery.assert_not_called()

    def test_render_default_diagnostics(self):
        resp = self.client.get('/')
        self.assertEqual(200, resp.status_code)

if __name__ == '__main__':
    unittest.main()
