"""`catchup-overlap` — scheduled worker: one reconcile-and-notify pass, then exit.

Shipped as a console script and run by Railway cron (hourly). The only scheduler
edge in the system (Constitution IV).
"""

from __future__ import annotations

import typer

from catchup.db import session_scope
from catchup.logging_config import configure_logging
from catchup.notify import get_notifier
from catchup.overlaps.runner import notify_new, reconcile


def _run_once() -> None:
    with session_scope() as db:
        reconcile(db)
        notify_new(db, get_notifier())


def run() -> None:
    """Run one reconcile-and-notify pass, then exit."""
    configure_logging()
    _run_once()


def main() -> None:
    typer.run(run)


if __name__ == "__main__":
    main()
