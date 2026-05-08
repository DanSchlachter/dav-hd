#!/usr/bin/env python3
"""
Alpenverein Heidelberg Tour Scraper (Yolawo API version)

Fetches tour/offer data from the Yolawo booking API and tracks changes.
Replaces the old HTML scraper — no IP blocking, clean JSON.
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

API_URL = "https://api.yolawo.de/widgets/698376bd0d53ced0ad924a59/offers"
TOURS_FILE = "tours.json"
DELTA_FILE = "tours_delta.json"


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_offers() -> List[Dict]:
    """Fetch all offers from the Yolawo API."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; dav-hd-scraper/2.0)",
        "Accept": "application/json",
    }
    resp = requests.get(API_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Normalise
# ---------------------------------------------------------------------------

def description_text(desc: Optional[Dict]) -> str:
    """Extract plain text from a Quill delta description object."""
    if not desc or not isinstance(desc, dict):
        return ""
    ops = desc.get("ops") or []
    return "".join(
        op.get("insert", "") for op in ops if isinstance(op.get("insert"), str)
    ).strip()


def normalise_offer(offer: Dict) -> Dict:
    """Flatten an API offer into a stable, comparable dict."""
    nb = offer.get("nextBookable") or {}
    cap = nb.get("capacity") or {}
    waitlist = nb.get("waitlist") or {}
    date_range = offer.get("dates", {}).get("range", {})
    locations = offer.get("dates", {}).get("locations") or []

    return {
        "id": offer["id"],
        "number": offer.get("number", ""),
        "title": offer.get("title", ""),
        "type": offer.get("type", ""),
        "canceled": offer.get("canceled", False),
        "cancel_reason": offer.get("cancelReason"),
        "categories": sorted(c["name"] for c in (offer.get("categories") or [])),
        "date_from": (date_range.get("from") or "")[:10],
        "date_to": (date_range.get("to") or "")[:10],
        "locations": [loc.get("name", "") for loc in locations],
        "description": description_text(offer.get("description")),
        # nextBookable fields
        "bookable_id": nb.get("id"),
        "bookable_start": (nb.get("start") or "")[:10],
        "bookable_end": (nb.get("end") or "")[:10],
        "free_places": cap.get("freePlaces"),
        "max_places": cap.get("maxLimit"),
        "bookable_places": cap.get("bookablePlaces"),
        "waitlist_active": waitlist.get("active"),
        "bookable_canceled": nb.get("canceled", False),
    }


# ---------------------------------------------------------------------------
# Delta
# ---------------------------------------------------------------------------

def _normalise_value(v):
    if isinstance(v, str):
        return re.sub(r"\s+", " ", v).strip()
    return v


def compute_deltas(previous: Dict, current: List[Dict]) -> Dict:
    prev_map = {t["id"]: t for t in previous.get("tours", [])}
    curr_map = {t["id"]: t for t in current}

    added, removed, modified = [], [], []

    for tid, tour in curr_map.items():
        if tid not in prev_map:
            added.append(tour)
        else:
            changes = {
                k: {"from": prev_map[tid].get(k), "to": tour.get(k)}
                for k in set(list(prev_map[tid].keys()) + list(tour.keys()))
                if _normalise_value(prev_map[tid].get(k)) != _normalise_value(tour.get(k))
            }
            if changes:
                modified.append({
                    "id": tid,
                    "changed_fields": list(changes.keys()),
                    "changes": changes,
                    "current": tour,
                    "previous": prev_map[tid],
                })

    for tid, tour in prev_map.items():
        if tid not in curr_map:
            removed.append(tour)

    return {"added": added, "removed": removed, "modified": modified}


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_previous(filename: str = TOURS_FILE) -> Dict:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(data: Dict, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_markdown_log(deltas: Dict, summary: Dict):
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    os.makedirs("changes", exist_ok=True)
    path = os.path.join("changes", f"CHANGES-{day}.md")
    with open(path, "a", encoding="utf-8") as md:
        md.write(f"\n## {datetime.now(timezone.utc).isoformat()}\n")
        md.write(
            f"Added: {summary['added']}, "
            f"Removed: {summary['removed']}, "
            f"Modified: {summary['modified']}\n\n"
        )
        if deltas["added"]:
            md.write("### Added\n")
            for t in deltas["added"]:
                md.write(f"- {t['id']} · {t['date_from']}–{t['date_to']} · {t['title']}\n")
        if deltas["removed"]:
            md.write("\n### Removed\n")
            for t in deltas["removed"]:
                md.write(f"- {t.get('id', '?')} · {t.get('date_from', '?')}–{t.get('date_to', '?')} · {t.get('title', '?')}\n")
        if deltas["modified"]:
            md.write("\n### Modified\n")
            for m in deltas["modified"]:
                cur = m["current"]
                md.write(f"- {m['id']} · {cur['date_from']}–{cur['date_to']} · {cur['title']}\n")
                for field in m["changed_fields"]:
                    ch = m["changes"][field]
                    md.write(f"  - {field}: {ch['from']!r} → {ch['to']!r}\n")
        md.write("\n---\n")
    print(f"Markdown log written to {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Fetching offers from Yolawo API...")
    raw_offers = fetch_offers()
    print(f"Fetched {len(raw_offers)} offers")

    tours = [normalise_offer(o) for o in raw_offers]

    previous = load_previous()

    current_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": API_URL,
        "tour_count": len(tours),
        "tours": tours,
    }

    save_json(current_data, TOURS_FILE)
    print(f"Saved {len(tours)} tours to {TOURS_FILE}")

    if previous:
        print("Computing deltas...")
        deltas = compute_deltas(previous, tours)
        summary = {
            "added": len(deltas["added"]),
            "removed": len(deltas["removed"]),
            "modified": len(deltas["modified"]),
        }
        delta_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_timestamp": previous.get("timestamp"),
            "summary": summary,
            "changes": deltas,
        }
        save_json(delta_data, DELTA_FILE)
        print(
            f"Delta: +{summary['added']} added, "
            f"-{summary['removed']} removed, "
            f"~{summary['modified']} modified"
        )
        write_markdown_log(deltas, summary)
    else:
        print("No previous data — first run, no delta computed.")
        # Write empty delta so cron job has something to read
        save_json({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_timestamp": None,
            "summary": {"added": 0, "removed": 0, "modified": 0},
            "changes": {"added": [], "removed": [], "modified": []},
        }, DELTA_FILE)


if __name__ == "__main__":
    main()
