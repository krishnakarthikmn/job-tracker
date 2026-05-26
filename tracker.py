#!/usr/bin/env python3
"""Job Application Tracker — terminal UI powered by rich."""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

DATA_FILE = Path(__file__).parent / "applications.json"

STATUSES = ["Applied", "Phone Screen", "Interview", "Final Round", "Offer", "Rejected", "Withdrawn"]

STATUS_COLORS = {
    "Applied":      "cyan",
    "Phone Screen": "blue",
    "Interview":    "yellow",
    "Final Round":  "magenta",
    "Offer":        "bright_green",
    "Rejected":     "red",
    "Withdrawn":    "dim",
}

console = Console()


# ── Data helpers ─────────────────────────────────────────────────────────────

def load() -> list[dict]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return []


def save(apps: list[dict]) -> None:
    DATA_FILE.write_text(json.dumps(apps, indent=2))


def next_id(apps: list[dict]) -> int:
    return max((a["id"] for a in apps), default=0) + 1


# ── Display helpers ───────────────────────────────────────────────────────────

def status_badge(status: str) -> Text:
    color = STATUS_COLORS.get(status, "white")
    return Text(f" {status} ", style=f"bold {color} on default")


def render_table(apps: list[dict], title: str = "All Applications") -> None:
    if not apps:
        console.print(Panel("[dim]No applications yet. Add one with [bold]a[/bold].[/dim]", title=title))
        return

    t = Table(
        box=box.ROUNDED,
        title=title,
        show_lines=False,
        header_style="bold white on #1a1a2e",
        expand=True,
    )
    t.add_column("#",         style="dim", width=4, justify="right")
    t.add_column("Company",   style="bold", min_width=16)
    t.add_column("Role",      min_width=18)
    t.add_column("Status",    min_width=13)
    t.add_column("Applied",   style="dim", width=11)
    t.add_column("Updated",   style="dim", width=11)
    t.add_column("Notes",     min_width=20, overflow="fold")

    for a in sorted(apps, key=lambda x: x.get("updated", x["applied"]), reverse=True):
        color = STATUS_COLORS.get(a["status"], "white")
        t.add_row(
            str(a["id"]),
            a["company"],
            a["role"],
            Text(a["status"], style=f"bold {color}"),
            a["applied"],
            a.get("updated", a["applied"]),
            a.get("notes", ""),
        )
    console.print(t)


def render_stats(apps: list[dict]) -> None:
    if not apps:
        return
    counts = {s: 0 for s in STATUSES}
    for a in apps:
        counts[a["status"]] = counts.get(a["status"], 0) + 1

    total = len(apps)
    active = sum(counts[s] for s in ["Phone Screen", "Interview", "Final Round"])
    offers = counts["Offer"]
    rate = f"{offers/total*100:.0f}%" if total else "—"

    panels = [
        Panel(f"[bold cyan]{total}[/bold cyan]\n[dim]Total[/dim]",   expand=True),
        Panel(f"[bold yellow]{active}[/bold yellow]\n[dim]Active[/dim]", expand=True),
        Panel(f"[bold bright_green]{offers}[/bold bright_green]\n[dim]Offers[/dim]", expand=True),
        Panel(f"[bold magenta]{rate}[/bold magenta]\n[dim]Offer Rate[/dim]", expand=True),
    ]
    console.print(Columns(panels, equal=True, padding=(0, 1)))


# ── CRUD actions ──────────────────────────────────────────────────────────────

def add_application(apps: list[dict]) -> None:
    console.rule("[bold cyan]New Application")
    company = Prompt.ask("  Company")
    role    = Prompt.ask("  Role / Title")

    console.print("  Statuses: " + ", ".join(
        f"[{i+1}] [{STATUS_COLORS[s]}]{s}[/]" for i, s in enumerate(STATUSES)
    ))
    idx = IntPrompt.ask("  Status #", default=1) - 1
    idx = max(0, min(idx, len(STATUSES) - 1))
    status = STATUSES[idx]

    today = date.today().isoformat()
    applied = Prompt.ask("  Date applied (YYYY-MM-DD)", default=today)
    notes   = Prompt.ask("  Notes (optional)", default="")

    app = {
        "id":      next_id(apps),
        "company": company,
        "role":    role,
        "status":  status,
        "applied": applied,
        "updated": today,
        "notes":   notes,
    }
    apps.append(app)
    save(apps)
    console.print(f"  [bold bright_green]Added[/] {company} — {role}")


