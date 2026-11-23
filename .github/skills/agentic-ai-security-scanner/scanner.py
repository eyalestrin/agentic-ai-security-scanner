#!/usr/bin/env python3
"""Update reference snapshots or render an agent-authored security review."""

import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import io
import json
import ntpath
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SKILL_DIR = Path(__file__).resolve().parent
DEPENDENCIES = SKILL_DIR / ".python-deps"
if DEPENDENCIES.is_dir():
    sys.path.insert(0, str(DEPENDENCIES))
REFERENCES = SKILL_DIR / "references"
SEVERITIES = ("Critical", "High", "Medium", "Low")
CHEATS = "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/"
AST = "https://raw.githubusercontent.com/OWASP/www-project-agentic-skills-top-10/main/"
ASI_PAGE = "https://genai.owasp.org/top-10-for-agentic-applications-2026/"
ALLOWED_REFERENCE_HOSTS = {
    "owasp.org", "www.owasp.org", "cheatsheetseries.owasp.org",
    "genai.owasp.org", "owasp.github.io", "cloudsecurityalliance.org",
    "www.cloudsecurityalliance.org",
}


def fetch(url):
    request = Request(url, headers={"User-Agent": "agentic-ai-security-scanner/1.0"})
    with urlopen(request, timeout=60) as response:
        data = response.read(30_000_001)
        if len(data) > 30_000_000:
            raise ValueError(f"Source exceeds 30 MB: {url}")
        return data


