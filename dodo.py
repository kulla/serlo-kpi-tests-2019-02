"""Dodo file for analysing the Serlo history."""

from itertools import count

import requests

from pyquery import PyQuery

TIMEOUT = 30*60

def get_history_page(page_number):
    """Returns the page `<page_number>` of the Serlo history as a
    PyQuery object. This function raises an exception iff the HTTP response
    status is not 200."""
    assert isinstance(page_number, int)
    assert page_number > 0

    req = requests.get("https://de.serlo.org/event/history",
                       params={"page": page_number})

    if req.status_code != 200:
        raise requests.HTTPError("Status '%s %s' while fetching '%s'" % \
                                 (req.status, req.reason, req.url))

    return PyQuery(req.text)

def get_max_page_number():
    """Returns the maximal page number of the Serlo history."""

    # Go through exponentially increasing pages of the Serlo history
    for page_number_exp in count(11):
        page_number = 2**page_number_exp
        page = get_history_page(page_number)

        # Parse the value "Seite XY" in the page header
        nr_in_page = page("div.page-header > h1 > small").text()
        nr_in_page = int(nr_in_page.lstrip("Seite "))

        # If the parsed page number is smaller than the page number used as a
        # parameter in the HTTP request, then this page number is the currently
        # maximal page number
        if nr_in_page < page_number:
            return nr_in_page

    raise ValueError("Maximal page number not found.")
