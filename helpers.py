#!/usr/bin/env python3

def short_region(txt):
    """
    Return shortened version of region or country/region, useful for UI elements
    """
    if txt == 'England - Yorkshire and the Humber':
        return 'England - Yorks/Humber'
    elif txt == 'Yorkshire and the Humber':
        return 'Yorks/Humber'
    else:
        return txt


