#!/usr/bin/env python3
"""Read your own Garmin data through the official Personal API (stdlib only)."""
import argparse
import datetime as dt
import getpass
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STATE = Path(os.environ.get('GARMIN_CONFIG_DIR', str(ROOT / '.local' / 'garmin'))).expanduser().resolve()
BASE = 'https://personal.connectapi.garmin.com'
TOKEN_PATH = '/personalapitoken-service/personal-api/personal-api-key/token'


class SafeError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward authentication to another host or endpoint.
        return None


def request(path, authorization, method='GET', query=None):
    url = BASE + path
    if query:
        url += '?' + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, method=method, headers={
        'Authorization': authorization, 'Accept': '*/*' if path == TOKEN_PATH else 'application/json',
        'User-Agent': 'personal-agent-garmin/1.0',
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=45) as response:
            if path == TOKEN_PATH:
                payload = response.read().decode('utf-8').strip()
                try:
                    return json.loads(payload)
                except ValueError:
                    return payload
            return json.load(response)
    except urllib.error.HTTPError as exc:
        hints = {401: 'Check or renew the Personal API key.',
                 403: 'Check Personal API access for your Garmin account.',
                 429: 'Garmin rate limit reached; try again later.'}
        # Response bodies and request headers may contain secrets.
        raise SafeError(f'Garmin HTTP {exc.code}. ' + hints.get(exc.code, 'Request failed.')) from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise SafeError('Garmin network request failed or returned invalid JSON.') from None


def private_write(path, content):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def access_token():
    path = STATE / 'api-key'
    if not path.is_file():
        raise SafeError('No Garmin key configured. Run: python3 scripts/garmin-personal.py init')
    if path.stat().st_mode & 0o077:
        raise SafeError('Key file must be private: set the configured api-key file to mode 0600.')
    key = path.read_text().strip()
    if not key or any(c.isspace() for c in key):
        raise SafeError('Stored API key is empty or contains whitespace.')
    result = request(TOKEN_PATH, 'ApiKey ' + key, method='POST')
    token = (result.get('access_token') or result.get('accessToken')) if isinstance(result, dict) else result
    if isinstance(token, str):
        token = token.strip()
    if not isinstance(token, str) or not token or any(c.isspace() for c in token):
        raise SafeError('Unexpected Garmin token response; token was not displayed or saved.')
    return token


def date_range(end, days):
    if not 1 <= days <= 90:
        raise SafeError('--days must be between 1 and 90.')
    try:
        end_date = dt.date.fromisoformat(end)
    except ValueError:
        raise SafeError('--end must be YYYY-MM-DD.') from None
    if end_date > dt.datetime.now(dt.timezone.utc).date():
        raise SafeError('--end cannot be in the future.')
    return end_date - dt.timedelta(days=days - 1), end_date


def snapshot(token, start, end):
    auth = 'Bearer ' + token
    get = lambda path, query=None: request(path, auth, query=query)
    result = {'source': 'Garmin Connect Personal API', 'start_date': str(start),
              'end_date': str(end), 'fetched_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'data': {}, 'errors': {},
              'limitations': ['Training Readiness and Training Status are not published in this API.',
                              'Missing metrics are not evidence of recovery or good health.']}
    # Keep successful categories when Garmin cannot return a particular metric.
    def collect(name, path, query=None):
        try:
            result['data'][name] = get(path, query)
        except SafeError as exc:
            result['errors'][name] = str(exc)

    collect('daily_summaries', '/usersummary-service/v2/dailysummaries',
            {'startDate': str(start), 'endDate': str(end)})
    collect('heart_rate_zones', '/biometric-service/heartRateZones/v2')
    # Sleep and Body Battery ranges support at most 31 days per request.
    cursor = start
    while cursor <= end:
        last = min(cursor + dt.timedelta(days=27), end)
        query = {'startDate': str(cursor), 'endDate': str(last)}
        suffix = f'{cursor}_{last}'
        collect('sleep_' + suffix, '/sleep-service/sleep/dailySleepSummariesByDate', query)
        collect('hrv_' + suffix, f'/hrv-service/hrv/daily/{cursor}/{last}')
        collect('body_battery_' + suffix, '/wellness-service/wellness/bodyBattery/reports/daily', query)
        cursor = last + dt.timedelta(days=1)
    activities = []
    try:
        for offset in range(0, 10000, 99):
            page = get('/activitylist-service/activities/search/activities',
                       {'startDate': str(start), 'endDate': str(end), 'start': offset,
                        'limit': 99, 'sortOrder': 'desc'})
            if not isinstance(page, list):
                raise SafeError('Unexpected activities response; pagination stopped.')
            activities.extend(page)
            if len(page) < 99:
                break
        else:
            result['errors']['activities'] = 'Activity safety limit reached; results may be incomplete.'
    except SafeError as exc:
        result['errors']['activities'] = str(exc)
    result['data']['activities'] = activities
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('init', help='Save a Personal API key through a hidden local prompt')
    commands.add_parser('check', help='Verify authentication without displaying credentials')
    snap = commands.add_parser('snapshot', help='Fetch wellness and all activities for a date range')
    snap.add_argument('--days', type=int, default=28)
    snap.add_argument('--end', default=str(dt.datetime.now(dt.timezone.utc).date()))
    activity = commands.add_parser('activity', help='Fetch one activity, including its split summary')
    activity.add_argument('id', type=int)
    args = parser.parse_args()
    if args.command == 'init':
        if not sys.stdin.isatty():
            raise SafeError('Run init yourself in an interactive terminal; do not pass a key on the command line.')
        key = getpass.getpass('Garmin Personal API key (hidden): ').strip()
        if not key or any(c.isspace() for c in key):
            raise SafeError('Key must be nonempty and contain no whitespace.')
        private_write(STATE / 'api-key', key + '\n')
        print('Key saved locally with mode 0600. Run check to verify access.')
        return
    dates = date_range(args.end, args.days) if args.command == 'snapshot' else None
    if args.command == 'activity' and args.id <= 0:
        raise SafeError('Activity ID must be positive.')
    token = access_token()
    if args.command == 'check':
        request('/userprofile-service/userprofile/settings', 'Bearer ' + token)
        print('Garmin Personal API authentication and profile read succeeded.')
    elif args.command == 'activity':
        print(json.dumps(request(f'/activity-service/activity/{args.id}', 'Bearer ' + token), indent=2))
    else:
        result = snapshot(token, *dates)
        path = STATE / f'snapshot-{dates[0]}-{dates[1]}.json'
        private_write(path, json.dumps(result, indent=2) + '\n')
        print(f'Saved {path}; {len(result["data"])} data categories, {len(result["errors"])} errors.')
        if result['errors']:
            print(json.dumps(result['errors'], indent=2))
            raise SystemExit(1)


if __name__ == '__main__':
    try:
        main()
    except (SafeError, OSError) as exc:
        print(str(exc) if isinstance(exc, SafeError) else 'Local file operation failed; check permissions.', file=sys.stderr)
        raise SystemExit(1)
