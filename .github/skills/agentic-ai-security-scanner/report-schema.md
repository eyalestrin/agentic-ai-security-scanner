# Findings JSON

Provide a UTF-8 JSON object with the following shape. All strings must be nonempty,
except `description`, which may be empty when unknown. `findings` may be empty.
Use absolute paths and 1-based line numbers. Reference URLs must be HTTPS links to
the relevant official OWASP or CSA page, ideally a specific category or section.
Provide a `coverage` explanation even when no risks are found.

```json
{
  "name": "Example agent",
  "description": "Answers support questions",
  "languages": ["Python"],
  "model": "Vendor model name and version or Unknown (not exposed by the host)",
  "intent": "Read support documents and draft answers without changing data",
  "coverage": "Reviewed agent.py and tools.py; deployment permissions unavailable.",
  "findings": [
    {
      "severity": "High",
      "file": "/absolute/path/to/agent.py",
      "line": 42,
      "title": "Untrusted text can drive a privileged action",
      "description": "Describe the reachable attack path, impact, and why this exceeds the intent.",
      "snippet": "relevant code, with any secrets redacted",
      "recommendation": "Describe an actionable fix.",
      "references": [
        {
          "title": "Relevant official guidance",
          "url": "https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html#tool-security-and-least-privilege"
        }
      ]
    }
  ]
}
```

The example URL is illustrative: use anchors actually present in the applicable
source. On Windows use JSON-escaped backslashes or absolute forward-slash paths.
