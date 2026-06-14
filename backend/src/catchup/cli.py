"""`catchup-roster` — owner-only CLI to manage the invite roster."""

from __future__ import annotations

import typer
from sqlalchemy import select

from catchup.db import session_scope
from catchup.models import RosterInvite

app = typer.Typer(help="Manage the catch-up invite roster.")


@app.command()
def add(email: str, note: str = typer.Option(None, help="Optional label")) -> None:
    """Add an email to the invite roster."""
    email = email.lower()
    with session_scope() as db:
        if db.get(RosterInvite, email) is not None:
            typer.echo(f"{email} already on roster")
            return
        db.add(RosterInvite(email=email, note=note))
    typer.echo(f"added {email}")


@app.command()
def remove(email: str) -> None:
    """Remove an email from the invite roster."""
    email = email.lower()
    with session_scope() as db:
        invite = db.get(RosterInvite, email)
        if invite is None:
            typer.echo(f"{email} not on roster")
            raise typer.Exit(code=1)
        db.delete(invite)
    typer.echo(f"removed {email}")


@app.command("list")
def list_() -> None:
    """List all roster emails."""
    with session_scope() as db:
        rows = db.execute(select(RosterInvite).order_by(RosterInvite.email)).scalars().all()
        for row in rows:
            typer.echo(f"{row.email}\t{row.note or ''}")


if __name__ == "__main__":
    app()
