# Test Suite Documentation

## Overview

The test suite (`test_scraper.py`) provides comprehensive testing for the Alpenverein Heidelberg Tour Scraper. It includes 27 tests across 6 test classes covering all major functionality.

## Running the Tests

### Run all tests:
```bash
python3 test_scraper.py
```

### Run specific test class:
```bash
python3 -m unittest test_scraper.TestHTMLParsing
```

### Run specific test:
```bash
python3 -m unittest test_scraper.TestHTMLParsing.test_parse_tours_basic
```

### Run with verbose output:
```bash
python3 -m unittest test_scraper -v
```

## Test Coverage

### 1. TestHTMLParsing (8 tests)
Tests the core HTML parsing functionality:
- `test_parse_tours_basic` - Basic tour data extraction
- `test_parse_tours_date_range` - Date range parsing (05.02.26 - 10.02.26)
- `test_parse_tours_leader_extraction` - Tour leader name extraction
- `test_parse_tours_registration_status` - Registration status parsing
- `test_parse_tours_description_fields` - Detailed field extraction (location, requirements, etc.)
- `test_parse_tours_full_description` - Full description capture
- `test_parse_tours_url_generation` - URL construction
- `test_parse_multiple_tours` - Multiple tour extraction from single HTML

**What it catches:**
- Broken HTML parsing logic
- Missing or incorrect field extraction
- URL generation errors
- Problems with multiple tour handling

### 2. TestGermanUmlauts (2 tests)
Tests German character encoding:
- `test_umlaut_parsing` - Umlauts in tour names and descriptions (ä, ö, ü, ß)
- `test_special_chars_in_fields` - Special characters in specific fields

**What it catches:**
- Encoding issues (UTF-8 problems)
- Character corruption (Ã¼ instead of ü)
- Loss of special characters

### 3. TestFileOperations (3 tests)
Tests JSON file reading/writing:
- `test_save_and_load_data` - Save and load round-trip
- `test_load_nonexistent_file` - Graceful handling of missing files
- `test_save_with_umlauts` - UTF-8 preservation in saved files

**What it catches:**
- File I/O errors
- Encoding problems in saved files
- Missing file handling issues

### 4. TestDeltaComputation (6 tests)
Tests change detection between runs:
- `test_no_changes` - No differences detected when data is identical
- `test_added_tours` - Detection of new tours
- `test_removed_tours` - Detection of deleted tours
- `test_modified_tours` - Detection of changed tours
- `test_mixed_changes` - All three types of changes at once
- `test_empty_previous_data` - First run scenario

**What it catches:**
- Delta computation errors
- Incorrect change detection
- Missing or false positive changes
- Edge case handling

### 5. TestEdgeCases (5 tests)
Tests error handling and edge cases:
- `test_empty_html` - Empty HTML input
- `test_malformed_html` - Broken/incomplete HTML
- `test_missing_tour_id` - Tours without ID anchors
- `test_missing_description_div` - Tours without detail sections
- `test_tour_with_special_date_format` - Unusual date formats

**What it catches:**
- Crashes on invalid input
- Incorrect handling of missing data
- Edge case failures

### 6. TestDataValidation (3 tests)
Tests data integrity and consistency:
- `test_tour_has_required_fields` - Required fields present
- `test_url_format` - Valid URL generation
- `test_date_consistency` - Date format validation

**What it catches:**
- Missing required fields
- Invalid data formats
- Inconsistent data

## Test Results

Current status: **✅ All 27 tests passing**

```
======================================================================
TEST SUMMARY
======================================================================
Tests run: 27
Successes: 27
Failures: 0
Errors: 0
======================================================================
```

## What the Tests Protect Against

### 1. Website Changes
If the Alpenverein website changes its HTML structure, tests will fail immediately, alerting you to:
- Changed CSS classes or IDs
- Modified HTML structure
- New or removed fields
- Different date formats

### 2. Encoding Issues
Tests ensure German umlauts (ä, ö, ü, ß) are always:
- Correctly parsed from HTML
- Properly stored in JSON
- Preserved across save/load cycles

