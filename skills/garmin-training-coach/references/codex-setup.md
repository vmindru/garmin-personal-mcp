# Set up Garmin in Codex

Use this procedure when the user requests installation or repair. It supports
Linux, macOS, and WSL with Python 3.11+, pip, Git, and network access. On an
unsupported environment or missing prerequisite, explain the specific blocker.
Do not claim installation succeeded until its non-secret configuration checks
pass. This procedure does not require a separate launcher or a setup Bash script.

## Resolve paths for this user

Resolve the active Codex home from `CODEX_HOME` if set; otherwise use
`Path.home() / ".codex"`. Use a task-specific variable for that resolved path;
do not reassign `HOME` or `CODEX_HOME`.

Default locations relative to that Codex home:

- Connector source: `garmin-mcp/`
- Python environment: `garmin-mcp/.local/garmin/mcp-venv/`
- Credential directory: `garmin-config/`
- Key file: `garmin-config/api-key`
- MCP configuration: `config.toml`

For a standard installation, the user's key file is
`~/.codex/garmin-config/api-key`. With a custom Codex home, resolve its equivalent
and show the actual absolute path. All server paths must work on the machine
or in the container where Codex runs. If the host and container expose different
paths, show a verified host path for the user; never guess a host mapping.

Inspect only the active user's Garmin MCP configuration, without displaying
unrelated configuration or secret values. Reuse an existing valid Garmin
installation and credential-directory setting rather than silently moving its
key. Do not inspect other client profiles or copy credentials from them.

## Prepare the connector

1. If the server source is absent, clone the public repository
   `https://github.com/vmindru/garmin-personal-mcp` to the resolved connector
   directory. Follow applicable local repository-access rules. Do not borrow
   GitHub credentials, replace an occupied directory, or overwrite local edits.
2. Check for `scripts/garmin-mcp.py` and
   `scripts/garmin-mcp-requirements.txt`. Use Python 3.11+ to create
   `.local/garmin/mcp-venv` inside that source directory. Install the requirements
   using that environment's `python -m pip install -r` command. Install no
   packages globally. Resolve the environment's actual Python executable.
3. Create the credential directory with mode `0700`. Create an empty `api-key`
   file with mode `0600` only if it does not already exist. Preserve an existing
   key. Check existence, size, and permissions through file metadata; do not
   read or print the key. Correct private permissions when necessary.
4. Add or repair only the Garmin MCP entry in the active Codex configuration.
   Parse existing TOML before editing and preserve unrelated settings. Never
   append duplicate Garmin tables. Use the resolved absolute paths in this
   template; placeholders and `~` must not remain in executable paths:

   ```toml
   [mcp_servers.garmin]
   command = "/absolute/connector/.local/garmin/mcp-venv/bin/python"
   args = ["-B", "/absolute/connector/scripts/garmin-mcp.py"]
   startup_timeout_sec = 30
   tool_timeout_sec = 600

   [mcp_servers.garmin.env]
   GARMIN_CONFIG_DIR = "/absolute/codex-home/garmin-config"
   ```

   The environment setting is a directory path, never an API key. Validate
   the resulting TOML and check that the configured executable and server
   script exist. Do not change the user's sign-in or configure memory services.

## User's one credential step

After completing setup, show this short instruction, substituting the exact
resolved file path:

> Create your key in [Garmin Connect API settings](https://connect.garmin.com/app/settings/personalApiToken).
> Open **<absolute path to api-key>**, paste only the key, and save the file.
> Keep the key out of this chat. Restart Codex, then ask me a Garmin question.

Do not ask the user to run install commands or manually edit MCP configuration.
Do not request their key in chat, command arguments, or an environment variable.
Creating the file and setting its permissions are the agent's setup work;
the user only fills it in. Garmin displays a newly created key only once.

## Verify after restart

Discover the Garmin tools and call `garmin_connection_status` when the user
asks to check setup. It checks local key configuration without contacting Garmin;
report live account access as unverified. A successful requested Garmin data
query is the live-access check. Do not fetch personal data just to finish setup.
If authentication fails, ask the user to replace the key in the same local file.
Never copy it into diagnostics or output.

Codex configuration sources: [MCP configuration](https://learn.chatgpt.com/docs/extend/mcp)
and [Codex home](https://learn.chatgpt.com/docs/config-file/environment-variables).
