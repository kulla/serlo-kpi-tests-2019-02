"""Downloads / Updates all events and saves them in `serlo_events.csv`."""

import os
import itertools
import json
import time

import requests

from pyquery import PyQuery

TIMEOUT = 60*60
HISTORY_EVENTS_PER_PAGE = 100

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")


def cache(cache_file_func):
    """Decorator for a function so that its results are getting cached in a
    JSON file. The content of the cached JSON is returned, when it is not
    older then `TIMEOUT`. The function `cache_file_func` returns the path
    to the file where the result shall be stored, when the function's arguments
    are passed to it. In case the cache file does not exist or is older than
    `TIMEOUT` the actual function is called and its result is returned after it
    was stored in the cache."""
    def cache_decorator(func):
        def cached_function(*args, **kwargs):
            cached_file = os.path.join(CACHE_DIR,
                                       cache_file_func(*args, **kwargs))

            if (os.path.exists(cached_file) and
                    time.time() - os.path.getmtime(cached_file) < TIMEOUT):
                with open(cached_file, "r") as cached_file_fd:
                    return json.load(cached_file_fd)
            else:
                result = func(*args, **kwargs)

                os.makedirs(os.path.dirname(cached_file), exist_ok=True)

                with open(cached_file, "w") as cached_file_fd:
                    json.dump(result, cached_file_fd)

                return result

        return cached_function
    return cache_decorator


def get_history_page(page_number):
    """Returns the page `<page_number>` of the Serlo history. This function
    raises an exception iff the HTTP response status is not 200."""
    assert isinstance(page_number, int)
    assert page_number > 0

    req = requests.get("https://de.serlo.org/event/history",
                       params={"page": page_number})

    if req.status_code != 200:
        raise requests.HTTPError("Status '%s %s' while fetching '%s'" %
                                 (req.status, req.reason, req.url))

    return req.text


@cache(lambda: os.path.join(CACHE_DIR, "history_information.json"))
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
        page = PyQuery(get_history_page(page_number))

        # Parse the value "Seite XY" in the page header
        number_in_page = int(page("div.page-header > h1 > small").text()
                             .lstrip("Seite "))

        # If the parsed page number is smaller than the requested page number,
        # then the paresed page number is the maximal page number
        if number_in_page < page_number:
            # Calculate information about the Serlo history
            last_page_number = number_in_page
            last_page_events_length = len(page("#content-layout > ul > li"))
            events_length = ((last_page_number - 1) * HISTORY_EVENTS_PER_PAGE
                             + last_page_events_length)

            return {"last_page_number": last_page_number,
                    "last_page_events": last_page_events_length,
                    "events_length": events_length}

    # This command shall not be reachable
    raise ValueError("Maximal page number not found.")


def run_script():
    """Runs this script."""
    print(get_history_information())


if __name__ == "__main__":
    run_script()
