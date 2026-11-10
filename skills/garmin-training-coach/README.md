# Garmin Training Coach

A portable agent skill for reviewing a user's current Garmin Connect training
and recovery data and turning it into a cautious, practical recommendation.

## Set up in Codex

Start with [INSTALL.md](INSTALL.md) for the download-to-first-query walkthrough.

Install this skill into Codex, then ask:

> Use $garmin-training-coach to set up Garmin.

Codex downloads the Garmin Personal MCP, prepares its Python environment,
registers the MCP, and creates a private key file. You only need to create a key
in [Garmin Connect API settings](https://connect.garmin.com/app/settings/personalApiToken),
put it in the exact file Codex shows you, and restart Codex. Never paste the key
into chat. Garmin displays a new key only once.

The default key location is `~/.codex/garmin-config/api-key`. If you use a
custom `CODEX_HOME` or an existing Garmin installation, Codex shows the matching
path for your environment. No personal launcher or fixed username is required.

Setup requires Linux, macOS, or WSL, Python 3.11+, pip, Git, and internet access.
Codex reports any missing prerequisite. The skill contains installation
instructions; connector code is downloaded separately from the public
[Garmin Personal MCP repository](https://github.com/vmindru/garmin-personal-mcp).
For other agent clients, use that repository's client-specific setup guide.

After restarting, ask:

> Use $garmin-training-coach to review my sleep yesterday.

A successful Garmin data response verifies live access. The local connection
status check alone does not verify your account.

The Garmin Personal MCP is a local, read-only server. It fetches data from the
user's Garmin Connect account and exposes tool results to the connected AI
client. This skill does not save Garmin data to a separate memory store or
forward it to another integration. Review the AI client's data-handling
settings and policies. A training plan is advice in the conversation; it is not
written to Garmin or synced to a watch.

## What it helps with

- Summarizing recent running and cross-training load.
- Reviewing sleep, HRV, resting heart rate, stress, and Body Battery alongside
  user-reported fatigue.
- Explaining an individual activity and its available split summary.
- Suggesting a session or a practical short-term plan with stated assumptions.

It does not provide medical diagnosis, injury treatment, Garmin Training
Readiness or Training Status scores, or guaranteed lifetime personal-best
searches.

## Example requests

- “Review my last four weeks of Garmin training and suggest what to focus on
  next week.”
- “Look at my sleep, HRV, and recent runs before suggesting today's session.”
- “Summarize this Garmin activity and explain the pacing.”

See `SKILL.md` for the full behavior and data-handling rules.

## License

Licensed under the [MIT License](LICENSE), including the skill and its documentation.
