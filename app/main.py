from __future__ import annotations

from datetime import date

from .config import DEFAULT_SEASON
from .db import init_db, get_session
from .roster_logic import sync_teams, process_team_for_date
from .export import export_team_rosters_for_date, export_changes_for_date
from .summary import generate_daily_summary


def run_for_date(run_date: date, season: int | None = None):
    if season is None:
        season = DEFAULT_SEASON

    init_db()
    session = get_session()

    try:
        teams = sync_teams(session, season=season)

        for team in teams:
            process_team_for_date(session, team, run_date)

        export_team_rosters_for_date(session, run_date)
        export_changes_for_date(session, run_date)
        generate_daily_summary(session, run_date)
    finally:
        session.close()


if __name__ == "__main__":
    # Default: run for today
    today = date.today()
    run_for_date(today)
