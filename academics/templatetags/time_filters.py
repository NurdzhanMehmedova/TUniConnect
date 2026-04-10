from django import template
from django.utils.timezone import now

register = template.Library()

@register.filter
def time_since(value):
    diff = now() - value

    if diff.days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            return "преди малко"
        return f"преди {hours} ч."
    elif diff.days == 1:
        return "преди 1 ден"
    elif diff.days < 7:
        return f"преди {diff.days} дни"
    elif diff.days < 30:
        return f"преди {diff.days // 7} седм."
    else:
        return f"преди {diff.days // 30} мес."