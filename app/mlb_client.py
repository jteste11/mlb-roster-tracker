from __future__ import annotations

from typing import List, Dict, Any
from datetime import date

import mlbstatsapi

from .config import DEFAULT_SEASON

mlb = mlbstatsapi.Mlb()


def get_all_mlb_teams(season: int | None = None) -> List[Dict[str, Any]]:
    """
    Returns a list of team dicts for MLB (sportId=1).
    """
    if season is None:
        season = DEFAULT_SEASON

    teams = mlb.get_teams(sport_id=1, season=season)
    # teams is a list of Team models; convert to dicts
    return [t.model_dump() for t in teams]


def get_team_active_roster(team_id: int, roster_date: date | None = None) -> List[Dict[str, Any]]:
    """
    Returns active roster for a team as list of dicts.
    """
    # python-mlb-statsapi exposes get_team_roster(team_id, roster_type, **params)
    params = {}
    if roster_date is not None:
        params["date"] = roster_date.isoformat()

    roster = mlb.get_team_roster(team_id, roster_type="active", **params)
    # roster is a list of RosterEntry models
    return [r.model_dump() for r in roster]
