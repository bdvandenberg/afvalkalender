from bs4 import BeautifulSoup
from datetime import datetime, date
import locale
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys

postcode, huisnummer = sys.argv[1:3] if len(sys.argv) > 2 else (None, None)

# Ensure month and weekday names are parsed/created in Dutch.  Not all
# systems provide the ``nl_NL`` locale, so fall back gracefully when it is
# unavailable.
try:
    locale.setlocale(locale.LC_TIME, 'nl_NL')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, '')

BASE_URL = "https://mijnafvalwijzer.nl"

MONTHS = {
    "januari": 1,
    "februari": 2,
    "maart": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "augustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}

def parse_dutch_date(text, year):
    """Parse a date string like 'maandag 01 januari' for ``year``."""
    parts = text.lower().split()
    if len(parts) < 3:
        raise ValueError("Unrecognized date format")
    day = int(parts[1])
    month = MONTHS.get(parts[2])
    if not month:
        raise ValueError("Unknown month")
    return date(year, month, day)


def categorize(name):
    """Return one of the known waste categories for ``name``."""
    text = name.lower()
    if "pmd" in text or "plastic" in text or "metaal" in text or "drankkarton" in text:
        return "PMD"
    if "papier" in text or "karton" in text:
        return "Papier en karton"
    if "gft" in text or "groente" in text or "fruit" in text or "tuin" in text:
        return "GFT"
    if "rest" in text:
        return "Restafval"
    return name.strip()


def fetch_waste(postcode, huisnummer, year):
    req = Request(
        f"{BASE_URL}/nl/{postcode}/{huisnummer}/#jaar-{year}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        with urlopen(req) as res:
            html = res.read()
    except HTTPError as exc:
        print(f"Failed to fetch {postcode}-{huisnummer}: {exc}")
        return []
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find(id=f"jaar-{year}")
    if not section:
        return []
    results = []
    for date in section.select("a.wasteInfoIcon"):
        datum_tag = date.find("span", class_="span-line-break")
        afval_tag = date.find("span", class_="afvaldescr")
        if datum_tag is None or afval_tag is None:
            continue
        datum = datum_tag.get_text(strip=True)
        afval = afval_tag.get_text(strip=True)
        try:
            dt = parse_dutch_date(datum.strip(), year)
        except Exception:
            continue
        results.append((dt, categorize(afval)))
    return results


def main():
    year = datetime.now().year
    results = fetch_waste(postcode, huisnummer, year)
    for datum, afval in results:
        print(datum, afval)

if __name__ == "__main__":
    main()
