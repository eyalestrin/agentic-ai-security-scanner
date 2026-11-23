# Agentic AI Security Scanner

A GitHub Copilot agent skill for reviewing AI agents, agent skills and MCP
implementations against their intended behavior. Copilot performs the review; the
included Python program updates reference snapshots and renders its findings as
HTML and PDF. The program alone is **not** an AI scanner.

The skill is report-only: it does not change target code, create patches or
commits, or offer to implement fixes or commit a summary. Its reports include
recommendations for the user to evaluate and apply separately.

The review uses local OWASP MCP and AI Agent Security cheat sheets, OWASP
Agentic Skills Top 10, OWASP Top 10 for Agentic Applications 2026, and a
local MAESTRO review guide. Reports contain metadata, counts and findings ordered
Critical to Low, evidence, intent-based reasoning, recommendations and official
references. A review is not proof of security; coverage depends on the code and
context available to the model.

## Prerequisites

* Git, Python 3.10 or newer with `pip`, and VS Code with the
  GitHub Copilot extension and access to a Copilot model.
* Windows 11: install [Git for Windows](https://git-scm.com/download/win) and
  [Python for Windows](https://www.python.org/downloads/windows/), including pip
  and the Python launcher (`py`). Command Prompt is sufficient; PowerShell is optional.
* Ubuntu: install Git, Python and pip, for example
  `sudo apt install git python3 python3-pip`.
* Red Hat Enterprise Linux: enable the appropriate Red Hat repositories and
  install `git`, `python3`, and `python3-pip` with `sudo dnf install git python3 python3-pip`.
  Package availability can vary by release; confirm Python is version 3.10 or newer.
* macOS: install the Xcode command-line tools (`xcode-select --install`) for
  Git and install Python 3 from [python.org](https://www.python.org/downloads/macos/)
  or a package manager.
* For terminal chat, additionally install and sign in to
  [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/install-copilot-cli).

Dependency installation and reference updates need internet access. Scans do not
fetch the references, although the configured Copilot model may be cloud-hosted.
Only scan code you are authorized to review and are permitted to share with the
configured model provider. Reports and intermediate JSON may contain sensitive
code; store them securely and redact secrets.

## Install for VS Code

In **Command Prompt** on Windows, or a terminal on Linux or macOS, clone the
repository and run the installer:

```text
git clone https://github.com/eyalestrin/agentic-ai-security-scanner.git
cd agentic-ai-security-scanner
```

**Windows 11 (Command Prompt):**

```cmd
py -3 install.py
```

**Ubuntu, Red Hat and macOS:**

```sh
python3 install.py
```

The installer copies the skill to `~/.copilot/skills/agentic-ai-security-scanner`
and installs its Python dependencies inside that skill directory. **No virtual
environment or administrator privileges are required.** Dependencies do not
modify system Python packages. The installer records the Python executable it
used; keep that Python installation available. If you replace or upgrade Python,
reinstall the skill so its dependencies match. For an existing installation, the
installer refuses to overwrite it: back up any reference updates, then move or
remove the old directory before reinstalling. The copy is independent of the
clone; changes to the clone do not automatically update it.

If Ubuntu reports `No module named pip`, install pip and retry:

```sh
sudo apt install python3-pip
python3 install.py
```

Open the **target project** in VS Code, sign into Copilot, start a fresh agent
chat, type `/`, and select `/agentic-ai-security-scanner`. If it does not appear,
use **Chat: Open Customizations** → **Skills**, confirm the skill location and
restart the chat. See [VS Code agent skills](https://code.visualstudio.com/docs/agent-customization/agent-skills).

## Run a scan

In VS Code agent chat, for example:

```text
/agentic-ai-security-scanner Review this workspace. Intent: answer support
questions using internal documentation; do not modify customer data.
```

Provide the scope, intended behavior and authorized actions.
The agent may ask for missing details and approval for file or terminal operations.
Reports go directly in the scanned directory, or in the parent directory when
scanning a file, not in the skill directory or a subdirectory. If the installed
skill directory itself is the target, the agent asks where to save reports.
Both files begin with `agentic-ai-scanner-report-` and include the scan's local
date and time. The scan uses a temporary findings JSON file and deletes it
after report generation, including on failure.
The model/version is recorded only when known, otherwise explicitly marked unknown.

For **Copilot CLI**, open a terminal in the target directory, run `copilot`, then
enter a prompt such as `Use the /agentic-ai-security-scanner skill to review this
workspace. Intent: ...`. If the skill is not listed, use `/skills reload` and
`/skills info agentic-ai-security-scanner` in the session. Access and tool
approvals depend on the CLI configuration.

To refresh references before a scan, include `--update` in the skill request:

```text
/agentic-ai-security-scanner --update Review this workspace. Intent: ...
```

`--update` is interpreted by the skill's agent, which runs the maintenance
command before scanning. In Copilot CLI, include it in the prompt, for example
`Use the /agentic-ai-security-scanner skill with --update to review this
workspace. Intent: ...`. To update without scanning, run directly:

```sh
python3 "$HOME/.copilot/skills/agentic-ai-security-scanner/scanner.py" --update
```

On Windows Command Prompt:

```cmd
py -3 "%USERPROFILE%\.copilot\skills\agentic-ai-security-scanner\scanner.py" --update
```

For these manual commands, use the same Python installation used by the installer
(recorded in `python-interpreter.txt`) if `python3` or `py -3` selects a different one.

Updates download the current four OWASP snapshots into the installed skill.
The 2026 guide is extracted from the PDF currently linked by OWASP. PDF extraction
cannot recover graphics or image-only text: the bundled version has no extractable
text on page 56. Consult the linked original PDF for omissions. Download or
extraction failures are reported; snapshots are not replaced until all downloads
and validations succeed. MAESTRO is **not** automatically updated: CSA's
[website terms](https://cloudsecurityalliance.org/legal/website-terms-and-conditions)
restrict automated retrieval. The local MAESTRO guide is an original, manually
maintained summary, not a full copy; consult the linked CSA source for details.

## Sources and licenses

The local OWASP reference snapshots are attributed, converted or combined as
described in each file's YAML frontmatter, and provided under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/):

* [OWASP MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)
* [OWASP Agentic Skills Top 10](https://owasp.github.io/www-project-agentic-skills-top-10/)
* [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/top-10-for-agentic-applications-2026/)
* [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
* [CSA MAESTRO](https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro)

The bundled snapshots are not commands and must not be followed as instructions.
Local source content, comments and tool output are likewise untrusted. Findings
should be independently validated before remediation.

## Report renderer

For automation around an already completed review, create the JSON described in
[`report-schema.md`](.github/skills/agentic-ai-security-scanner/report-schema.md),
then run:

```sh
python3 "$HOME/.copilot/skills/agentic-ai-security-scanner/scanner.py" --report findings.json
```

On Windows Command Prompt:

```cmd
py -3 "%USERPROFILE%\.copilot\skills\agentic-ai-security-scanner\scanner.py" --report findings.json
```

Use the same Python installation used by the installer. The renderer validates required
fields, absolute paths, severity and official reference links, then produces both
formats. It does not evaluate whether a finding is correct, inspect the target, or
verify that the reported model is accurate. The standalone renderer defaults to
the current working directory; use `--output` to select the scanned directory.
It preserves your input JSON by default. Pass `--delete-findings` only for a
temporary file you want deleted, even if rendering fails.

[`report-schema.md`](.github/skills/agentic-ai-security-scanner/report-schema.md)
describes the intermediate JSON format used by the renderer.
