from django import template

register = template.Library()


@register.filter
def pl_plural(value, forms):
    """Polska odmiana po liczebniku: {{ n|pl_plural:"fiszka,fiszki,fiszek" }}.

    1 → fiszka; 2–4 (poza 12–14) → fiszki; reszta → fiszek.
    """
    one, few, many = forms.split(',')
    try:
        n = abs(int(value))
    except (TypeError, ValueError):
        return many
    if n == 1:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many
