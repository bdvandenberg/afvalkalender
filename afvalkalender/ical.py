from datetime import UTC, date, datetime


def export_ical(filename: str, items: list[tuple[date, str]], postcode: str, huisnummer: int):
    """Write the waste data to an iCalendar file."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//afvalkalender//{postcode}-{huisnummer}//EN",
        f"X-WR-CALNAME:Afvalkalender {postcode} {huisnummer}",
    ]
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

