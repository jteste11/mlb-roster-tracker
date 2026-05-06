from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from .config import get_today_folder
from .db import RosterChange, Team, Player


def generate_daily_summary(session: Session, change_date: date) -> Path:
    """
    Generate a text summary of all roster changes for the given date.
    """
    folder = get_today_folder(change_date)
    summary_path = folder / "summary.txt"

    q = (
        session.query(
            Team.name.label("team_name"),
            Player.full_name.label("player_name"),
            RosterChange.change_type,
        )
        .join(Team, Team.id == RosterChange.team_id)
        .join(Player, Player.id == RosterChange.player_id)
        .filter(RosterChange.change_date == change_date)
        .order_by(Team.name, Player.full_name)
    )

    rows = list(q.all())

    with summary_path.open("w", encoding="utf-8") as f:
        f.write(f"MLB Roster Changes for {change_date.isoformat()}\n")
        f.write("=" * 60 + "\n\n")

        if not rows:
            f.write("No roster changes recorded.\n")
            return summary_path

        current_team = None
        for team_name, player_name, change_type in rows:
            if team_name != current_team:
                if current_team is not None:
                    f.write("\n")
                f.write(f"{team_name}\n")
                f.write("-" * len(team_name) + "\n")
                current_team = team_name

            f.write(f"  {change_type.upper():7}  {player_name}\n")

    return summary_path
