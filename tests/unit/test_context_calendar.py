import pandas as pd

from novo_f1.transformation.calendar import (
    available_meetings,
    grid_session_key,
    meeting_sessions,
    season_calendar,
)
from novo_f1.transformation.context import (
    key_events,
    race_control_events,
    weather_series,
    weather_summary,
)

NOW = pd.Timestamp("2026-10-19T00:00:00Z")


def test_season_calendar(meetings, sessions):
    calendar = season_calendar(meetings, sessions)

    assert calendar["meeting_key"].tolist() == [1140, 1219, 1300]
    singapore = calendar.set_index("meeting_key").loc[1219]
    assert singapore["sessions"] == 3
    assert bool(singapore["has_sprint"])
    assert bool(calendar.set_index("meeting_key").loc[1140, "is_testing"])


def test_season_calendar_without_sessions(meetings):
    calendar = season_calendar(meetings, pd.DataFrame())

    assert (calendar["sessions"] == 0).all()
    assert not calendar["has_sprint"].any()


def test_season_calendar_empty():
    assert season_calendar(pd.DataFrame(), pd.DataFrame()).empty


def test_available_meetings_excludes_future_and_cancelled(meetings, sessions):
    available = available_meetings(season_calendar(meetings, sessions), NOW)

    assert available["meeting_key"].tolist() == [1140, 1219]


def test_meeting_sessions_sorted(sessions):
    result = meeting_sessions(sessions, 1219)

    assert result["session_name"].tolist() == ["Sprint", "Qualifying", "Race"]


def test_meeting_sessions_empty():
    assert meeting_sessions(pd.DataFrame(), 1).empty


def test_weather_series_and_summary(weather):
    series = weather_series(weather)
    summary = weather_summary(weather)

    assert series["rainfall"].tolist() == [True, False]
    assert summary == {
        "air_min": 29.5,
        "air_max": 30.1,
        "track_min": 40.5,
        "track_max": 42.0,
        "rain": True,
    }


def test_weather_summary_empty():
    assert weather_summary(pd.DataFrame())["air_min"] is None


def test_race_control_events_sorted(race_control):
    events = race_control_events(race_control)

    assert events["date"].is_monotonic_increasing


def test_key_events_keeps_track_flags_and_safety_car(race_control):
    events = key_events(race_control)

    assert events["message"].tolist() == [
        "GREEN LIGHT - PIT EXIT OPEN",
        "SAFETY CAR DEPLOYED",
    ]


def test_key_events_empty():
    assert key_events(pd.DataFrame()).empty


def test_grid_session_key_race_uses_last_qualifying(sessions):
    assert grid_session_key(sessions, 9161) == 9160


def test_grid_session_key_sprint_uses_sprint_qualifying():
    sessions = pd.DataFrame(
        {
            "session_key": [9502, 9506, 9498, 9507],
            "session_name": ["Sprint Qualifying", "Sprint", "Qualifying", "Race"],
            "session_type": ["Qualifying", "Race", "Qualifying", "Race"],
            "meeting_key": [1234] * 4,
            "date_start": [
                "2024-05-03T20:30:00+00:00",
                "2024-05-04T16:00:00+00:00",
                "2024-05-04T20:00:00+00:00",
                "2024-05-05T20:00:00+00:00",
            ],
        }
    )

    assert grid_session_key(sessions, 9506) == 9502
    assert grid_session_key(sessions, 9507) == 9498


def test_grid_session_key_unavailable(sessions):
    assert grid_session_key(sessions, 9160) is None
    assert grid_session_key(sessions, 1) is None
    assert grid_session_key(pd.DataFrame(), 9161) is None


def test_weather_series_drops_zero_temperature_glitch(weather):
    weather.loc[0, "track_temperature"] = 0.0

    summary = weather_summary(weather)

    assert summary["track_min"] == 42.0
