from bs4 import BeautifulSoup
from datetime import datetime, date, UTC
import locale
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys

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


class WasteFetcher:
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

    def __init__(self, postcode: str, huisnummer: int):
        self.postcode = postcode
        self.huisnummer = huisnummer

    @staticmethod
    def parse_dutch_date(text: str, year: int) -> date:
        """Parse a date string like 'maandag 01 januari' for ``year``."""
        parts = text.lower().split()
        if len(parts) < 3:
            raise ValueError("Unrecognized date format")
        day = int(parts[1])
        month = WasteFetcher.MONTHS.get(parts[2])
        if not month:
            raise ValueError("Unknown month")
        return date(year, month, day)

    @staticmethod
    def categorize(name: str) -> str:
        """Return one of the known waste categories for ``name``."""
        text = name.lower()
        if (
            "pmd" in text
            or "plastic" in text
            or "metaal" in text
            or "drankkarton" in text
        ):
            return "PMD"
        if "papier" in text or "karton" in text:
            return "Papier en karton"
        if (
            "gft" in text
            or "groente" in text
            or "fruit" in text
            or "tuin" in text
        ):
            return "GFT"
        if "rest" in text:
            return "Restafval"
        return name.strip()

    def _url(self, year: int) -> str:
        return f"{BASE_URL}/nl/{self.postcode}/{self.huisnummer}/#jaar-{year}"

    def fetch(self, year: int) -> list[tuple[date, str]]:
        req = Request(self._url(year), headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urlopen(req) as res:
                html = res.read()
        except HTTPError as exc:
            print(f"Failed to fetch {self.postcode}-{self.huisnummer}: {exc}")
            return []
        soup = BeautifulSoup(html, "html.parser")
        section = soup.find(id=f"jaar-{year}")
        if not section:
            return []
        results = []
        for item in section.select("a.wasteInfoIcon"):
            datum_tag = item.find("span", class_="span-line-break")
            afval_tag = item.find("span", class_="afvaldescr")
            if datum_tag is None or afval_tag is None:
                continue
            datum = datum_tag.get_text(strip=True)
            afval = afval_tag.get_text(strip=True)
            try:
                dt = self.parse_dutch_date(datum, year)
            except Exception:
                continue
            results.append((dt, self.categorize(afval)))
        return results


def export_ical(filename: str, items: list[tuple[date, str]], postcode: str, huisnummer: int):
    """Write the waste data to an iCalendar file."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//afvalkalender//{postcode}-{huisnummer}//EN",
        f"X-WR-CALNAME:Afvalkalender {postcode} {huisnummer}",
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    for dt, cat in items:
        uid = f"{postcode}-{huisnummer}-{dt.isoformat()}"
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{dt.strftime('%Y%m%d')}",
            f"SUMMARY:{cat}",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"TRIGGER;VALUE=DATE-TIME:{dt.strftime('%Y%m%dT070000')}",
            f"DESCRIPTION:{cat}",
            "END:VALARM",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    with open(filename, "w") as fh:
        fh.write("\n".join(lines))


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