def update_status(apps: list[dict]) -> None:
    if not apps:
        console.print("[dim]No applications to update.[/dim]")
        return
    render_table(apps)
    aid = IntPrompt.ask("\n  Application ID to update")
    matches = [a for a in apps if a["id"] == aid]
    if not matches:
        console.print(f"[red]No application with ID {aid}[/red]")
        return
    app = matches[0]

    console.print(f"  Updating: [bold]{app['company']}[/] — {app['role']}  (current: [yellow]{app['status']}[/yellow])")
    console.print("  " + ", ".join(
        f"[{i+1}] [{STATUS_COLORS[s]}]{s}[/]" for i, s in enumerate(STATUSES)
    ))
    idx = IntPrompt.ask("  New status #") - 1
    idx = max(0, min(idx, len(STATUSES) - 1))
    app["status"]  = STATUSES[idx]
    app["updated"] = date.today().isoformat()

    note = Prompt.ask("  Add a note? (leave blank to skip)", default="")
    if note:
        existing = app.get("notes", "")
        app["notes"] = f"{existing} | {note}".lstrip(" | ") if existing else note

    save(apps)
    console.print(f"  [bold bright_green]Updated[/] → {app['status']}")


def delete_application(apps: list[dict]) -> None:
    if not apps:
        console.print("[dim]No applications.[/dim]")
        return
    render_table(apps)
    aid = IntPrompt.ask("\n  Application ID to delete")
    matches = [a for a in apps if a["id"] == aid]
    if not matches:
        console.print(f"[red]No application with ID {aid}[/red]")
        return
    app = matches[0]
    if Confirm.ask(f"  Delete [bold]{app['company']}[/] — {app['role']}?"):
        apps.remove(app)
        save(apps)
        console.print("  [dim]Deleted.[/dim]")


def search(apps: list[dict]) -> None:
    q = Prompt.ask("  Search (company / role / notes)").lower()
    results = [
        a for a in apps
        if q in a["company"].lower()
        or q in a["role"].lower()
        or q in a.get("notes", "").lower()
    ]
    render_table(results, title=f'Results for "{q}"')


def filter_by_status(apps: list[dict]) -> None:
    console.print("  " + ", ".join(
        f"[{i+1}] [{STATUS_COLORS[s]}]{s}[/]" for i, s in enumerate(STATUSES)
    ))
    idx = IntPrompt.ask("  Filter by status #") - 1
    idx = max(0, min(idx, len(STATUSES) - 1))
    status = STATUSES[idx]
    results = [a for a in apps if a["status"] == status]
    render_table(results, title=f"Status: {status}")


# ── Main loop ─────────────────────────────────────────────────────────────────

MENU = [
    ("a", "Add application"),
    ("u", "Update status"),
    ("s", "Search"),
    ("f", "Filter by status"),
    ("d", "Delete"),
    ("q", "Quit"),
]


def print_menu() -> None:
    items = "  ".join(f"[dim][[/dim][bold cyan]{k}[/bold cyan][dim]][/dim] {label}" for k, label in MENU)
    console.print(Panel(items, box=box.SIMPLE))


def main() -> None:
    console.clear()
    console.print(Panel(
        "[bold cyan]Job Application Tracker[/bold cyan]\n[dim]Stay on top of every opportunity[/dim]",
        box=box.DOUBLE_EDGE,
        expand=False,
    ))

    apps = load()

    while True:
        console.print()
        render_stats(apps)
        print_menu()
        choice = Prompt.ask("  >", default="").strip().lower()

        console.print()

        if choice == "a":
            add_application(apps)
        elif choice == "u":
            update_status(apps)
        elif choice == "s":
            search(apps)
        elif choice == "f":
            filter_by_status(apps)
        elif choice == "d":
            delete_application(apps)
        elif choice in ("q", "quit", "exit"):
            console.print("[dim]Goodbye.[/dim]")
            sys.exit(0)
        elif choice == "l" or choice == "":
            render_table(apps)
        else:
            console.print("[dim]Unknown command. Press Enter to list all.[/dim]")


if __name__ == "__main__":
    main()
