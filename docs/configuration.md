# Configuration

## Credential location

By default the API client and MCP server use `<repository>/.local/garmin` for
the API key and optional CLI snapshots. The MCP Python environment also lives
under that directory. Paths are resolved from the script location, not Claude's
working directory.

Set `GARMIN_CONFIG_DIR` to an absolute directory to keep credentials and CLI
snapshots elsewhere. It does not move the Python environment:

```bash
export GARMIN_CONFIG_DIR="$HOME/.config/garmin-personal-mcp"
python3 scripts/garmin-personal.py init
python3 scripts/garmin-personal.py check
```

To pass the same directory explicitly to Claude's MCP server:

```bash
claude mcp add --transport stdio --scope local \
  --env "GARMIN_CONFIG_DIR=$GARMIN_CONFIG_DIR" \
  garmin -- "$(pwd)/.local/garmin/mcp-venv/bin/python" \
  -B "$(pwd)/scripts/garmin-mcp.py"
```

The environment variable contains a **directory path**, never the key itself.
When using the default location, omit `--env` entirely.

## Claude Code scopes and verification

The README uses `--scope local`: the server belongs to you in the current
project. `--scope user` makes it available in all your projects for that Claude
identity. `--scope project` writes shared project configuration in `.mcp.json`;
machine-specific absolute paths generally belong in local scope instead.

Run configuration commands from a regular shell, not inside Claude's prompt:

```bash
claude mcp get garmin
claude mcp list
```

Then open Claude Code and use `/mcp` to check its connection. After changing the
launch command or credential-directory environment setting, reconnect or restart
Claude. If the name is already registered, inspect it first and replace that
specific entry:

```bash
claude mcp remove --scope local garmin
```

Re-run the desired `claude mcp add` command. Match the scope used when adding it.

The stdio server must run through its dedicated Python executable. Running
`python3 scripts/garmin-mcp.py` outside that environment may fail to import `mcp`.

## Claude Desktop

For Claude Desktop's local MCP configuration, merge this entry into `mcpServers`
in your existing configuration, replacing `/absolute/path/garmin-personal-mcp`:

```json
{
  "mcpServers": {
    "garmin": {
      "command": "/absolute/path/garmin-personal-mcp/.local/garmin/mcp-venv/bin/python",
      "args": ["-B", "/absolute/path/garmin-personal-mcp/scripts/garmin-mcp.py"]
    }
  }
}
```

If using a custom credential directory, add an `env` object to the `garmin`
entry, for example `"env": {"GARMIN_CONFIG_DIR": "/absolute/path/to/private/garmin"}`.
Do not replace unrelated servers. Restart Claude Desktop after saving.
The Python executable, source, and key must be accessible on the machine running
Claude Desktop; a path only inside a container will not work on the host.

## Codex

From the repository root, register the local server:

```bash
codex mcp add garmin -- "$(pwd)/.local/garmin/mcp-venv/bin/python" \
  -B "$(pwd)/scripts/garmin-mcp.py"
codex mcp get garmin
```

For project-scoped setup, use this in your project's `.codex/config.toml`, with
real absolute paths:

```toml
[mcp_servers.garmin]
command = "/absolute/path/garmin-personal-mcp/.local/garmin/mcp-venv/bin/python"
args = ["-B", "/absolute/path/garmin-personal-mcp/scripts/garmin-mcp.py"]
startup_timeout_sec = 30
tool_timeout_sec = 600

# Optional; omit this table when using the default credential directory.
[mcp_servers.garmin.env]
GARMIN_CONFIG_DIR = "/absolute/path/to/private/garmin"
```

Restart/resume Codex to load the tools and enable/trust project MCP configuration
if the client requests it.

## Containers and rebuilds

Keep the clone and credential directory on persistent host mounts. Installing
into an ephemeral container home loses dependencies when the container is
replaced. The clone-local environment and `.local/garmin/api-key` survive if the
whole clone is mounted persistently. If using `GARMIN_CONFIG_DIR`, mount that
directory too. Keep personal credentials scoped to your personal target.

Use paths valid **inside the client container** for the MCP command. A fresh
image with a different Python version or architecture may require recreating
the environment. Run the installer again before registering the server there.
Existing sessions may keep old server processes until restarted.

## Updating and key rotation

After updating the source, install dependencies again:

```bash
bash scripts/garmin-mcp-setup.bash
```

Restart the MCP connection to use the updated code. If pip reports satisfied
dependencies, the installed versions already meet the declared requirements.

Create a replacement key on Garmin's site and run `init` again, using the same
`GARMIN_CONFIG_DIR` if configured. The server detects key-file replacement and
renews its in-memory access token. Tokens are otherwise renewed before Garmin's
24-hour expiry; individual requests retry once on HTTP 401. Revoke a key on
Garmin's site to revoke its associated access tokens.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `No Garmin key configured` | Run `init`; verify Claude uses the same credential directory |
| Key permissions error | Set the key file to `0600` and its directory to `0700` |
| `No module named mcp` | Run the installer and use the environment's Python executable |
| Server absent in Claude | Check its scope and absolute paths, run `/mcp`, reconnect/restart |
| HTTP 401 | Check key expiry/revocation; replace it using `init` |
| HTTP 403 | Check whether your Garmin account has Personal API access |
| HTTP 406 during token exchange | Use this client's `Accept: */*` handling; Garmin can return plain text |
| HTTP 429 | Wait before retrying; avoid repeated large snapshot calls |
| Empty health records | Sync your device; specify a completed local calendar date |
| Snapshot has `errors` | Treat it as partial data; retry only the affected metric when possible |
| Large output or slow response | Request one metric, a shorter snapshot, or paginated activities |

No tools write workouts or plans to your watch. Training suggestions remain
advice in your Claude conversation; account mutations are outside this server.
