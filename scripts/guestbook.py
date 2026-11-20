import os
import re
import html
from datetime import datetime, timezone

MAX_ENTRIES = 5
README_PATH = "README.md"
START_TAG = "<!-- START_SECTION:guestbook -->"
END_TAG = "<!-- END_SECTION:guestbook -->"

def sanitize(text):
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    # Escape markdown formatting characters to prevent breaking layout
    clean = clean.replace('|', '\\|').replace('\n', ' ').replace('\r', '')
    clean = html.escape(clean)
    return clean[:120].strip()

def main():
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_body = os.environ.get("ISSUE_BODY", "")
    author = os.environ.get("ISSUE_AUTHOR", "anonymous")

    # Only process if triggered by guestbook
    if not issue_title.lower().startswith("guestbook"):
        print("Not a guestbook issue, skipping.")
        return

    # Extract message from issue body
    message = sanitize(issue_body)
    if not message:
        message = "Stopped by to explore your work! ⭐"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    new_entry = (
        f"<tr>"
        f"<td><code>{timestamp}</code></td>"
        f"<td><a href=\"https://github.com/{author}\"><b>@{author}</b></a></td>"
        f"<td>{message}</td>"
        f"</tr>"
    )

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(f"{re.escape(START_TAG)}(.*?){re.escape(END_TAG)}", re.DOTALL)
    match = pattern.search(content)

    if not match:
        print("Guestbook tags not found in README.md")
        return

    section_body = match.group(1)

    # Extract existing rows
    row_pattern = re.compile(r"(<tr>.*?</tr>)", re.DOTALL)
    existing_rows = row_pattern.findall(section_body)

    # Insert new entry at top and keep max entries
    updated_rows = [new_entry] + existing_rows[: MAX_ENTRIES - 1]

    table_header = (
        "\n<table>\n"
        "  <thead>\n"
        "    <tr>\n"
        "      <th>Timestamp</th>\n"
        "      <th>Visitor</th>\n"
        "      <th>Message</th>\n"
        "    </tr>\n"
        "  </thead>\n"
        "  <tbody>\n"
    )
    table_footer = "\n  </tbody>\n</table>\n"

    new_section_body = table_header + "    " + "\n    ".join(updated_rows) + table_footer
    updated_content = pattern.sub(f"{START_TAG}{new_section_body}{END_TAG}", content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Successfully added guestbook entry for @{author}")

if __name__ == "__main__":
    main()