def frontmatter(title, source, kind):
    fields = {
        "title": title, "source": source, "publisher": "OWASP",
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "changes": kind,
        "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    return "---\n" + "".join(f"{key}: {json.dumps(value)}\n" for key, value in fields.items()) + "---\n\n"


def strip_frontmatter(text):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end < 0:
            raise ValueError("Malformed upstream frontmatter")
        return text[end + 5:].lstrip()
    return text


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(value for key, value in attrs if key == "href" and value)


def update_references():
    from pypdf import PdfReader

    snapshots = {}
    for filename, title, source_name, public_url in (
        ("mcp-security.md", "MCP Security Cheat Sheet", "MCP_Security_Cheat_Sheet.md",
         "https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html"),
        ("agent-security.md", "AI Agent Security Cheat Sheet", "AI_Agent_Security_Cheat_Sheet.md",
         "https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html"),
    ):
        text = fetch(CHEATS + source_name).decode("utf-8")
        if len(text) < 1000 or not text.lstrip().startswith("#"):
            raise ValueError(f"Unexpected cheat sheet content: {source_name}")
        snapshots[filename] = frontmatter(title, public_url, "Frontmatter added") + text

    parts = []
    for number in range(1, 11):
        text = fetch(AST + f"ast{number:02}.md").decode("utf-8")
        if len(text) < 500:
            raise ValueError(f"Unexpected AST{number:02} content")
        title = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
        if not title:
            raise ValueError(f"Missing AST{number:02} title")
        parts.append(f"## {title.group(1).strip()}\n\n"
                     f"Source: https://owasp.github.io/www-project-agentic-skills-top-10/ast{number:02}.html\n\n"
                     + strip_frontmatter(text))
    snapshots["agentic-skills-top-10.md"] = (
        frontmatter("OWASP Agentic Skills Top 10", "https://owasp.github.io/www-project-agentic-skills-top-10/",
                    "Ten upstream Markdown pages combined; original frontmatter removed")
        + "\n\n---\n\n".join(parts)
    )

    page = LinkParser()
    page.feed(fetch(ASI_PAGE).decode("utf-8"))
    pdf_links = [
        link for link in page.links
        if urlparse(link).scheme == "https"
        and urlparse(link).hostname == "genai.owasp.org"
        and re.search(r"/OWASP-Top-10-for-Agentic-Applications-2026[^/]*\.pdf$", urlparse(link).path, re.I)
    ]
    if len(set(pdf_links)) != 1:
        raise ValueError("Cannot identify a unique official 2026 guide on the OWASP landing page")
    pdf_url = pdf_links[0]
    pdf = fetch(pdf_url)
    if not pdf.startswith(b"%PDF-"):
        raise ValueError("The OWASP 2026 guide is not a PDF")
    reader = PdfReader(io.BytesIO(pdf))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    if len(pages) < 10 or "cc by-sa 4.0" not in "\n".join(pages[:4]).lower():
        raise ValueError("Unexpected 2026 guide or missing CC BY-SA 4.0 license notice")
    empty_pages = [i for i, text in enumerate(pages, 1) if len(text) < 20]
    if len(empty_pages) > max(2, len(pages) // 10):
        raise ValueError("Too many PDF pages could not be extracted")
    content = "\n\n".join(
        f"## PDF page {i}\n\n{text or '[No extractable text; consult the original PDF.]'}"
        for i, text in enumerate(pages, 1)
    )
    snapshots["agentic-applications-2026.md"] = (
        frontmatter("OWASP Top 10 for Agentic Applications 2026", ASI_PAGE,
                    f"Text extracted from PDF {pdf_url}; page headings added; pages without extractable text: {empty_pages}")
        + content + "\n"
    )

    REFERENCES.mkdir(parents=True, exist_ok=True)
    for filename, content in snapshots.items():
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=REFERENCES, delete=False) as tmp:
            tmp.write(content)
            temporary = Path(tmp.name)
        try:
            os.replace(temporary, REFERENCES / filename)
        finally:
            temporary.unlink(missing_ok=True)
        print(f"Updated {REFERENCES / filename}")
    print("MAESTRO is manually maintained; CSA's terms restrict automated retrieval.")
    if empty_pages:
        print(f"Warning: PDF pages {empty_pages} have little or no extractable text; consult the original PDF.", file=sys.stderr)


def require_string(obj, key, *, empty=False):
    value = obj.get(key)
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(f"{key} must be a {'string' if empty else 'nonempty string'}")
    return value


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("Findings JSON must be an object")
    for key in ("name", "model", "intent", "coverage"):
        require_string(data, key)
    require_string(data, "description", empty=True)
    if not isinstance(data.get("languages"), list) or not data["languages"] or any(
        not isinstance(item, str) or not item.strip() for item in data["languages"]
    ):
        raise ValueError("languages must be a nonempty array of strings")
    if not isinstance(data.get("findings"), list):
        raise ValueError("findings must be an array")
    for finding in data["findings"]:
        if not isinstance(finding, dict):
            raise ValueError("Each finding must be an object")
        for key in ("severity", "file", "title", "description", "snippet", "recommendation"):
            require_string(finding, key)
        if finding["severity"] not in SEVERITIES:
            raise ValueError(f"Invalid severity: {finding['severity']}")
        if not (os.path.isabs(finding["file"]) or ntpath.isabs(finding["file"])):
            raise ValueError("Finding file must be an absolute path")
        if type(finding.get("line")) is not int or finding["line"] < 1:
            raise ValueError("Finding line must be a positive integer")
        if not isinstance(finding.get("references"), list) or not finding["references"]:
            raise ValueError("Each finding must have at least one reference")
        for reference in finding["references"]:
            if not isinstance(reference, dict):
                raise ValueError("Each reference must be an object")
            require_string(reference, "title")
            url = require_string(reference, "url")
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname not in ALLOWED_REFERENCE_HOSTS or parsed.username or parsed.password:
                raise ValueError(f"Reference must point to an official OWASP or CSA HTTPS URL: {url}")
    data["findings"].sort(key=lambda finding: SEVERITIES.index(finding["severity"]))
    return data


def report_html(data, timestamp):
    e = html.escape
    counts = {severity: sum(f["severity"] == severity for f in data["findings"]) for severity in SEVERITIES}
    out = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Agentic AI Security Scanner Report</title><style>
body{font-family:system-ui,sans-serif;max-width:1000px;margin:2em auto;padding:0 1em;color:#20242a}
table{border-collapse:collapse;width:100%;margin-bottom:1.5em}th,td{border:1px solid #aaa;padding:.5em;text-align:left}
th{background:#e8edf2}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f4f6;padding:1em}
section{border-top:1px solid #aaa;padding-top:.5em}a{overflow-wrap:anywhere}
</style></head><body><h1>Agentic AI Security Scanner Report</h1>"""]
    fields = [("Name", data["name"]), ("Description", data["description"] or "Not provided"),
              ("Programming language(s)", ", ".join(data["languages"])), ("Scan model", data["model"]),
              ("Scan date and time", timestamp), ("Intended behavior", data["intent"]), ("Coverage and limitations", data["coverage"])]
    out.extend(f"<p><strong>{e(label)}:</strong> {e(value)}</p>" for label, value in fields)
    out.append("<h2>Executive summary</h2><table><tr><th>Severity</th><th>Count</th></tr>")
    out.extend(f"<tr><td>{s}</td><td>{counts[s]}</td></tr>" for s in SEVERITIES)
    out.append("</table><table><tr><th>Severity</th><th>Risk</th><th>Location</th></tr>")
    for f in data["findings"]:
        out.append(f"<tr><td>{e(f['severity'])}</td><td>{e(f['title'])}</td><td>{e(f['file'])}:{f['line']}</td></tr>")
    out.append("</table><h2>Detailed findings</h2>")
    if not data["findings"]:
        out.append("<p>No substantiated findings were identified in the reviewed scope. This is not a guarantee of security.</p>")
    for i, f in enumerate(data["findings"], 1):
        out.append(f"<section><h3>{i}. {e(f['title'])}</h3>")
        for label, value in (("Severity", f["severity"]), ("Full file location", f"{f['file']}:{f['line']}"),
                             ("Risk description and intent", f["description"])):
            out.append(f"<p><strong>{e(label)}:</strong> {e(value)}</p>")
        out.append(f"<h4>Code snippet</h4><pre>{e(f['snippet'])}</pre><h4>Recommendations</h4><p>{e(f['recommendation'])}</p><h4>References</h4><ul>")
        out.extend(f'<li><a href="{e(r["url"], quote=True)}">{e(r["title"])}</a></li>' for r in f["references"])
        out.append("</ul></section>")
    return "\n".join(out) + "</body></html>\n"


def report_pdf(data, timestamp, output):
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"),
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arial.ttf",
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path(reportlab.__file__).parent / "fonts" / "Vera.ttf",
    ]
    font = next((path for path in candidates if path.is_file()), None)
    if font is None:
        raise ValueError("No compatible TrueType font found for PDF generation")
    pdfmetrics.registerFont(TTFont("ScannerFont", str(font)))
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = "ScannerFont"
    styles.add(ParagraphStyle(name="CodeWrap", parent=styles["BodyText"], fontSize=8,
                              leading=10, alignment=TA_LEFT, splitLongWords=True))
    story = []
    def paragraph(text, style="BodyText"):
        story.append(Paragraph(html.escape(str(text)).replace("\n", "<br/>"), styles[style]))
        story.append(Spacer(1, 5))

    paragraph("Agentic AI Security Scanner Report", "Title")
    for label, value in (("Name", data["name"]), ("Description", data["description"] or "Not provided"),
                         ("Programming language(s)", ", ".join(data["languages"])), ("Scan model", data["model"]),
                         ("Scan date and time", timestamp), ("Intended behavior", data["intent"]),
                         ("Coverage and limitations", data["coverage"])):
        paragraph(f"{label}: {value}")
    paragraph("Executive summary", "Heading2")
    rows = [["Severity", "Count"]] + [[s, str(sum(f["severity"] == s for f in data["findings"]))] for s in SEVERITIES]
    table = Table(rows, colWidths=[200, 80], hAlign="LEFT", repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                               ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.extend([table, Spacer(1, 10)])
    if data["findings"]:
        rows = [[Paragraph(value, styles["BodyText"]) for value in ("Severity", "Risk", "Location")]]
        for f in data["findings"]:
            rows.append([Paragraph(html.escape(value), styles["BodyText"]) for value in
                         (f["severity"], f["title"], f"{f['file']}:{f['line']}")])
        table = Table(rows, colWidths=[60, 155, 230], hAlign="LEFT", repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                                   ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.extend([table, Spacer(1, 10)])
    paragraph("Detailed findings", "Heading2")
    if not data["findings"]:
        paragraph("No substantiated findings were identified in the reviewed scope. This is not a guarantee of security.")
    for i, f in enumerate(data["findings"], 1):
        paragraph(f"{i}. {f['title']}", "Heading3")
        for label, value in (("Severity", f["severity"]), ("Full file location", f"{f['file']}:{f['line']}"),
                             ("Risk description and intent", f["description"])):
            paragraph(f"{label}: {value}")
        paragraph("Code snippet", "Heading4")
        for line in f["snippet"].splitlines() or [""]:
            text = html.escape(line.expandtabs(4) or " ").replace(" ", "&nbsp;")
            story.extend([Paragraph(text, styles["CodeWrap"]), Spacer(1, 5)])
        paragraph("Recommendations", "Heading4")
        paragraph(f["recommendation"])
        paragraph("References", "Heading4")
        for ref in f["references"]:
            story.append(Paragraph(f'<link href="{html.escape(ref["url"], quote=True)}" color="blue">{html.escape(ref["title"])}</link>', styles["BodyText"]))
            story.append(Spacer(1, 5))
    SimpleDocTemplate(str(output), title="Agentic AI Security Scanner Report").build(story)


def generate_report(input_file, output_dir):
    with open(input_file, encoding="utf-8") as file:
        data = validate(json.load(file))
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().astimezone()
    timestamp = now.isoformat(timespec="seconds")
    name = "agentic-ai-scanner-report-" + now.strftime("%Y-%m-%d-%H%M%S-%f")
    html_path, pdf_path = output_dir / (name + ".html"), output_dir / (name + ".pdf")
    try:
        report_pdf(data, timestamp, pdf_path)
        html_path.write_text(report_html(data, timestamp), encoding="utf-8")
    except Exception:
        html_path.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)
        raise
    print(f"HTML: {html_path}\nPDF: {pdf_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--update", action="store_true", help="Update the online OWASP reference snapshots")
    mode.add_argument("--report", metavar="FINDINGS_JSON", help="Render agent-authored findings")
    parser.add_argument("--output", default=".", help="Report output directory (default: current directory)")
    args = parser.parse_args()
    try:
        if args.update:
            update_references()
        else:
            generate_report(args.report, args.output)
    except (OSError, ValueError, ImportError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
