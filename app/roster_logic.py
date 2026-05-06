from __future__ import annotations

from datetime import date
from typing import Dict, Any, List, Tuple

from sqlalchemy.orm import Session

from .db import Team, Player, Roster, RosterChange, get_latest_roster_date_for_team, get_roster_for_team_on_date
from .mlb_client import get_all_mlb_teams, get_team_active_roster


def sync_teams(session: Session, season: int) -> List[Team]:
    """
    Ensure all MLB teams exist in DB and return them.
    """
    api_teams = get_all_mlb_teams(season=season)
    teams_by_id: Dict[int, Team] = {t.id: t for t in session.query(Team).all()}

    result: List[Team] = []

    for t in api_teams:
        team_id = t["id"]
        name = t["name"]
        abbr = t.get("abbreviation") or t.get("abbrev") or None

        if team_id in teams_by_id:
            team = teams_by_id[team_id]
            team.name = name
            team.abbreviation = abbr
        else:
            team = Team(id=team_id, name=name, abbreviation=abbr)
            session.add(team)

        result.append(team)

    session.commit()
    return result


def _get_or_create_player(session: Session, player_data: Dict[str, Any]) -> Player:
    player_id = player_data["person"]["id"]
    full_name = player_data["person"]["full_name"]
    primary_position = None
    if player_data.get("position"):
        primary_position = player_data["position"].get("abbreviation")

    player = session.get(Player, player_id)
    if player is None:
        player = Player(
            id=player_id,
            full_name=full_name,
            primary_position=primary_position,
        )
        session.add(player)
    else:
        player.full_name = full_name
        player.primary_position = primary_position

    return player


def store_roster_snapshot(
    session: Session,
    team: Team,
    roster_date: date,
    roster_entries: List[Dict[str, Any]],
    roster_type: str = "active",
) -> List[Roster]:
    """
    Store today's roster snapshot for a team.
    """
    # First, ensure players exist
    players: List[Player] = []
    for entry in roster_entries:
        player = _get_or_create_player(session, entry)
        players.append(player)

    session.flush()

    # Remove any existing snapshot for this date/team (idempotent runs)
    session.query(Roster).filter(
        Roster.team_id == team.id,
        Roster.date == roster_date,
    ).delete()

    roster_rows: List[Roster] = []
    for player in players:
        r = Roster(
            date=roster_date,
            team_id=team.id,
            player_id=player.id,
            roster_type=roster_type,
        )
        session.add(r)
        roster_rows.append(r)

    session.commit()
    return roster_rows


def diff_rosters(
    previous: List[Roster],
    current: List[Roster],
) -> Tuple[List[Roster], List[Roster]]:
    """
    Returns (added, removed) lists comparing previous vs current.
    """
    prev_ids = {r.player_id: r for r in previous}
    curr_ids = {r.player_id: r for r in current}

    added = [curr_ids[pid] for pid in curr_ids.keys() - prev_ids.keys()]
    removed = [prev_ids[pid] for pid in prev_ids.keys() - curr_ids.keys()]

    return added, removed


def record_roster_changes(
    session: Session,
    change_date: date,
    team: Team,
    added: List[Roster],
    removed: List[Roster],
):
    """
    Persist roster changes into RosterChange table.
    """
    for r in added:
        change = RosterChange(
            change_date=change_date,
            team_id=team.id,
            player_id=r.player_id,
            change_type="added",
            old_roster_type=None,
            new_roster_type=r.roster_type,
        )
        session.add(change)

    for r in removed:
        change = RosterChange(
            change_date=change_date,
            team_id=team.id,
            player_id=r.player_id,
            change_type="removed",
            old_roster_type=r.roster_type,
            new_roster_type=None,
        )
        session.add(change)

    session.commit()


def process_team_for_date(session: Session, team: Team, roster_date: date):
    """
    Full pipeline for a single team on a given date:
    - fetch roster
    - store snapshot
    - diff vs previous
    - record changes
    """
    api_roster = get_team_active_roster(team.id, roster_date=roster_date)
    current_snapshot = store_roster_snapshot(
        session=session,
        team=team,
        roster_date=roster_date,
        roster_entries=api_roster,
        roster_type="active",
    )

    # Find previous date for this team
    prev_date = get_latest_roster_date_for_team(session, team.id)
    if prev_date is None or prev_date == roster_date:
        # No previous snapshot to diff against
        return

    previous_snapshot = get_roster_for_team_on_date(session, team.id, prev_date)
    added, removed = diff_rosters(previous_snapshot, current_snapshot)
    record_roster_changes(session, roster_date, team, added, removed)
