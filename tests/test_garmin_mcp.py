"""Offline MCP protocol and Garmin boundary checks using the official SDK."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mcp.client import Client

spec = importlib.util.spec_from_file_location(
    'garmin_mcp', Path(__file__).resolve().parents[1] / 'scripts/garmin-mcp.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_discovery_and_status_need_no_credentials_or_network(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
                server.garmin, 'STATE', Path(directory)), patch.object(
                server.garmin, 'request', side_effect=AssertionError('Network must not run')):
            async with Client(server.mcp) as client:
                tools = (await client.list_tools()).tools
                self.assertEqual(len(tools), 5)
                self.assertTrue(all(tool.annotations.read_only_hint for tool in tools))
                result = await client.call_tool('garmin_connection_status', {})
                self.assertFalse(result.is_error)
                self.assertFalse(result.structured_content['key_configured'])

    async def test_metric_routes_to_documented_endpoint(self):
        with patch.object(server, 'fetch', return_value={'sleepScore': 80}) as fetch:
            async with Client(server.mcp) as client:
                result = await client.call_tool('garmin_health_stats', {'metric': 'sleep', 'date': '2026-01-01'})
            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content['data'], {'sleepScore': 80})
            fetch.assert_called_once_with('/sleep-service/sleep/dailySleep', {'date': '2026-01-01'})

    async def test_invalid_inputs_never_contact_garmin(self):
        with patch.object(server, 'fetch', side_effect=AssertionError('Network must not run')), patch.object(
                server, 'token', side_effect=AssertionError('Authentication must not run')):
            async with Client(server.mcp) as client:
                for name, args in [
                    ('garmin_health_stats', {'metric': 'unknown'}),
                    ('garmin_health_stats', {'metric': 'sleep', 'date': 'not-a-date'}),
                    ('garmin_activity', {'activity_id': -1}),
                    ('garmin_list_activities', {'limit': 100}),
                    ('garmin_training_snapshot', {'days': 91}),
                ]:
                    result = await client.call_tool(name, args)
                    self.assertTrue(result.is_error, name)

    async def test_activity_pagination_is_explicit(self):
        with patch.object(server, 'fetch', return_value=[{'activityId': 1}, {'activityId': 2}]) as fetch:
            async with Client(server.mcp) as client:
                result = await client.call_tool('garmin_list_activities',
                                                {'end': '2026-01-28', 'days': 28, 'limit': 2, 'offset': 4})
            self.assertFalse(result.is_error)
            self.assertTrue(result.structured_content['has_more'])
            self.assertEqual(result.structured_content['next_offset'], 6)
            self.assertEqual(fetch.call_args.args[1]['startDate'], '2026-01-01')
            self.assertEqual(fetch.call_args.args[1]['start'], 4)

    async def test_snapshot_preserves_partial_failures_and_does_not_write(self):
        payload = {'data': {'activities': []}, 'errors': {'sleep': 'Garmin HTTP 403.'}}
        with patch.object(server, 'token', return_value='example-token'), patch.object(
                server.garmin, 'snapshot', return_value=payload), patch.object(
                server.garmin, 'private_write', side_effect=AssertionError('Must not persist data')):
            async with Client(server.mcp) as client:
                result = await client.call_tool('garmin_training_snapshot', {'end': '2026-01-28'})
            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content['errors'], payload['errors'])
            self.assertNotIn('example-token', str(result))

    async def test_unexpected_exception_is_sanitized(self):
        with patch.object(server, 'fetch', side_effect=RuntimeError('secret-token-value')):
            async with Client(server.mcp) as client:
                result = await client.call_tool('garmin_activity', {'activity_id': 1})
            self.assertTrue(result.is_error)
            self.assertNotIn('secret-token-value', str(result))


class TokenTests(unittest.TestCase):
    def setUp(self):
        server._token = None
        server._token_until = 0
        server._key_signature = None

    def test_token_cache_renews_on_expiry_and_key_rotation(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
                server.garmin, 'STATE', Path(directory)), patch.object(
                server.garmin, 'access_token', side_effect=['first', 'renewed', 'rotated']) as auth:
            path = Path(directory) / 'api-key'
            server.garmin.private_write(path, 'example-key')
            self.assertEqual(server.token(), 'first')
            self.assertEqual(server.token(), 'first')
            self.assertEqual(auth.call_count, 1)
            server._token_until = 0
            self.assertEqual(server.token(), 'renewed')
            server.garmin.private_write(path, 'replacement-key')
            self.assertEqual(server.token(), 'rotated')
            path.chmod(0o644)
            with self.assertRaises(server.garmin.SafeError):
                server.token()

    def test_unauthorized_request_reauthenticates_once(self):
        with patch.object(server, 'token', side_effect=['old', 'new']), patch.object(
                server.garmin, 'request', side_effect=[server.garmin.SafeError('Garmin HTTP 401.'), {'ok': True}]) as req:
            self.assertEqual(server.fetch('/hrv-service/hrv/2026-01-01'), {'ok': True})
            self.assertEqual(req.call_args.args[1], 'Bearer new')


if __name__ == '__main__':
    unittest.main()
