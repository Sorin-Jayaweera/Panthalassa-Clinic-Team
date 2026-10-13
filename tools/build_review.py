"""Rebuild the review/ folder and docs/review.json from the repository's GitHub issues.

Run by .github/workflows/review.yml whenever an issue is opened, edited, closed or commented on.
A review note is an issue whose title starts with [validated], [question], [comment] or [change] and whose
body contains the marker the website puts there. Anything else in the issue tracker is ignored.

Can be run by hand:  REPO=Sorin-Jayaweera/Panthalassa-Clinic-Team python tools/build_review.py
"""
import datetime as dt
import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = os.environ.get("REPO", "Sorin-Jayaweera/Panthalassa-Clinic-Team")
TOKEN = os.environ.get("GH_TOKEN", "")
NAMES = {"validated": "Validated", "question": "Under question", "comment": "Comment", "change": "Suggested change"}
FILES = {"validated": "validated.md", "question": "under_question.md", "comment": "comments.md", "change": "suggested_changes.md"}


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "jacon-review"})
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def issues():
    out, page = [], 1
    while True:
        batch = get(f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&page={page}")
        out += [i for i in batch if "pull_request" not in i]
        if len(batch) < 100:
            return out
        page += 1


def parse(i):
    body = i.get("body") or ""
    m = re.match(r"\[(validated|question|comment|change)\]", i.get("title") or "", re.I)
    if not m or "jacon-review" not in body:
        return None

    def field(n):
        f = re.search(r"\*\*" + n + r":\*\*[ \t]*(.*)", body)
        return f.group(1).strip() if f else ""
    note = body.split("**Note:**", 1)[1] if "**Note:**" in body else ""
    note = re.sub(r"\(optional: how you checked it\)|\(write your [a-z ]+ here\)", "", note).strip()
    replies = []
    if i.get("comments"):
        for c in get(i["comments_url"]):
            replies.append({"by": c["user"]["login"], "at": c["created_at"][:10], "text": (c.get("body") or "").strip()})
    return {"kind": m.group(1).lower(), "number": i["number"], "url": i["html_url"], "state": i["state"], "by": i["user"]["login"], "at": i["created_at"][:10],
            "closed": (i.get("closed_at") or "")[:10], "tab": field("Tab"), "section": field("Section"), "block": field("Block"), "quote": field("Quote"),
            "link": field("Link"), "note": note, "replies": len(replies), "thread": replies}


def md(item):
    lines = [f"### #{item['number']}: {item['tab']}" + (f", {item['section']}" if item["section"] else ""), "",
             f"- **{NAMES[item['kind']]}** by @{item['by']} on {item['at']}" + (f" (closed {item['closed']})" if item["state"] == "closed" else ""),
             f"- On the page: {item['link']}", f"- Issue: {item['url']}", "", "> " + item["quote"], ""]
    if item["note"]:
        lines += [item["note"], ""]
    for r in item["thread"]:
        lines += [f"**@{r['by']}, {r['at']}:** {r['text']}", ""]
    return "\n".join(lines)


def main():
    items = [x for x in (parse(i) for i in issues()) if x]
    items.sort(key=lambda x: x["number"])
    open_, closed = [x for x in items if x["state"] == "open"], [x for x in items if x["state"] == "closed"]
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rev = ROOT / "review"
    rev.mkdir(exist_ok=True)
    for kind, name in FILES.items():
        sel = [x for x in open_ if x["kind"] == kind]
        text = f"# {NAMES[kind]}\n\n{len(sel)} open. Generated from the GitHub issues; do not edit by hand.\n\n" + "\n".join(md(x) for x in sel)
        (rev / name).write_text(text.rstrip() + "\n", encoding="utf-8")
    (rev / "resolved.md").write_text((f"# Resolved\n\n{len(closed)} closed notes.\n\n" + "\n".join(md(x) for x in closed)).rstrip() + "\n", encoding="utf-8")
    counts = {k: sum(1 for x in open_ if x["kind"] == k) for k in FILES}
    readme = f"""# Review notes

Marks and comments that people made on the website. Each one is a GitHub issue; this folder is rebuilt from the
issues by `tools/build_review.py` (GitHub Action "Review notes") every time an issue changes. Do not edit these files by hand.

| File | What | Open |
|---|---|---|
| [validated.md](validated.md) | text a person has checked and confirmed | {counts['validated']} |
| [under_question.md](under_question.md) | text a person doubts or wants checked | {counts['question']} |
| [comments.md](comments.md) | comments | {counts['comment']} |
| [suggested_changes.md](suggested_changes.md) | wording or numbers a person wants changed | {counts['change']} |
| [resolved.md](resolved.md) | closed notes | {len(closed)} |

To add one: open https://sorin-jayaweera.github.io/Panthalassa-Clinic-Team/, press Edit, select text, choose a button, and submit
the issue that opens. To withdraw or resolve one, close its issue.
"""
    (rev / "README.md").write_text(readme, encoding="utf-8")
    slim = [{k: v for k, v in x.items() if k != "thread"} for x in open_]
    (ROOT / "docs" / "review.json").write_text(json.dumps({"updated": now, "open": slim}, indent=1), encoding="utf-8")
    print(len(open_), "open,", len(closed), "closed")


if __name__ == "__main__":
    main()
