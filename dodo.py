"""Dodo file for analysing the Serlo history."""

import itertools
import datetime

import requests

from doit.tools import timeout
from pyquery import PyQuery

DOIT_TIMEOUT = timeout(datetime.timedelta(minutes=60))

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

def get_history_max_page_number():
    """Returns the maximal page number of the Serlo history."""

    # Go through pages of the Serlo history with exponentially increased page
    # number
    for page_number_exp in itertools.count(11):
        # Load Serlo history page
        page_number = 2**page_number_exp
        page = get_history_page(page_number)

        # Parse the value "Seite XY" in the page header
        number_in_page = int(page("div.page-header > h1 > small").text()\
                             .lstrip("Seite "))

        # If the parsed page number is smaller than the requested page number,
        # then the paresed page number is the maximal page number
        if number_in_page < page_number:
            return {"history_max_page_number": number_in_page}

    # This command shall not be reachable
    raise ValueError("Maximal page number not found.")

def task_history_max_page_number():
    """Creates a task for computing the maximal page number of the Serlo
    history."""
    return {"actions": (get_history_max_page_number,),
            "uptodate": [DOIT_TIMEOUT]}
