#!/usr/bin/env python3

import argparse
import colorsys
import os
import time
from datetime import datetime
from typing import Dict, Tuple

import requests


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    to_255 = lambda x: max(0, min(255, round(x * 255)))
    return f"{to_255(r):02x}{to_255(g):02x}{to_255(b):02x}"

def _dracula_tiered_color(stars: int) -> str:
    stars = max(0, min(50, stars))

    if stars <= 16:
        return "fefcbf"
    elif stars <= 33:
        return "ffcce5"
    else:
        return "e2d7fc"


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"missing required environment variable: {key}")
    return value


def _badge_url(label: str, stars: int, color: str, style: str = "flat-square") -> str:
    return f"https://img.shields.io/badge/{label}-{stars}%20★-{color.lstrip('#')}?style={style}"


def _fetch_leaderboard(year: int, uid: str,
                       cookies: Dict[str, str],
                       headers: Dict[str, str]) -> Dict:
    url = f"https://adventofcode.com/{year}/leaderboard/private/view/{uid}.json"
    res = requests.get(url, headers=headers, cookies=cookies, timeout=10)
    res.raise_for_status()
    return res.json()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sleep-sec", type=int, default=2,
                        help="delay between leaderboard requests")
    args = parser.parse_args()

    session = _require_env("AOC_SESSION")
    uid = _require_env("AOC_UID")

    cookies = {"session": session}
    headers = {"User-Agent": "https://github.com/http-kennedy"}

    now = datetime.now()
    latest_event_year = now.year if now.month >= 12 else now.year - 1
    years = range(latest_event_year, 2014, -1)

    year_stars: Dict[int, int] = {}

    for year in years:
        try:
            data = _fetch_leaderboard(year, uid, cookies, headers)
            stars = data["members"][uid]["stars"]
            if stars:
                year_stars[year] = stars
            time.sleep(args.sleep_sec)
        except requests.HTTPError as exc:
            if exc.response.status_code == 404:
                continue
            raise

    total_stars = sum(year_stars.values())
    total_possible = (latest_event_year - 2015 + 1) * 50
    total_normalised = round(total_stars * 50 / total_possible)

    badges: list[str] = []

    for year, stars in sorted(year_stars.items(), reverse=True):
        color = _dracula_tiered_color(stars)
        url = _badge_url(str(year), stars, color)
        badges.append(f"[![{year} stars]({url})](https://adventofcode.com/{year})")

    total_color = _dracula_tiered_color(total_normalised)
    total_url = _badge_url("total", total_stars, total_color)
    badges.append(f"[![total stars]({total_url})](https://adventofcode.com)")

    print(" ".join(badges))


if __name__ == "__main__":
    main()

