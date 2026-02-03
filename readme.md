# Alpenverein Heidelberg Tour Scraper

A Python script that scrapes tour information from the Alpenverein Heidelberg website and tracks changes between runs.

## Features

- Scrapes tour data from https://www.alpenverein-heidelberg.de/index.php?inhalt=tourensucheergebnis
- Extracts comprehensive tour information including:
  - Begin and end dates
  - Title and tour type
  - Description
  - URL to tour details
  - Tour leader information
  - Registration status
  - Location, requirements, meeting point
  - Maximum participants, fees, deadlines
- Compares results with previous run and stores deltas
- Saves data in JSON format for easy processing

## Installation

1. Install Python 3.9 or higher

2. Install required dependencies:
```bash
pip3 install -r requirements.txt
```

## Testing

**⚠️ IMPORTANT: Run tests before every commit!**

Run the test suite to verify everything works correctly:

```bash
python3 test_scraper.py
```

This runs 27 tests covering:
- HTML parsing
- German umlaut handling
- File I/O operations
- Delta computation
- Edge cases and error handling
- Data validation

### Automated Testing

#### Git Pre-commit Hook (Recommended)
Automatically run tests before every commit:

```bash
# Create the hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running tests before commit..."
python3 test_scraper.py
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Please fix the issues before committing."
    exit 1
fi
echo "✅ All tests passed!"
EOF

# Make it executable
chmod +x .git/hooks/pre-commit
```

Now tests will run automatically before every `git commit`. If tests fail, the commit will be blocked.

#### Manual Testing Workflow
Always run tests when:
- ✅ Making changes to scraper.py
- ✅ Modifying parsing logic
- ✅ Adding new features
- ✅ Fixing bugs
- ✅ Before pushing to repository

See [TESTING.md](TESTING.md) for detailed test documentation.

## Usage

Run the scraper:
```bash
python3 scraper.py
```

### First Run
On the first run, the script will:
- Fetch all tours from the website
- Save them to `tours.json`
- Display a message that no previous data was found

### Subsequent Runs
On subsequent runs, the script will:
- Fetch current tours from the website
- Compare with previous data in `tours.json`
- Save new data to `tours.json`
- Save changes to `tours_delta.json`
- Display summary of changes (added/removed/modified tours)

## Output Files

### tours.json
Contains the complete current tour data:
```json
{
  "timestamp": "2026-02-03T11:30:05.622748",
  "url": "https://www.alpenverein-heidelberg.de/index.php?inhalt=tourensucheergebnis",
  "tour_count": 77,
  "tours": [
    {
      "date": "04.02.26, 1 Tage",
      "begin_date": "04.02.26",
      "end_date": "04.02.26",
      "title": "Skitouren Planung Theorie",
      "tour_type": "Ausbildungskurs",
      "id": "t7138",
      "url": "https://www.alpenverein-heidelberg.de/index.php?inhalt=tourensucheergebnis#t7138",
      "leader": "Michael Pfisterer",
      "registration_status": "gruen",
      "location": "Vereinsheim DAV Heidelberg",
      "requirements": "Keine Vorkenntnisse...",
      "max_participants": "8",
      "meeting_point": "Vereinsheim DAV Heidelberg...",
      ...
    }
  ]
}
```

### tours_delta.json
Contains only the changes since the last run:
```json
{
  "timestamp": "2026-02-03T11:30:05.624686",
  "previous_timestamp": "2026-02-03T11:30:01.562244",
  "summary": {
    "added": 2,
    "removed": 1,
    "modified": 3
  },
  "changes": {
    "added": [...],      // New tours not in previous run
    "removed": [...],    // Tours that no longer exist
    "modified": [...]    // Tours with changed information
  }
}
```

## Automating the Scraper

To automatically run the scraper periodically, you can use a cron job:

### macOS/Linux
```bash
# Edit crontab
crontab -e

# Run every day at 6:00 AM
0 6 * * * cd /path/to/dav && /usr/bin/python3 scraper.py

# Run every hour
0 * * * * cd /path/to/dav && /usr/bin/python3 scraper.py
```

### Windows Task Scheduler
1. Open Task Scheduler
2. Create a new task
3. Set trigger (e.g., daily at 6:00 AM)
4. Set action: Run `python3 scraper.py` in the script directory

## Data Fields Extracted

For each tour, the scraper extracts:

- **begin_date**: Start date (DD.MM.YY format)
- **end_date**: End date (DD.MM.YY format)
- **title**: Tour name/title (e.g., "Skitouren Planung Theorie", "Geißler, Puezgruppe in den Dolomiten")
- **tour_type**: Type of tour (e.g., Führungstour-7152, Ausbildungskurs-7138)
- **id**: Unique tour ID (e.g., t7138)
- **url**: Direct link to tour details
- **leader**: Primary tour leader name
- **leader_full**: Complete leader information with additional leaders
- **registration_status**: Status indicator (gruen/gelb/orange/rot)
- **registration_text**: Human-readable registration status
- **description_full**: Full tour description (plain text)
- **description_html**: Full tour description (HTML preserved)
- **location**: Tour location/destination
- **requirements**: Participant requirements
- **max_participants**: Maximum number of participants
- **meeting_point**: Where and when to meet
- **registration_deadline**: Last day to register
- **course_fee**: Fee information (if applicable)
- **equipment**: Required equipment (if specified)
- **pre_meeting**: Pre-meeting information

## German Umlauts

The script correctly handles German umlauts (ä, ö, ü, ß) and special characters by:
- Setting UTF-8 encoding when fetching the webpage
- Using UTF-8 encoding when reading and writing JSON files
- Setting `ensure_ascii=False` in JSON output to preserve special characters

Examples of correctly handled characters: Geißler, Küche, genießen, ermäßigt, Anfänger, Übernachtung

## Notes

- The script respects the website by using appropriate headers
- Encoding is set to UTF-8 to properly handle German characters
- The script is designed to be idempotent - running it multiple times without changes produces consistent results
- Tour IDs are used as unique identifiers for tracking changes

## License

Open source - feel free to modify and use as needed.