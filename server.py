from datetime import datetime
from pathlib import Path

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ToolBridge")

# Paths are based on this file's location, so they work from any folder
BASE_DIR = Path(__file__).parent
TASKS_FILE = BASE_DIR / "tasks.txt"
NOTES_DIR = BASE_DIR / "notes"


@mcp.tool()
def add_task(task: str) -> str:
    """Add a task to the user's to-do list."""
    with open(TASKS_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M}] {task}\n")
    return f"Task added: {task}"


@mcp.tool()
def search_notes(keyword: str) -> str:
    """Search the user's notes (.txt and .md files) for a keyword."""
    if not NOTES_DIR.exists():
        return "No notes folder found."
    matches = []
    for file in sorted(NOTES_DIR.glob("*")):
        if file.suffix not in (".txt", ".md"):
            continue
        text = file.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            if keyword.lower() in line.lower():
                matches.append(f"{file.name} (line {number}): {line.strip()}")
    if not matches:
        return f"No notes found containing '{keyword}'."
    return "\n".join(matches[:10])  # at most 10 results


@mcp.tool()
def summarize_repo(repo: str) -> str:
    """Summarize a public GitHub repository. Input format: owner/name,
    for example princy21aj/taskpilot-agent."""
    if repo.count("/") != 1:
        return "Please use the format owner/name."
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ToolBridge"}
    try:
        r = requests.get(
            f"https://api.github.com/repos/{repo}", headers=headers, timeout=10
        )
    except requests.RequestException as e:
        return f"Network error: {e}"
    if r.status_code == 404:
        return f"Repository '{repo}' was not found."
    if r.status_code != 200:
        return f"GitHub returned error {r.status_code} (maybe a rate limit)."

    d = r.json()
    summary = (
        f"{d['full_name']}: {d.get('description') or 'No description'}\n"
        f"Language: {d.get('language')} | Stars: {d['stargazers_count']} | "
        f"Forks: {d['forks_count']}\n"
        f"Last updated: {d['pushed_at']}\n"
        f"Topics: {', '.join(d.get('topics', [])) or 'none'}"
    )

    # Add the first part of the README, if there is one
    try:
        rd = requests.get(
            f"https://api.github.com/repos/{repo}/readme",
            headers={**headers, "Accept": "application/vnd.github.raw+json"},
            timeout=10,
        )
        if rd.status_code == 200:
            summary += f"\n\nREADME start:\n{rd.text[:600]}"
    except requests.RequestException:
        pass
    return summary


if __name__ == "__main__":
    mcp.run()