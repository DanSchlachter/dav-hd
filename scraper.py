#!/usr/bin/env python3
"""
Alpenverein Heidelberg Tour Scraper

Scrapes tour information from the Alpenverein Heidelberg website and tracks changes.
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List
import requests
from bs4 import BeautifulSoup


def fetch_tour_page(url: str) -> str:
    """
    Fetch the HTML content from the tour search results page.
    
    Args:
        url: The URL to fetch
        
    Returns:
        HTML content as string
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    # Explicitly set encoding to UTF-8 to handle German umlauts correctly
    response.encoding = 'utf-8'
    return response.text


def parse_tours(html: str) -> List[Dict]:
    """
    Parse tour entries from the HTML content.
    
    Args:
        html: HTML content as string
        
    Returns:
        List of tour dictionaries
    """
    soup = BeautifulSoup(html, 'html.parser')
    tours = []
    
    # Find all tour entries - they are in <p> tags with background-color:silver
    tour_headers = soup.find_all('p', style=lambda value: value and 'background-color:silver' in value)
    
    for header in tour_headers:
        tour = {}
        
        # Extract date range and title from the header
        # Line structure: [empty, date, title, tour_type, empty...]
        title_parts = [part.strip() for part in header.get_text().split('\n') if part.strip()]
        
        # First non-empty line contains the date
        if len(title_parts) >= 1:
            date_text = title_parts[0]
            # Parse begin and end dates
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{2})\s*(?:-\s*(\d{2}\.\d{2}\.\d{2}))?', date_text)
            if date_match:
                tour['begin_date'] = date_match.group(1)
                tour['end_date'] = date_match.group(2) if date_match.group(2) else date_match.group(1)
        
        # Second non-empty line contains the actual tour title/name
        if len(title_parts) >= 2:
            tour['title'] = title_parts[1]
        
        # Third non-empty line contains the tour type (e.g., "Führungstour-7138")
        if len(title_parts) >= 3:
            tour['tour_type'] = title_parts[2]
        
        # Extract anchor/ID
        anchor = header.find('a', {'name': True})
        if anchor:
            tour['id'] = anchor['name']
            tour['url'] = f"https://www.alpenverein-heidelberg.de/index.php?inhalt=tourensucheergebnis#{tour['id']}"
        
        # Find the next sibling paragraphs for details
        next_elem = header.find_next_sibling()
        description_parts = []
        
        while next_elem and next_elem.name == 'p':
            # Check if this is the start of a new tour
            if next_elem.get('style') and 'background-color:silver' in next_elem.get('style', ''):
                break
            
            text = next_elem.get_text(strip=True)
            
            # Extract leader
            if text.startswith('Leitung:'):
                email_link = next_elem.find('a', href=lambda x: x and x.startswith('mailto:'))
                if email_link:
                    tour['leader'] = email_link.get_text(strip=True)
                    # Also extract any additional leaders
                    full_text = next_elem.get_text()
                    tour['leader_full'] = full_text.replace('Leitung:', '').strip()
            
            # Extract registration status
            elif 'Anmeldestatus:' in text:
                img = next_elem.find('img')
                if img and img.get('alt'):
                    tour['registration_status'] = img['alt']
                tour['registration_text'] = text.replace('Anmeldestatus:', '').strip()
            
            next_elem = next_elem.find_next_sibling()
        
        # Find the collapsible div with more details
        if 'id' in tour:
            # The div ID is 'b' + number (tour['id'] is like 't7138', so we replace 't' with 'b')
            div_id = 'b' + tour['id'][1:]
            detail_div = soup.find('div', {'id': div_id})
            if detail_div:
                # Get full description text including all paragraphs and lists
                detail_text = detail_div.get_text(separator='\n', strip=True)
                tour['description_full'] = detail_text
                
                # Also get structured description with HTML preserved
                tour['description_html'] = str(detail_div)
                
                # Extract specific fields from description
                for p in detail_div.find_all('p'):
                    p_text = p.get_text(strip=True)
                    if p_text.startswith('Ort:'):
                        tour['location'] = p_text.replace('Ort:', '').strip()
                    elif p_text.startswith('Anforderungen:'):
                        tour['requirements'] = p_text.replace('Anforderungen:', '').strip()
                    elif p_text.startswith('max. Teilnehmerzahl:'):
                        tour['max_participants'] = p_text.replace('max. Teilnehmerzahl:', '').strip()
                    elif p_text.startswith('Treffpunkt:'):
                        tour['meeting_point'] = p_text.replace('Treffpunkt:', '').strip()
                    elif p_text.startswith('Anmeldeschluss:'):
                        tour['registration_deadline'] = p_text.replace('Anmeldeschluss:', '').strip()
                    elif p_text.startswith('Kursgeb'):
                        tour['course_fee'] = p_text.strip()
                    elif p_text.startswith('Vorbesprechung:'):
                        tour['pre_meeting'] = p_text.replace('Vorbesprechung:', '').strip()
                    elif p_text.startswith('Ausrüstung:') or p_text.startswith('Ausruestung:'):
                        tour['equipment'] = p_text.replace('Ausrüstung:', '').replace('Ausruestung:', '').strip()
        
        # Only add tour if it has at least a title and ID
        if 'title' in tour and 'id' in tour:
            tours.append(tour)
    
    return tours


