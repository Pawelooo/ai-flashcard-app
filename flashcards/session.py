from typing import TypedDict, cast

from django.http import HttpRequest


class SK:
    TOPIC_ID = "session_topic_id"
    CARDS = "session_cards"
    INDEX = "session_index"
    SCORE = "session_score"
    WRONG_IDS = "session_wrong_ids"
    LAST_WRONG_IDS = "last_wrong_ids"
    # Quiz ABCD: kolejność opcji bieżącej karty — trzymana na serwerze, nie w formularzu
    QUIZ_OPTIONS = "quiz_options"
    ALL = [TOPIC_ID, CARDS, INDEX, SCORE, WRONG_IDS, QUIZ_OPTIONS]

    # Tryb na czas — osobne klucze, żeby nie mieszać się ze zwykłą sesją nauki
    TIMED_RUN = "timed_run_id"
    TIMED_CARDS = "timed_cards"
    TIMED_INDEX = "timed_index"
    TIMED_ALL = [TIMED_RUN, TIMED_CARDS, TIMED_INDEX]


class SessionState(TypedDict):
    session_topic_id: int | None
    session_cards: list[int]
    session_index: int
    session_score: int
    session_wrong_ids: list[int]


def get_session(request: HttpRequest) -> SessionState:
    return cast(SessionState, request.session)
