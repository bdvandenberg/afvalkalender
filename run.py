from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import locale
import icalendar
import sys

postcode, huisnummer = sys.argv[1], sys.argv[2]

def is_plastic(soup):
    """Return ``True`` when the element contains plastic waste info."""
    if soup.find("p", {"class": "plastic"}) is not None:
        return True
    return False

def get_plastic(soup):
    res = soup.find("p", {"class": "plastic"})
    # Split the text into lines and remove empty parts/whitespace
    return [line.strip() for line in res.text.split("\n") if line.strip()]

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

url = "http://mijnafvalwijzer.nl"
# postcode = "3997MH"
# huisnummer = 63
jaar = 2025

res = requests.get(url=f"{url}/nl/{postcode}/{huisnummer}/#jaar-{jaar}")
soup = BeautifulSoup(res.content, "html.parser")

dates = soup.find_all("a", {"class":"wasteInfoIcon textDecorationNone"})
ls = []
for date in dates:
    if is_plastic(date):
        datum, afval = get_plastic(date)
    else:
        datum = date.find("span", {"class": "span-line-break"}).text.strip()
        afval = date.find("span", {"class": "afvaldescr"}).text.strip()

    dt = datetime.strptime(datum.strip(), "%A %d %B %Y")
    ls.append((dt.date(), afval))

# Create calendar
cal = icalendar.Calendar()
cal.add('prodid', f'afvalkalender {postcode} {huisnummer}')
cal.add('version', '2.0')
cal.add("X-WR-CALNAME", f"Afvalkalender {jaar} - {postcode} {huisnummer}")

for n, (datum, afval) in enumerate(ls):
    if datum.year != jaar:
        continue
    event = icalendar.Event()
    event.add("dtstamp", datetime.now())
    event.add("uid", n)
    event.add('summary', afval)
    event.add('dtstart', datum)
    alarm_6h_before = icalendar.Alarm()
    alarm_6h_before.add('action', 'DISPLAY')
    alarm_6h_before.add('trigger', timedelta(hours=-6))
    alarm_6h_before.add('description', '')
    alarm_6h_after = icalendar.Alarm()
    alarm_6h_after.add('action', 'DISPLAY')
    alarm_6h_after.add('trigger', timedelta(hours=6))
    alarm_6h_after.add('description', '')
    event.add_component(alarm_6h_before)
    event.add_component(alarm_6h_after)
    cal.add_component(event)

with open('afval.ics', 'wb') as f:
    f.write(cal.to_ical())
