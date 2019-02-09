"""Dodo file for analysing the Serlo history."""

import itertools
import datetime
import os

from math import ceil, log10

import requests

from doit.tools import timeout
from pyquery import PyQuery

DOIT_TIMEOUT = timeout(datetime.timedelta(minutes=60))

HISTORY_EVENTS_PER_PAGE = 100

MAX_EVENTS = 1000000
MAX_FILES_PER_DIRECTORY = 100

TARGET_DATA = "data"
TARGET_HISTORY = os.path.join(TARGET_DATA, "history")

def target_history_page(page_number):
    """Returns the path to the file where the history page with the page
    number `page_number` shall be stored."""
    max_file_number = MAX_EVENTS / HISTORY_EVENTS_PER_PAGE
    max_dir_number = max_file_number / MAX_FILES_PER_DIRECTORY

    file_number_width = ceil(log10(max_file_number))
    dir_number_width = ceil(log10(max_dir_number))

    file_number = str(page_number).zfill(file_number_width)
    dir_number = int(page_number / MAX_FILES_PER_DIRECTORY)
    dir_number = str(dir_number).zfill(dir_number_width)

    return os.path.join(TARGET_HISTORY, "pages", dir_number,
                        "serlo-history-page" + file_number + ".html")

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

def get_history_information():
    """Query information about the the Serlo history. It returns a dictionary
    containing the follwing information:
        
        last_page_number - Number of the last page
        last_page_events - Number of events on the last page
        events_length    - Total number of events
    """

    # Go through pages of the Serlo history with exponentially increased page
    # number in order to find the last page
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
            # Calculate information about the Serlo history
            last_page_number = number_in_page
            last_page_events_length = len(page("#content-layout > ul > li"))
            events_length = (last_page_number - 1) * HISTORY_EVENTS_PER_PAGE \
                                + last_page_events_length

            return {"last_page_number": last_page_number,
                    "last_page_events": last_page_events_length,
                    "events_length": events_length}

    # This command shall not be reachable
    raise ValueError("Maximal page number not found.")

def task_history_information():
    """Creates a task for querying information about the Serlo history."""
    return {"actions": (get_history_information,),
            "uptodate": [DOIT_TIMEOUT]}

def task_all_history_page_targets():
    """Task for computing all possible history pages."""
    def all_history_pages(last_page_number):
        return {"file_dep": [target_history_page(n)
                             for n in range(1, last_page_number + 1)]}

    return {"actions": [all_history_pages],
            "getargs": {"last_page_number": ("history_information",
                                             "last_page_number")}}

def task_history_json_file():
    """Creates a json file containing all events of the Serlo history."""
    def create_history_json_file(task):
        pass

    return {"actions": (create_history_json_file,),
            "calc_dep": ["all_history_page_targets"]}
