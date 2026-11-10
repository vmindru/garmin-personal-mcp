"""Offline checks: credentials, network boundaries, pagination, partial data."""
import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

spec = importlib.util.spec_from_file_location(
    'garmin_personal', Path(__file__).resolve().parents[1] / 'scripts/garmin-personal.py')
garmin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(garmin)


class GarminTests(unittest.TestCase):
    def test_token_endpoint_accepts_plain_text(self):
        with patch.object(garmin.urllib.request, 'build_opener') as opener:
            opener.return_value.open.return_value = io.BytesIO(b'example-token\n')
            self.assertEqual(garmin.request(garmin.TOKEN_PATH, 'ApiKey example-key', method='POST'),
                             'example-token')
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.get_header('Accept'), '*/*')

    def test_plain_text_token_response(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'garmin'
            garmin.private_write(state / 'api-key', 'example-key\n')
            with patch.object(garmin, 'STATE', state), patch.object(
                    garmin, 'request', return_value='example-token\n'):
                self.assertEqual(garmin.access_token(), 'example-token')

    def test_private_key_and_token_exchange(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'garmin'
            garmin.private_write(state / 'api-key', 'example-key\n')
            self.assertEqual((state / 'api-key').stat().st_mode & 0o777, 0o600)
            with patch.object(garmin, 'STATE', state), patch.object(
                    garmin, 'request', return_value={'access_token': 'example-token'}) as call:
                self.assertEqual(garmin.access_token(), 'example-token')
                call.assert_called_once_with(garmin.TOKEN_PATH, 'ApiKey example-key', method='POST')
                (state / 'api-key').chmod(0o644)
                with self.assertRaises(garmin.SafeError):
                    garmin.access_token()
                self.assertEqual(call.call_count, 1)

    def test_redirects_refused(self):
        self.assertIsNone(garmin.NoRedirect().redirect_request(
            None, None, 302, '', {}, 'https://example.com'))

    def test_http_errors_do_not_echo_server_body(self):
        error = urllib.error.HTTPError('https://example.com', 401, 'secret-value', {}, None)
        with patch.object(garmin.urllib.request, 'build_opener') as opener:
            opener.return_value.open.side_effect = error
            with self.assertRaises(garmin.SafeError) as caught:
                garmin.request('/userprofile-service/userprofile/settings', 'Bearer example-token')
            self.assertNotIn('secret-value', str(caught.exception))
            self.assertNotIn('example-token', str(caught.exception))

    def test_snapshot_chunks_paginates_and_records_partial_failure(self):
        requests = []
        def fake(path, auth, method='GET', query=None):
            self.assertEqual(auth, 'Bearer example-token')
            self.assertEqual(method, 'GET')
            requests.append((path, query))
            if 'search/activities' in path:
                return [{'activityId': i} for i in range(99)] if query['start'] == 0 else []
            if 'hrv-service' in path:
                raise garmin.SafeError('Garmin HTTP 403.')
            return []
        with patch.object(garmin, 'request', side_effect=fake):
            result = garmin.snapshot('example-token', dt.date(2026, 1, 1), dt.date(2026, 3, 31))
        self.assertEqual(len(result['data']['activities']), 99)
        self.assertEqual(len(result['errors']), 4)
        self.assertEqual([q['start'] for p, q in requests if 'search/activities' in p], [0, 99])
        for path, query in requests:
            if 'dailySleepSummariesByDate' in path or 'reports/daily' in path:
                duration = dt.date.fromisoformat(query['endDate']) - dt.date.fromisoformat(query['startDate'])
                self.assertLessEqual(duration.days, 27)
        self.assertNotIn('example-token', json.dumps(result))

    def test_date_validation(self):
        self.assertEqual(garmin.date_range('2026-01-28', 28),
                         (dt.date(2026, 1, 1), dt.date(2026, 1, 28)))
        for end, days in [('invalid', 1), ('2026-01-01', 0), ('2026-01-01', 91), ('9999-01-01', 1)]:
            with self.assertRaises(garmin.SafeError):
                garmin.date_range(end, days)


if __name__ == '__main__':
    unittest.main()