def load_previous_data(filename: str = 'tours.json') -> Dict:
    """
    Load the previous run's data.
    
    Args:
        filename: JSON file to load
        
    Returns:
        Dictionary with previous tour data
    """
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_data(data: Dict, filename: str = 'tours.json'):
    """
    Save tour data to JSON file.
    
    Args:
        data: Dictionary containing tour data
        filename: JSON file to save to
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _normalize_value(v):
    """Normalize values for comparison (trim and collapse whitespace for strings)."""
    if isinstance(v, str):
        # Collapse all whitespace runs to a single space and strip
        return re.sub(r"\s+", " ", v).strip()
    return v


def _diff_fields(prev: Dict, curr: Dict) -> Dict:
    """Return a mapping of changed fields with from/to values."""
    changes = {}
    # Fields we care about in deltas (skip very verbose HTML)
    preferred_keys = {
        'begin_date','end_date','title','tour_type','leader','leader_full',
        'registration_status','registration_text','location','requirements',
        'max_participants','meeting_point','registration_deadline','course_fee',
        'equipment','pre_meeting','description_full'
    }
    keys = preferred_keys.union(set(prev.keys())).union(set(curr.keys()))
    for k in sorted(keys):
        if k == 'description_html':
            continue  # too noisy
        pv = prev.get(k)
        cv = curr.get(k)
        if _normalize_value(pv) != _normalize_value(cv):
            changes[k] = {'from': pv, 'to': cv}
    return changes


def compute_deltas(previous: Dict, current: List[Dict]) -> Dict:
    """
    Compute changes between previous and current tour data.
    
    Args:
        previous: Previous run's data
        current: Current tour list
        
    Returns:
        Dictionary with added, removed, and modified tours
    """
    previous_tours = {tour['id']: tour for tour in previous.get('tours', [])}
    current_tours = {tour['id']: tour for tour in current}
    
    deltas = {
        'added': [],
        'removed': [],
        'modified': []
    }
    
    # Find added and modified tours
    for tour_id, tour in current_tours.items():
        if tour_id not in previous_tours:
            deltas['added'].append(tour)
        else:
            prev = previous_tours[tour_id]
            if tour != prev:
                changed_fields = _diff_fields(prev, tour)
                deltas['modified'].append({
                    'id': tour_id,
                    'changed_fields': changed_fields,
                    'previous': prev,
                    'current': tour
                })
    
    # Find removed tours
    for tour_id, tour in previous_tours.items():
        if tour_id not in current_tours:
            deltas['removed'].append(tour)
    
    return deltas


def main():
    """Main execution function."""
    url = 'https://www.alpenverein-heidelberg.de/index.php?inhalt=tourensucheergebnis'
    
    print(f"Fetching tours from {url}...")
    html = fetch_tour_page(url)
    
    print("Parsing tour data...")
    tours = parse_tours(html)
    print(f"Found {len(tours)} tours")
    
    # Load previous data
    previous_data = load_previous_data()
    
    # Create current data structure
    current_data = {
        'timestamp': datetime.now().isoformat(),
        'url': url,
        'tour_count': len(tours),
        'tours': tours
    }
    
    # Save current data
    save_data(current_data, 'tours.json')
    print("Saved current data to tours.json")
    
    # Compute and save deltas
    if previous_data:
        print("\nComputing deltas...")
        deltas = compute_deltas(previous_data, tours)
        
        delta_data = {
            'timestamp': datetime.now().isoformat(),
            'previous_timestamp': previous_data.get('timestamp'),
            'summary': {
                'added': len(deltas['added']),
                'removed': len(deltas['removed']),
                'modified': len(deltas['modified'])
            },
            'changes': deltas
        }
        
        save_data(delta_data, 'tours_delta.json')
        print(f"Saved deltas to tours_delta.json:")
        print(f"  - Added: {delta_data['summary']['added']}")
        print(f"  - Removed: {delta_data['summary']['removed']}")
        print(f"  - Modified: {delta_data['summary']['modified']}")

        # Also write human-readable markdown log entry for repo traceability
        # File: changes/CHANGES-YYYY-MM-DD.md (append per day)
        day = datetime.now().strftime('%Y-%m-%d')
        os.makedirs('changes', exist_ok=True)
        md_path = os.path.join('changes', f'CHANGES-{day}.md')
        with open(md_path, 'a', encoding='utf-8') as md:
            md.write(f"\n## {datetime.now().isoformat()}\n")
            md.write(f"Added: {delta_data['summary']['added']}, Removed: {delta_data['summary']['removed']}, Modified: {delta_data['summary']['modified']}\n\n")
            if deltas['added']:
                md.write("### Added\n")
                for t in deltas['added']:
                    md.write(f"- {t.get('id')} · {t.get('begin_date')}–{t.get('end_date')} · {t.get('title')}\n")
            if deltas['removed']:
                md.write("\n### Removed\n")
                for t in deltas['removed']:
                    md.write(f"- {t.get('id')} · {t.get('begin_date')}–{t.get('end_date')} · {t.get('title')}\n")
            if deltas['modified']:
                md.write("\n### Modified\n")
                for m in deltas['modified']:
                    tcur = m['current']
                    md.write(f"- {m['id']} · {tcur.get('begin_date')}–{tcur.get('end_date')} · {tcur.get('title')}\n")
                    # Show field-level changes
                    changes = m.get('changed_fields', {})
                    for field, vals in changes.items():
                        md.write(f"  - {field}: '{vals.get('from')}' → '{vals.get('to')}'\n")
            md.write("\n---\n")
            
        print(f"Appended human-readable delta log to {md_path}")
    else:
        print("\nNo previous data found - this is the first run")


if __name__ == '__main__':
    main()
