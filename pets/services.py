from datetime import date
from django.utils import timezone


def get_pet_age_display(birth_date: date | None) -> str:
    """Возвращает возраст питомца в удобном формате."""
    if not birth_date:
        return ""

    today = timezone.localdate()
    if birth_date > today:
        return ""

    total_days = (today - birth_date).days

    if total_days < 31:
        return f"{total_days} дн."

    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day

    if days < 0:
        months -= 1

        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year

        if prev_month == 12:
            next_month = 1
            next_year = prev_year + 1
        else:
            next_month = prev_month + 1
            next_year = prev_year

        days_in_prev_month = (
            date(next_year, next_month, 1) - date(prev_year, prev_month, 1)
        ).days
        days += days_in_prev_month

    if months < 0:
        years -= 1
        months += 12

    parts = []

    if years > 0:
        parts.append(f"{years} г.")
    if months > 0:
        parts.append(f"{months} мес.")
    if days > 0:
        parts.append(f"{days} дн.")

    return " ".join(parts)