Example: Prevents regression where "für" becomes "fÃ¼r"

### 3. Data Loss
Tests verify that all fields are extracted:
- Tour title and type
- Dates (begin and end)
- Leader information
- Registration status
- Full descriptions
- Location, requirements, etc.

### 4. Delta Tracking
Tests ensure change detection works correctly:
- New tours are marked as "added"
- Deleted tours are marked as "removed"
- Changed tours are marked as "modified"
- No false positives or negatives

### 5. Error Handling
Tests verify graceful handling of:
- Missing files
- Empty or malformed HTML
- Incomplete tour data
- Missing description sections

## Adding New Tests

When adding new functionality to the scraper, add corresponding tests:

### Example: Testing a new field extraction

```python
def test_new_field_extraction(self):
    """Test extraction of new field"""
    html = '''
    <p style="background-color:silver;">
        <b>10.03.26</b><br />
        Test Tour<a name="t1234">&nbsp;</a><br />
    </p>
    <div id="b1234">
        <p><b>New Field: </b>New Value</p>
    </div>
    '''
    tours = parse_tours(html)
    
    self.assertEqual(tours[0]['new_field'], 'New Value')
```

### Example: Testing error handling

```python
def test_handles_missing_new_field(self):
    """Test graceful handling when new field is missing"""
    html = '''
    <p style="background-color:silver;">
        <b>10.03.26</b><br />
        Test Tour<a name="t1234">&nbsp;</a><br />
    </p>
    '''
    tours = parse_tours(html)
    
    # Should not crash, field should be absent or None
    self.assertNotIn('new_field', tours[0])
```

## Continuous Integration

**⚠️ IMPORTANT: Always run tests before committing changes!**

### Automated Pre-commit Hook (Highly Recommended)

Set up a Git pre-commit hook to automatically run tests before every commit:

```bash
# Create the pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "🧪 Running tests before commit..."
python3 test_scraper.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Tests failed! Commit aborted."
    echo "Please fix the failing tests before committing."
    echo ""
    echo "To see detailed test output, run:"
    echo "  python3 -m unittest test_scraper -v"
    exit 1
fi

echo "✅ All tests passed! Proceeding with commit..."
EOF

# Make it executable
chmod +x .git/hooks/pre-commit
```

**What this does:**
- Runs all 27 tests automatically before each `git commit`
- Blocks the commit if any test fails
- Forces you to fix issues before committing broken code
- Ensures code quality and prevents regressions

**To bypass in emergencies only:**
```bash
git commit --no-verify  # Skip the pre-commit hook (NOT recommended!)
```

### Scheduled testing
Run tests daily to catch website changes:
```bash
# Add to crontab
0 7 * * * cd /path/to/dav && python3 test_scraper.py && mail -s "Scraper Tests Passed" you@email.com
```

### GitHub Actions
The `.github/workflows/test.yml` file automatically runs tests on:
- Every push to main/master/develop
- Every pull request
- Daily at 6 AM UTC (to catch website changes)

## Troubleshooting

### Test fails after website update
1. Check if the website HTML structure changed
2. Update the scraper parsing logic
3. Update tests if expectations changed
4. Re-run tests to verify

### Encoding test fails
1. Check system locale: `locale`
2. Verify Python encoding: `python3 -c "import sys; print(sys.getdefaultencoding())"`
3. Ensure UTF-8 is properly configured

### Tests pass but scraper fails on real data
1. Add a new test case with the problematic HTML
2. Debug with: `python3 -m pdb test_scraper.py`
3. Fix the issue and verify test passes

## Test Maintenance

**Run tests:**
- ✅ Before committing changes
- ✅ After website updates
- ✅ Before deploying to production
- ✅ As part of CI/CD pipeline

**Update tests when:**
- Adding new features
- Fixing bugs
- Website structure changes
- Requirements change

## Performance

Current test suite performance:
- **Total tests:** 27
- **Execution time:** ~0.02 seconds
- **Memory usage:** Minimal (uses temporary files)

Tests are fast enough to run on every commit.
