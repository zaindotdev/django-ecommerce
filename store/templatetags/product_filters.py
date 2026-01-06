from django import template
import math

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key.
    Usage: {{ mydict|get_item:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def star_rating(rating):
    """
    Convert a float rating (0.5 to 5.0) into a list of star types.
    Returns a list of tuples: [(star_type, index), ...]
    star_type can be 'full', 'half', or 'empty'
    """
    if not rating:
        rating = 0
    
    rating = float(rating)
    full_stars = int(rating)
    has_half = (rating - full_stars) >= 0.5
    
    stars = []
    for i in range(1, 6):
        if i <= full_stars:
            stars.append('full')
        elif i == full_stars + 1 and has_half:
            stars.append('half')
        else:
            stars.append('empty')
    
    return stars
