from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import List

import pandas as pd
from sqlalchemy.orm import Session

from .config import get_today_folder
from .db import Roster, Team, Player, RosterChange


def export_team_rosters_for_date(session: Session, roster_date: date) -> Path:
    """
    Export all team rosters for a given date into CSV files in that day's folder.
    """
    folder = get_today_folder(roster_date)

    # Join rosters with team and player for readability
    q = (
        session.query(
            Roster.date,
            Team.id.label("team_id"),
            Team.name.label("team_name"),
            Player.id.label("player_id"),
            Player.full_name.label("player_name"),
            Player.primary_position.label("position"),
            Roster.roster_type,
        )
        .join(Team, Team.id == Roster.team_id)
        .join(Player, Player.id == Roster.player_id)
        .filter(Roster.date == roster_date)
    )

    df = pd.read_sql(q.statement, session.bind)

    # Save one combined file and optionally per-team
    combined_path = folder / "all_rosters.csv"
    df.to_csv(combined_path, index=False)

    for team_id, team_df in df.groupby("team_id"):
        team_name = team_df["team_name"].iloc[0]
        safe_name = "".join(c for c in team_name if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
        path = folder / f"team_{team_id}_{safe_name}_roster.csv"
        team_df.to_csv(path, index=False)

    return folder


def export_changes_for_date(session: Session, change_date: date) -> Path:
    """
    Export roster changes for a given date into a CSV in that day's folder.
    """
    folder = get_today_folder(change_date)

    q = (
        session.query(
            RosterChange.change_date,
            Team.id.label("team_id"),
            Team.name.label("team_name"),
            Player.id.label("player_id"),
            Player.full_name.label("player_name"),
            Player.primary_position.label("position"),
            RosterChange.change_type,
            RosterChange.old_roster_type,
            RosterChange.new_roster_type,
            RosterChange.created_at,
        )
        .join(Team, Team.id == RosterChange.team_id)
        .join(Player, Player.id == RosterChange.player_id)
        .filter(RosterChange.change_date == change_date)
    )

    df = pd.read_sql(q.statement, session.bind)

    path = folder / "roster_changes.csv"
    df.to_csv(path, index=False)

    return path
