# Security review

Reviewed: 2026-11-23. The review assessed the scanner's installer, skill
instructions, Python code, dependencies, report schema and tests against its
documented intent and relevant OWASP and MAESTRO guidance.

| Severity | Finding | Confidence |
| --- | --- | --- |
| Medium | Unpinned dependencies permit compromised releases | 8/10 |

## Unpinned dependencies permit compromised releases

**Location:** [requirements.txt](.github/skills/agentic-ai-security-scanner/requirements.txt)

The installer accepts future releases of direct and transitive dependencies
without verifying artifact hashes. If a package release or its source is
compromised, installation or subsequent imports may run attacker-controlled
code with the user's privileges, beyond the scanner's intended reporting and
reference-update behavior. Exploitation depends on a supply-chain compromise;
no compromised release was identified in this review.

```text
reportlab>=4.2,<5
pypdf>=5,<7
fonttools>=4,<5
```

**Recommendation:** Lock reviewed direct and transitive dependencies to exact
versions and hashes, enable hash verification during installation, and consider
a controlled package mirror.

**Reference:** [OWASP Agentic Skills Top 10: AST02 Supply Chain Compromise](https://owasp.github.io/www-project-agentic-skills-top-10/ast02.html).

## Limitations

The security review did not execute target code or tests. Deployment permissions
and package-index configuration were unavailable. One official OWASP webpage was
accessed to verify the reference; the review otherwise used local snapshots. The
review model's version was not exposed by the host. A review does not guarantee
that other vulnerabilities are absent.
