import unittest
from datetime import date

from providers import chernivtsi

URL = chernivtsi.URL
TODAY = date(2026, 11, 21)


def page(day, rows=None, next_link=False):
    rows = rows or {str(g): "<u>з</u>" * 48 for g in range(1, 13)}
    body = "".join(f'<div id="inf{g}" data-id="{g}">{cells}</div>' for g, cells in rows.items())
    link = '<a href="/shutdowns/?next">Завтра</a>' if next_link else ""
    return f'{link}<div id="gsv"><ul><p>{day:%d.%m.%Y}</p>{body}'


class Collect(unittest.TestCase):
    def test_today_and_tomorrow(self):
        pages = {URL: page(TODAY, next_link=True), URL + "?next": page(date(2026, 11, 22))}
        self.assertEqual(sorted(chernivtsi.collect(pages.__getitem__, TODAY)), ["2026-11-21", "2026-11-22"])

    def test_tomorrow_still_dated_today_keeps_today(self):
        # 21.11 22:19-23:04 the link to tomorrow was up while its page still showed today's date
        pages = {URL: page(TODAY, next_link=True), URL + "?next": page(TODAY)}
        self.assertEqual(list(chernivtsi.collect(pages.__getitem__, TODAY)), ["2026-11-21"])

    def test_broken_tomorrow_still_fails(self):
        broken = {str(g): "<u>з</u>" * 47 for g in range(1, 13)}
        pages = {URL: page(TODAY, next_link=True), URL + "?next": page(date(2026, 11, 22), broken)}
        with self.assertRaises(ValueError):
            chernivtsi.collect(pages.__getitem__, TODAY)

    def test_outdated_today_fails(self):
        with self.assertRaises(ValueError):
            chernivtsi.collect({URL: page(date(2026, 11, 20))}.__getitem__, TODAY)


if __name__ == "__main__":
    unittest.main()
