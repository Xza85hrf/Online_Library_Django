from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value

@register.filter(name='addclass')
def addclass(field, css_class):
    """Adds a CSS class to a Django form field."""
    return field.as_widget(attrs={"class": css_class})
