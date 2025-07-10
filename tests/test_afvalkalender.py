from datetime import UTC, date, datetime
from unittest.mock import patch

import pytest

from afvalkalender.fetcher import WasteFetcher
from afvalkalender.ical import export_ical


def test_parse_dutch_date_valid():
    dt = WasteFetcher.parse_dutch_date("maandag 01 januari", 2024)
    assert dt == date(2024, 1, 1)


def test_parse_dutch_date_invalid():
    with pytest.raises(ValueError):
        WasteFetcher.parse_dutch_date("maandag 32 januari", 2024)


def test_categorize():
    assert WasteFetcher.categorize("GFT bak") == "GFT"
    assert WasteFetcher.categorize("Papier en karton") == "Papier en karton"
    assert WasteFetcher.categorize("  restafval ") == "Restafval"


def test_url():
    f = WasteFetcher("1234AB", 56)
    assert f._url(2024) == "https://mijnafvalwijzer.nl/nl/1234AB/56/#jaar-2024"


class DummyResponse:
    def __init__(self, data: bytes):
        self.data = data

    def read(self) -> bytes:
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_fetch_parses_html():
    html = b"""
    <div id='jaar-2024'>
      <a class='wasteInfoIcon'>
        <span class='span-line-break'>maandag 01 januari</span>
        <span class='afvaldescr'>gft</span>
      </a>
    </div>
    """
    f = WasteFetcher("1234AB", 56)
    with patch("afvalkalender.fetcher.urlopen", return_value=DummyResponse(html)):
        items = f.fetch(2024)
    assert items == [(date(2024, 1, 1), "GFT")]


def test_export_ical(tmp_path):
    items = [(date(2024, 1, 1), "PMD")]
    target = tmp_path / "out.ics"
    fixed = datetime(2023, 12, 31, tzinfo=UTC)

    class DummyDateTime:
        @staticmethod
        def now(tz=None):
            return fixed

    with patch("afvalkalender.ical.datetime", DummyDateTime):
        export_ical(str(target), items, "1234AB", 56)
    text = target.read_text().splitlines()
    assert text[0] == "BEGIN:VCALENDAR"
    assert any(line.startswith("DTSTART;VALUE=DATE:20240101") for line in text)
