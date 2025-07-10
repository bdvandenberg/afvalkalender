from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import locale
import icalendar
import sys

postcode, huisnummer = sys.argv[1], sys.argv[2]

def is_plastic(soup):
    if soup.find("p", {"class":"plastic"}) is not None:
        return True

def get_plastic(soup):
    res = soup.find("p", {"class":"plastic"})
    return res.text.split("\n")

locale.setlocale(locale.LC_TIME, 'nl_NL')

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
        datum = date.find("span", {"class":"span-line-break"}).text
        afval = date.find("span", {"class":"afvaldescr"}).text

    dt = datetime.strptime(datum, "%A %d %B %Y")
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

f = open('afval.ics', 'wb')
f.write(cal.to_ical())
f.close()