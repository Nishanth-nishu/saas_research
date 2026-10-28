"""Fill message templates from lead fields without inventing anything that isn't on the lead."""
from __future__ import annotations

import sqlite3


def first_name(lead: sqlite3.Row | dict) -> str:
    name = (lead["name"] or "").strip()
    return name.split()[0].title() if name else "there"


def topic(lead: sqlite3.Row | dict) -> str:
    course, country = lead["course_interest"], lead["country_interest"]
    if course and country:
        return f"{course} in {country}"
    return course or (f"studying in {country}" if country else "your plans")


def fill(template: str, lead: sqlite3.Row | dict, org_name: str) -> str:
    t = topic(lead)
    about = f" about {t}" if t != "your plans" else ""
    return template.format(first_name=first_name(lead), org_name=org_name, topic=t, about=about,
                           course=lead["course_interest"] or "", country=lead["country_interest"] or "")
