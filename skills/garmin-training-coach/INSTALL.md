# Install Garmin Training Coach in Codex

You need Codex on Linux, macOS, or WSL, with Python 3.11+, pip, Git, and
internet access. Codex will check these during setup.

## 1. Download and ask Codex to install

Download `agensi-garmin-training-coach.zip` to the computer where Codex runs.
If Agensi has already installed the skill, skip to step 2.

Open Codex in the project where you want to use Garmin. Send this message,
replacing the ZIP path with the location of your download:

> Install Garmin Training Coach from the ZIP at <path to downloaded ZIP> into
> this project's .agents/skills/garmin-training-coach directory. Keep all its
> references together. Read its SKILL.md and follow references/codex-setup.md
> to set up Garmin. Handle the connector download, Python dependencies, MCP
> registration, and private key-file creation. Show me the exact file where
> I should put my Garmin API key. Do not ask me to paste the key in chat.

Codex should extract the `garmin-training-coach` folder without adding an extra
nested folder. The installed entry point must be:
`.agents/skills/garmin-training-coach/SKILL.md`.

For availability across projects, ask Codex to install the folder under
`~/.agents/skills/garmin-training-coach` instead. Choose one location to avoid
duplicate skills. If Codex cannot see the download, move it into the current
project folder and give Codex that path.

## 2. Ask Codex to prepare Garmin

If step 1 already completed setup, continue to step 3. Otherwise send:

> Use $garmin-training-coach to set up Garmin. Handle installation and MCP
> configuration, and show me the exact local key-file path.

Codex downloads the public Garmin Personal MCP and prepares its local Python
environment and configuration. You do not need to run a setup script or edit
MCP configuration. If a required program is missing, Codex reports the blocker.

## 3. Put your key in the file

Create your key in [Garmin Connect API settings](https://connect.garmin.com/app/settings/personalApiToken).
Garmin displays a new key only once.

Open the exact file Codex shows you in a text editor. Paste only the key into
that file and save it. The usual location is
`~/.codex/garmin-config/api-key`; Codex adjusts this for your environment.
Never paste the key into chat.

Codex creates the file and sets its private permissions during setup. Your only
credential setup action is to fill in that file.

## 4. Restart Codex and use Garmin

Close and reopen Codex in the same project. Ask:

> Use $garmin-training-coach to review my sleep yesterday. State which date
> you checked and whether Garmin returned data. Do not save the results.

A successful data response verifies live Garmin access. A local connection
status check alone does not. If Garmin is absent, ask Codex to check its MCP
registration. If authentication fails, replace the key in the same local file.

## Included in this download

- `SKILL.md`: the training and recovery workflow.
- `references/codex-setup.md`: installation instructions for Codex to follow.
- `INSTALL.md`: this guide.
- `README.md`: capabilities and example requests.

The MCP connector is downloaded separately during setup. This package contains
no credentials. The connector reads Garmin data; it does not create workouts
or sync plans to your watch. Garmin results are shared with your AI client to
answer your questions; review that client's data-handling settings.

Other agent clients require the connector's client-specific setup:
[Garmin Personal MCP](https://github.com/vmindru/garmin-personal-mcp).

Codex skill locations follow the [official OpenAI documentation](https://learn.chatgpt.com/docs/build-skills).
