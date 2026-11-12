"""Dane wspólne dla każdego szablonu."""

# url_name → zakładka w menu, którą podświetlamy
_NAV_SECTIONS = {
    'dashboard': 'panel',
    'topics': 'nauka',
    'study': 'nauka',
    'study_results': 'nauka',
    'quiz_play': 'nauka',
    'written_play': 'nauka',
    'timed_play': 'nauka',
    'timed_results': 'nauka',
    'card_list': 'fiszki',
    'card_detail': 'fiszki',
    'card_edit': 'fiszki',
    'card_delete': 'fiszki',
    'card_create': 'dodaj',
    'leaderboard': 'ranking',
}


def navigation(request):
    match = getattr(request, 'resolver_match', None)
    section = _NAV_SECTIONS.get(match.url_name) if match else None

    initial = '?'
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        name = user.username or (user.email or '').split('@')[0]
        initial = (name[:1] or '?').upper()

    return {'nav_section': section, 'user_initial': initial}
