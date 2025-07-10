import locale
import sys
from datetime import datetime

from afvalkalender import WasteFetcher, export_ical

# Ensure month and weekday names are parsed/created in Dutch.  Not all systems
# provide the ``nl_NL`` locale, so fall back gracefully when it is unavailable.
try:
    locale.setlocale(locale.LC_TIME, 'nl_NL')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, '')


def main(argv: list[str] | None = None):
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 2:
        print("Usage: python run.py <postcode> <huisnummer>")
        return
    postcode, huisnummer_str = argv
    try:
        huisnummer = int(huisnummer_str)
    except ValueError:
        print("Huisnummer must be a number")
        return
    year = datetime.now().year
    fetcher = WasteFetcher(postcode, huisnummer)
    items = fetcher.fetch(year)
    for dt, cat in items:
        print(dt, cat)
    export_ical(f"afvalkalender {postcode}-{huisnummer}.ics", items, postcode, huisnummer)


if __name__ == "__main__":
    main()

