# Quick Reference

## Common Commands

### Run the scraper
```bash
python3 scraper.py
```

### Run tests
```bash
python3 test_scraper.py
```

### Run specific test class
```bash
python3 -m unittest test_scraper.TestHTMLParsing -v
```

### Check output
```bash
# View tour count
python3 -c "import json; print(json.load(open('tours.json'))['tour_count'])"

# View delta summary
python3 -c "import json; print(json.load(open('tours_delta.json'))['summary'])"
```

### View scraped data
```bash
# Pretty print first tour
python3 -c "import json; from pprint import pprint; pprint(json.load(open('tours.json'))['tours'][0])"
```

## File Structure

```
dav/
├── scraper.py           # Main scraper script (9.2 KB)
├── test_scraper.py      # Test suite (19 KB, 27 tests)
├── requirements.txt     # Python dependencies
├── README.md            # Main documentation
├── TESTING.md          # Test documentation
├── tours.json          # Current tour data (198 KB)
├── tours_delta.json    # Changes since last run
└── .github/
    └── workflows/
        └── test.yml    # CI/CD configuration
```

## Project Statistics

- **Lines of code (scraper):** ~260
- **Lines of code (tests):** ~550
- **Test coverage:** 27 tests
- **Test execution time:** ~0.02 seconds
- **Supported Python versions:** 3.9+

## What Each File Does

| File | Purpose |
|------|---------|
| `scraper.py` | Main script that fetches and parses tour data |
| `test_scraper.py` | Comprehensive test suite (27 tests) |
| `tours.json` | Complete tour data from latest run |
| `tours_delta.json` | Only the changes since previous run |
| `requirements.txt` | Python package dependencies |
| `README.md` | Main documentation and usage guide |
| `TESTING.md` | Detailed test documentation |
| `.github/workflows/test.yml` | GitHub Actions CI/CD pipeline |

## Test Coverage Summary

✅ **27/27 tests passing**

- **HTML Parsing:** 8 tests
- **German Umlauts:** 2 tests  
- **File Operations:** 3 tests
- **Delta Computation:** 6 tests
- **Edge Cases:** 5 tests
- **Data Validation:** 3 tests

## Key Features

✅ Scrapes all tour data from Alpenverein website  
✅ Handles German umlauts (ä, ö, ü, ß) correctly  
✅ Extracts 15+ fields per tour  
✅ Tracks changes (added/removed/modified)  
✅ Comprehensive test suite  
✅ CI/CD with GitHub Actions  
✅ Full documentation  

## Data Fields Extracted

Each tour includes:
- `begin_date`, `end_date` - Tour dates (DD.MM.YY)
- `title` - Tour name (e.g., "Skitouren Planung Theorie")
- `tour_type` - Tour category (e.g., "Führungstour-7152")
- `id`, `url` - Unique ID and link
- `leader`, `leader_full` - Tour leaders
- `registration_status` - Availability (gruen/gelb/orange/rot)
- `description_full` - Complete description
- `location`, `requirements` - Tour details
- `max_participants` - Capacity
- `meeting_point` - Where to meet
- `registration_deadline` - When to register by
- `course_fee`, `equipment` - Costs and gear needed

## Automation Examples

### Cron job (daily at 6 AM)
```bash
0 6 * * * cd /path/to/dav && python3 scraper.py
```

### Git pre-commit hook
```bash
#!/bin/bash
python3 test_scraper.py || exit 1
```

### Monitor for changes
```bash
python3 scraper.py && \
python3 -c "import json; d=json.load(open('tours_delta.json')); \
total=sum(d['summary'].values()); \
print(f'{total} changes detected') if total > 0 else exit(0)"
```

## Troubleshooting

### Tests fail
```bash
# Run with verbose output
python3 -m unittest test_scraper -v
```

### Encoding issues
```bash
# Check Python encoding
python3 -c "import sys; print(sys.getdefaultencoding())"
# Should output: utf-8
```

### No tours found
```bash
# Check if website is accessible
curl -I https://www.alpenverein-heidelberg.de/
```

## Links

- **Website:** https://www.alpenverein-heidelberg.de/
- **Tour Page:** https://www.alpenverein-heidelberg.de/index.php?inhalt=tourensucheergebnis
- **Documentation:** See README.md and TESTING.md
