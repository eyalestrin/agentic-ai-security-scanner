# Security review

Reviewed: 2026-11-23. The review assessed the report-only scanner's installer,
skill instructions, Python code, dependencies, and local OWASP and MAESTRO
guidance against its documented intent.

| Severity | Finding | Confidence |
| --- | --- | --- |
| High | Dependencies lack immutable version and artifact verification | 8/10 |
| Medium | Reference updates lack immutable provenance and integrity verification | 9/10 |

## Dependencies lack immutable version and artifact verification

**Location:** [requirements.txt](.github/skills/agentic-ai-security-scanner/requirements.txt)

The installer accepts compatible future dependency releases and does not verify
artifact hashes. If a dependency maintainer, package index, or distribution
infrastructure is compromised, malicious package code could execute with the
installing user's privileges. This exceeds the intended installation of report
dependencies. Exploitation depends on a supply-chain compromise; no malicious
release was identified.

```text
reportlab>=4.2,<5
pypdf>=5,<7
fonttools>=4,<5
```

**Recommendation:** Pin reviewed direct and transitive dependencies to exact
versions and SHA-256 hashes, install using `pip --require-hashes`, and consider a
controlled package mirror.

**References:**

- [OWASP Agentic Skills Top 10: AST02 Supply Chain Compromise](https://owasp.github.io/www-project-agentic-skills-top-10/ast02.html)
- [OWASP MCP Security Cheat Sheet: Supply Chain Security](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html#9-supply-chain-security)
- [CSA MAESTRO threat modeling framework](https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro)

## Reference updates lack immutable provenance and integrity verification

**Location:** [scanner.py](.github/skills/agentic-ai-security-scanner/scanner.py)

The updater retrieves mutable upstream branches and a PDF selected from the OWASP
landing page without pinning a revision or verifying a separately maintained
digest. An attacker who compromises an upstream source or hosting account could
alter the local guidance when a user requests an update, potentially influencing
subsequent review findings and recommendations. This exceeds the intent of
maintaining trustworthy reference snapshots. The attack depends on an upstream
compromise; none was identified.

```python
CHEATS = "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/"
AST = "https://raw.githubusercontent.com/OWASP/www-project-agentic-skills-top-10/main/"
ASI_PAGE = "https://genai.owasp.org/top-10-for-agentic-applications-2026/"
```

**Recommendation:** Review and pin upstream revisions or release artifact hashes,
verify downloaded content against separately maintained digests, and require
explicit review of unexpected source changes before replacement.

**References:**

- [OWASP Agentic Skills Top 10: AST02 Supply Chain Compromise](https://owasp.github.io/www-project-agentic-skills-top-10/ast02.html)
- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
- [CSA MAESTRO threat modeling framework](https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro)

## Limitations

The review was static: target code was not executed, and no online documents
were fetched. Registry compromise controls, infrastructure permissions, and
deployment isolation were unavailable. The review model's version was not
exposed by the host. A review does not guarantee that other vulnerabilities
are absent.
