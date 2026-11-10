# Garmin Personal MCP

A local, read-only MCP server for your Garmin Connect activities and health
metrics. Ask Claude about your recent training, sleep, HRV, resting heart rate,
stress, and Body Battery using Garmin's **official Personal API**.

The server runs on your machine over stdio. It needs no public URL, hosted
service, Garmin password, or Garmin developer partnership. An API key generated
in your own Garmin Connect account is required. This project is independent
of Garmin and Anthropic.

## Requirements

- Linux or macOS with Bash, Python **3.11+**, and pip 22.3+.
- Claude Code installed and signed in.
- A Garmin Connect account with access to Personal API key creation.
- Internet access to Garmin and, during installation, PyPI.

Windows users can follow these commands in WSL with Claude Code installed there.
These instructions target **Claude Code**, the terminal client. See
[configuration](docs/configuration.md) for Claude Desktop and Codex examples.

## Install

Clone this repository, then run these commands from its root directory:

```bash
cd /path/to/garmin-personal-mcp
bash scripts/garmin-mcp-setup.bash
```

The installer creates `.local/garmin/mcp-venv` and installs the official Python
MCP SDK there. It does not change your system Python packages or register a
connection in Claude automatically.

Create a key in [Garmin Connect Personal API settings](https://connect.garmin.com/app/settings/personalApiToken).
Choose an expiry, copy the key, then enter it at the hidden terminal prompt:

```bash
python3 scripts/garmin-personal.py init
python3 scripts/garmin-personal.py check
```

The key is saved in `.local/garmin/api-key` with permissions `0600` inside a
`0700` directory. Do not paste it into Claude, shell command arguments, or Git.
See [configuration](docs/configuration.md) to keep credentials outside the clone.

## Connect Claude Code

From this repository's root, run:

```bash
claude mcp add --transport stdio --scope local garmin -- \
  "$(pwd)/.local/garmin/mcp-venv/bin/python" \
  -B "$(pwd)/scripts/garmin-mcp.py"

claude mcp get garmin
```

`--scope local` makes this connection available only to you in the current
project. Use `--scope user` instead if you want it available across your personal
Claude Code projects. Run the command on the same machine or inside the same
container where Claude runs and where these paths exist.

Start or restart Claude Code from the project, run `/mcp`, and check that `garmin`
is connected. If Claude asks for permission to use the tools, review and allow
the reads you want.

## Basic usage

Ask Claude naturally:

> Fetch my Garmin sleep, HRV, resting heart rate, and Body Battery for today.

> Review my last 28 days of activities and recovery. Include cycling and strength
> sessions when assessing my running workload.

> Suggest next week's running plan based on my Garmin data. Ask about my goals,
> available days, fatigue, and any pain before making assumptions.

> Show my latest run's pace, heart rate, and split summary.

Claude can call these tools on demand:

| Tool | What it does |
| --- | --- |
| `garmin_connection_status` | Checks local key availability and permissions; does not test live access |
| `garmin_health_stats` | Fetches one metric for a date: `daily_summary`, `sleep`, `hrv`, `body_battery`, `heart_rate`, or `heart_rate_zones` |
| `garmin_list_activities` | Fetches a page of activities across all sports, newest first |
| `garmin_activity` | Fetches activity details, measurements, and Garmin's split summary |
| `garmin_training_snapshot` | Fetches health metrics and activities together; defaults to 7 days |

Use `days: 28` for an initial training baseline; date ranges support up to 90
days. Dates are `YYYY-MM-DD` and default to **today UTC**. Specify the date when
your local calendar differs. Sleep belongs to the morning it ends.

## Data handling and limits

- Data reads go directly to `personal.connectapi.garmin.com`. The MCP server
  opens no listening port and does not send telemetry or data to a separate
  service. Tool responses become available to the AI client you connect.
- The server never modifies Garmin workouts, calendars, profile, or health
  records. Its only POST exchanges your API key for an access token.
- API keys stay in a local file; access tokens are held only in memory.
  The MCP does not save health snapshots to disk.
- `.gitignore` excludes local credentials, dependencies, and CLI snapshots.
- Missing fields depend on your device and recorded data. Partial snapshot
  failures appear in `errors`; they are not proof that you are recovered.
- Garmin's published Personal API currently has no Training Readiness or
  Training Status endpoints. The server does not invent those scores.

## Optional CLI and tests

The API client also works without MCP, using only Python's standard library:

```bash
python3 scripts/garmin-personal.py snapshot --days 28
python3 scripts/garmin-personal.py activity ACTIVITY_ID
```

Replace `ACTIVITY_ID` with a positive numeric ID from your activity list.
CLI snapshots are saved under `.local/garmin/` with permissions `0600`.

Run the offline test suite:

```bash
.local/garmin/mcp-venv/bin/python -B -m unittest discover -s tests -p 'test_garmin*.py'
```

For key rotation, container persistence, updating, client configuration, and
troubleshooting, see [configuration](docs/configuration.md).

## References

- [Garmin Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api/)
- [Garmin Personal API FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq/)
- [Garmin endpoint documentation](https://developer.garmin.com/gc-developer-program/personal/swagger-docs/)
- [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp)
- [Official Python MCP SDK](https://py.sdk.modelcontextprotocol.io/)

## License

The code, skill instructions, and documentation are licensed under the
[MIT License](LICENSE). Copyright (c) 2026 Veaceslav Mindru.
