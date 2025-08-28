#!/usr/bin/env python3
import argparse
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests


def _tiered_color(stars: int) -> str:
    stars = max(0, min(50, stars))
    if stars <= 16:
        return "fff779"
    elif stars <= 33:
        return "ffaad4"
    else:
        return "d6b5ff"


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"missing required environment variable: {key}")
    return value


def _badge_url(label: str, stars: int, color: str, style: str = "flat-square") -> str:
    return f"https://img.shields.io/badge/{label}-{stars}%20★-{color.lstrip('#')}?style={style}"


def _fetch_leaderboard(
    year: int,
    board_id: str,
    cookies: Dict[str, str],
    headers: Dict[str, str],
    retries: int = 3,
) -> Dict[str, Any]:
    url = f"https://adventofcode.com/{year}/leaderboard/private/view/{board_id}.json"
    last_exc: Optional[Exception] = None
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            if res.status_code == 404:
                raise FileNotFoundError("leaderboard not found for this year")
            res.raise_for_status()
            ctype = res.headers.get("Content-Type", "")
            if "application/json" not in ctype:
                text = res.text.strip()
                preview = (text[:300] + "…") if len(text) > 300 else text
                raise RuntimeError(
                    f"expected JSON but got '{ctype or 'unknown'}'; "
                    f"server returned:\n{preview}"
                )
            return res.json()
        except (requests.RequestException, RuntimeError) as exc:
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    assert last_exc is not None
    raise last_exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sleep-sec", type=int, default=2)
    args = parser.parse_args()

    session = _require_env("AOC_SESSION")
    board_id = _require_env("AOC_LEADERBOARD_ID")

    cookies = {"session": session}
    ua_owner = os.getenv("AOC_CONTACT", "github.com/http-kennedy")
    headers = {"User-Agent": f"AoC Stars Updater (+{ua_owner})"}

    now = datetime.now()
    latest_event_year = now.year - (0 if now.month >= 12 else 1)
    years = range(latest_event_year, 2015 - 1, -1)

    year_stars: Dict[int, int] = {}

    for year in years:
        try:
            data = _fetch_leaderboard(year, board_id, cookies, headers)

            member_id = os.getenv("AOC_MEMBER_ID") or str(data.get("owner_id"))

            members = data.get("members", {})
            if member_id not in members:
                raise KeyError(
                    f"member id '{member_id}' not found on board '{board_id}' for {year}. "
                    f"Available: {', '.join(members.keys())}"
                )

            stars = int(members[member_id].get("stars", 0))
            if stars:
                year_stars[year] = stars

            time.sleep(args.sleep_sec)

        except FileNotFoundError:
            continue

    total_stars = sum(year_stars.values())
    total_possible = (latest_event_year - 2015 + 1) * 50
    total_normalised = round(total_stars * 50 / max(1, total_possible))

    badges: list[str] = []

    for year, stars in sorted(year_stars.items(), reverse=True):
        color = _tiered_color(stars)
        url = _badge_url(str(year), stars, color)
        badges.append(f"[![{year} stars]({url})](https://adventofcode.com/{year})")

    total_color = _tiered_color(total_normalised)
    total_url = _badge_url("total", total_stars, total_color)
    badges.append(f"[![total stars]({total_url})](https://adventofcode.com)")

    print(" ".join(badges))


if __name__ == "__main__":
    main()
