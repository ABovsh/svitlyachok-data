"""Collect one regional feed. Publish only complete, changed schedules."""
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from providers import chernivtsi

PROVIDERS = {"chernivtsi": chernivtsi.collect}
# "checked" is refreshed at least this often, so readers can tell a quiet day from a stopped collector.
HEARTBEAT = timedelta(minutes=55)


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "Svitlyachok regional schedules"}), timeout=25) as res:
        body = res.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("Schedule exceeds size limit")
        return body.decode("utf-8")


def update(region):
    now = datetime.now(ZoneInfo("Europe/Kyiv"))
    days = PROVIDERS[region](fetch, now.date())
    target = Path("data") / (region + ".json")
    old = json.loads(target.read_text()) if target.exists() else {}
    same = old.get("days") == days
    if same and "checked" in old and now - datetime.fromisoformat(old["checked"]) < HEARTBEAT:
        return
    stamp = now.isoformat(timespec="seconds")
    output = {"region": region, "updated": old["updated"] if same else stamp, "checked": stamp, "days": days}
    target.parent.mkdir(exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(output, indent=2) + "\n")
    temp.replace(target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("region", nargs="?", choices=PROVIDERS)
    args = parser.parse_args()
    failures = []
    for region in [args.region] if args.region else PROVIDERS:
        try:
            update(region)
        except (OSError, ValueError, KeyError) as error:
            failures.append(f"{region}: {error}")
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
