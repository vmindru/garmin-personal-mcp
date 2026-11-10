# Agensi listing draft

**Title:** Garmin Training Coach

**Short description:** Turn your live Garmin Connect training and recovery data
into a clear weekly review, activity analysis, or sensible next-session
suggestion.

**Full description:** Garmin Training Coach reads your recent Garmin activities,
sleep, HRV, heart rate, and other available wellness metrics through the
local Garmin Personal MCP. It checks dates, missing data, units,
partial days, and cross-training before summarizing the evidence and suggesting
practical next steps. It distinguishes Garmin measurements from calculations
and coaching judgment, and explains uncertainty instead of inventing a single
readiness score.

**Setup in Codex:** Install the skill and ask it to set up Garmin. Codex
handles downloading the connector, installing dependencies, and registering the
MCP. Create your own Garmin Personal API key in [Garmin Connect API settings](https://connect.garmin.com/app/settings/personalApiToken),
put it in the exact local file Codex shows you, and restart Codex. Never paste
the key into chat. Requires Linux, macOS, or WSL with Python 3.11+, pip, Git,
and internet access. Other clients use the connector's client-specific setup.
The package includes the skill and Codex setup instructions; it downloads the
MCP server separately and contains no Garmin credentials.

The skill uses Garmin data in the current conversation and does not store it in a separate memory service. Your connected AI client receives tool results; review its data-handling policy. The skill does not alter Garmin records or sync workouts to your watch. It is not medical advice.

**Suggested launch price:** $5 one-time, then revisit after buyer feedback and
conversion data. Review pricing after buyers complete the assisted setup successfully.

**Tags:** Garmin, running, fitness, training, recovery, MCP
