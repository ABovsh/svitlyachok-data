"""Read the operator's dated half-hour grid."""
import re
from datetime import datetime, timedelta

URL = "https://oblenergo.cv.ua/shutdowns/"
GROUPS = {str(i) for i in range(1, 13)}
CELLS = {"<u>з</u>": "1", "<o>в</o>": "0", "<s>мз</s>": "3"}


def parse(html, expected):
    header = re.search(r'<div\s+id="gsv"[^>]*>\s*<ul>\s*<p>\s*(\d{2}\.\d{2}\.\d{4})\s*</p>', html)
    if not header or datetime.strptime(header[1], "%d.%m.%Y").date() != expected:
        raise ValueError("Missing or outdated schedule date")
    rows = {}
    for row in re.finditer(r'<div id="inf(\d+)" data-id="(\d+)">(.*?)</div>', html[header.end():], re.S):
        group, number, content = row.groups()
        cells = re.findall(r'<[uos]>[^<]*</[uos]>', content)
        if group != number or group in rows or len(cells) != 48 or ''.join(cells) != re.sub(r'\s+', '', content):
            raise ValueError("Invalid schedule row")
        rows[group] = ''.join(CELLS[cell.lower()] for cell in cells)
    if rows.keys() != GROUPS:
        raise ValueError("Incomplete group list")
    return rows


def collect(fetch, today):
    html = fetch(URL)
    days = {today.isoformat(): parse(html, today)}
    if 'href="/shutdowns/?next"' in html:
        tomorrow = today + timedelta(days=1)
        days[tomorrow.isoformat()] = parse(fetch(URL + '?next'), tomorrow)
    return days
