from django import template

register = template.Library()

@register.filter
def format_currency(value):
    try:
        return '{:,.2f}'.format(value).replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return value
