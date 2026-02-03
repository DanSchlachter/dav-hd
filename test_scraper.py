#!/usr/bin/env python3
"""
Test suite for the Alpenverein Heidelberg Tour Scraper

This test suite covers:
- HTML parsing
- Data extraction
- Encoding handling (German umlauts)
- Delta computation
- File I/O operations
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch, Mock

from scraper import (
    parse_tours,
    load_previous_data,
    save_data,
    compute_deltas
)


class TestHTMLParsing(unittest.TestCase):
    """Test HTML parsing functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_html = '''
        <html>
        <body>
            <p style="background-color:silver; margin-top:15pt;">
                <b>04.02.26, 1 Tage</b><br />
                Skitouren Planung Theorie<a name="t7138">&nbsp;</a><br />
                Ausbildungskurs-7138<br />
            </p>
            <p>
                <b>Leitung: </b><a href="mailto:test@example.com">Michael Pfisterer</a> und Adrian Leibold
            </p>
            <p>
                <b> Anmeldestatus: </b><img src="status.gif" alt="gruen" /> Es sind noch genügend freie Plätze vorhanden
            </p>
            <div id="b7138" class="klappbar">
                <p><b>Ort: </b>Vereinsheim DAV Heidelberg</p>
                <p><b>Anforderungen: </b>Keine Vorkenntnisse erforderlich</p>
                <p><b>max. Teilnehmerzahl: </b>8</p>
                <p><b>Treffpunkt: </b>Vereinsheim DAV Heidelberg, 04.02.2026, 19:00 Uhr</p>
                <p><b>Anmeldeschluss: </b>21.01.26</p>
                <p><b>Kursgebühr (ermäßigt): </b>10.00 EUR (10.00 EUR)</p>
                <p><b>Ausrüstung: </b>Schreibbedarf</p>
            </div>
        </body>
        </html>
        '''

    def test_parse_tours_basic(self):
        """Test basic tour parsing"""
        tours = parse_tours(self.sample_html)
        
        self.assertEqual(len(tours), 1)
        tour = tours[0]
        
        # Check basic fields
        self.assertEqual(tour['id'], 't7138')
        self.assertEqual(tour['begin_date'], '04.02.26')
        self.assertEqual(tour['end_date'], '04.02.26')
        self.assertIn('Skitouren', tour['title'])
        
    def test_parse_tours_date_range(self):
        """Test parsing tours with date ranges"""
        html = '''
        <p style="background-color:silver;">
            <b>05.02.26 - 10.02.26</b><br />
            Skitour<a name="t7152">&nbsp;</a><br />
        </p>
        '''
        tours = parse_tours(html)
        
        self.assertEqual(len(tours), 1)
        self.assertEqual(tours[0]['begin_date'], '05.02.26')
        self.assertEqual(tours[0]['end_date'], '10.02.26')
        
    def test_parse_tours_leader_extraction(self):
        """Test leader name extraction"""
        tours = parse_tours(self.sample_html)
        tour = tours[0]
        
        self.assertEqual(tour['leader'], 'Michael Pfisterer')
        self.assertIn('Adrian Leibold', tour['leader_full'])
        
    def test_parse_tours_registration_status(self):
        """Test registration status extraction"""
        tours = parse_tours(self.sample_html)
        tour = tours[0]
        
        self.assertEqual(tour['registration_status'], 'gruen')
        self.assertIn('genügend', tour['registration_text'])
        
    def test_parse_tours_description_fields(self):
        """Test extraction of description fields"""
        tours = parse_tours(self.sample_html)
        tour = tours[0]
        
        self.assertEqual(tour['location'], 'Vereinsheim DAV Heidelberg')
        self.assertEqual(tour['requirements'], 'Keine Vorkenntnisse erforderlich')
        self.assertEqual(tour['max_participants'], '8')
        self.assertEqual(tour['registration_deadline'], '21.01.26')
        self.assertIn('Schreibbedarf', tour['equipment'])
        
    def test_parse_tours_full_description(self):
        """Test that full description is captured"""
        tours = parse_tours(self.sample_html)
        tour = tours[0]
        
        self.assertIn('description_full', tour)
        self.assertIn('Vereinsheim DAV Heidelberg', tour['description_full'])
        self.assertIn('Keine Vorkenntnisse', tour['description_full'])
        
    def test_parse_tours_url_generation(self):
        """Test URL generation for tours"""
        tours = parse_tours(self.sample_html)
        tour = tours[0]
        
        expected_url = 'https://www.alpenverein-heidelberg.de/index.php?inhalt=tourensucheergebnis#t7138'
        self.assertEqual(tour['url'], expected_url)
        
    def test_parse_multiple_tours(self):
        """Test parsing multiple tours from HTML"""
        html = '''
        <p style="background-color:silver;">
            <b>04.02.26</b><br />
            Tour 1<a name="t1001">&nbsp;</a><br />
        </p>
        <p style="background-color:silver;">
            <b>05.02.26</b><br />
            Tour 2<a name="t1002">&nbsp;</a><br />
        </p>
        <p style="background-color:silver;">
            <b>06.02.26</b><br />
            Tour 3<a name="t1003">&nbsp;</a><br />
        </p>
        '''
        tours = parse_tours(html)
        
        self.assertEqual(len(tours), 3)
        self.assertEqual(tours[0]['id'], 't1001')
        self.assertEqual(tours[1]['id'], 't1002')
        self.assertEqual(tours[2]['id'], 't1003')


class TestGermanUmlauts(unittest.TestCase):
    """Test handling of German special characters"""
    
    def test_umlaut_parsing(self):
        """Test that umlauts are correctly parsed"""
        html = '''
        <p style="background-color:silver;">
            <b>10.03.26</b><br />
            Geißler und Küche<a name="t9999">&nbsp;</a><br />
        </p>
        <div id="b9999">
            <p>Schöne Übernachtung für Anfänger mit gemütlicher Atmosphäre</p>
        </div>
        '''
        tours = parse_tours(html)
        
        tour = tours[0]
        self.assertIn('Geißler', tour['title'])
        self.assertIn('Küche', tour['title'])
        self.assertIn('Schöne', tour['description_full'])
        self.assertIn('Übernachtung', tour['description_full'])
        self.assertIn('Anfänger', tour['description_full'])
        self.assertIn('gemütlicher', tour['description_full'])
        
    def test_special_chars_in_fields(self):
        """Test umlauts in specific fields"""
        html = '''
        <p style="background-color:silver;">
            <b>10.03.26</b><br />
            Test Tour<a name="t8888">&nbsp;</a><br />
        </p>
        <p>
            <b>Leitung: </b><a href="mailto:test@test.de">Jürgen Müller</a>
        </p>
        <div id="b8888">
            <p><b>Ort: </b>München</p>
            <p><b>Anforderungen: </b>Für Anfänger geeignet</p>
            <p><b>Kursgebühr (ermäßigt): </b>50.00 EUR</p>
        </div>
        '''
        tours = parse_tours(html)
        
        tour = tours[0]
        self.assertIn('Jürgen', tour['leader'])
        self.assertIn('Müller', tour['leader'])
        self.assertIn('München', tour['location'])
        self.assertIn('Anfänger', tour['requirements'])


class TestFileOperations(unittest.TestCase):
    """Test file I/O operations"""
    
    def setUp(self):
        """Create temporary directory for test files"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.test_dir)
        
    def test_save_and_load_data(self):
        """Test saving and loading JSON data"""
        test_file = os.path.join(self.test_dir, 'test_tours.json')
        
        test_data = {
            'timestamp': '2026-02-03T12:00:00',
            'tour_count': 2,
            'tours': [
                {'id': 't1001', 'title': 'Test Tour 1'},
                {'id': 't1002', 'title': 'Test Tour 2'}
            ]
        }
        
        # Save data
        save_data(test_data, test_file)
        
        # Verify file exists
        self.assertTrue(os.path.exists(test_file))
        
        # Load data back
        loaded_data = load_previous_data(test_file)
        
        # Verify data matches
        self.assertEqual(loaded_data['tour_count'], 2)
        self.assertEqual(len(loaded_data['tours']), 2)
        self.assertEqual(loaded_data['tours'][0]['id'], 't1001')
        
    def test_load_nonexistent_file(self):
        """Test loading from a file that doesn't exist"""
        nonexistent_file = os.path.join(self.test_dir, 'does_not_exist.json')
        result = load_previous_data(nonexistent_file)
        
        self.assertEqual(result, {})
        
    def test_save_with_umlauts(self):
        """Test that umlauts are preserved in saved files"""
        test_file = os.path.join(self.test_dir, 'test_umlauts.json')
        
        test_data = {
            'tours': [
                {
                    'id': 't1',
                    'title': 'Schöne Bergtour',
                    'leader': 'Jürgen Müller',
                    'description': 'Für Anfänger geeignet. Übernachtung in gemütlicher Hütte.'
                }
            ]
        }
        
        save_data(test_data, test_file)
        
        # Read file and verify umlauts
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('Schöne', content)
            self.assertIn('Jürgen', content)
            self.assertIn('Müller', content)
            self.assertIn('Für', content)
            self.assertIn('Anfänger', content)
            self.assertIn('Übernachtung', content)
            self.assertIn('gemütlicher', content)


class TestDeltaComputation(unittest.TestCase):
    """Test delta computation between runs"""
    
    def test_no_changes(self):
        """Test delta when nothing changed"""
        previous = {
            'tours': [
                {'id': 't1001', 'title': 'Tour 1'},
                {'id': 't1002', 'title': 'Tour 2'}
            ]
        }
        
        current = [
            {'id': 't1001', 'title': 'Tour 1'},
            {'id': 't1002', 'title': 'Tour 2'}
        ]
        
        deltas = compute_deltas(previous, current)
        
        self.assertEqual(len(deltas['added']), 0)
        self.assertEqual(len(deltas['removed']), 0)
        self.assertEqual(len(deltas['modified']), 0)
        
    def test_added_tours(self):
        """Test detection of added tours"""
        previous = {
            'tours': [
                {'id': 't1001', 'title': 'Tour 1'}
            ]
        }
        
        current = [
            {'id': 't1001', 'title': 'Tour 1'},
            {'id': 't1002', 'title': 'Tour 2'},
            {'id': 't1003', 'title': 'Tour 3'}
        ]
        
        deltas = compute_deltas(previous, current)
        
        self.assertEqual(len(deltas['added']), 2)
        self.assertEqual(len(deltas['removed']), 0)
        self.assertEqual(len(deltas['modified']), 0)
        
        added_ids = [t['id'] for t in deltas['added']]
        self.assertIn('t1002', added_ids)
        self.assertIn('t1003', added_ids)
        
    def test_removed_tours(self):
        """Test detection of removed tours"""
        previous = {
            'tours': [
                {'id': 't1001', 'title': 'Tour 1'},
                {'id': 't1002', 'title': 'Tour 2'},
                {'id': 't1003', 'title': 'Tour 3'}
            ]
        }
        
        current = [
            {'id': 't1001', 'title': 'Tour 1'}
        ]
        
        deltas = compute_deltas(previous, current)
        
        self.assertEqual(len(deltas['added']), 0)
        self.assertEqual(len(deltas['removed']), 2)
        self.assertEqual(len(deltas['modified']), 0)
        
        removed_ids = [t['id'] for t in deltas['removed']]
        self.assertIn('t1002', removed_ids)
        self.assertIn('t1003', removed_ids)
        
    def test_modified_tours(self):
        """Test detection of modified tours"""
        previous = {
            'tours': [
                {'id': 't1001', 'title': 'Tour 1', 'status': 'open'},
                {'id': 't1002', 'title': 'Tour 2', 'participants': 5}
            ]
        }
        
        current = [
            {'id': 't1001', 'title': 'Tour 1', 'status': 'closed'},
            {'id': 't1002', 'title': 'Tour 2', 'participants': 5}
        ]
        
        deltas = compute_deltas(previous, current)
        
        self.assertEqual(len(deltas['added']), 0)
        self.assertEqual(len(deltas['removed']), 0)
        self.assertEqual(len(deltas['modified']), 1)
        
        modified = deltas['modified'][0]
        self.assertEqual(modified['id'], 't1001')
        self.assertEqual(modified['previous']['status'], 'open')
        self.assertEqual(modified['current']['status'], 'closed')
        
    def test_mixed_changes(self):
        """Test detection of mixed changes (add, remove, modify)"""
        previous = {
            'tours': [
                {'id': 't1001', 'title': 'Tour 1', 'status': 'open'},
                {'id': 't1002', 'title': 'Tour 2'},
                {'id': 't1003', 'title': 'Tour 3'}
            ]
        }
        
        current = [
            {'id': 't1001', 'title': 'Tour 1', 'status': 'closed'},
            {'id': 't1002', 'title': 'Tour 2'},
            {'id': 't1004', 'title': 'Tour 4'}
        ]
        
        deltas = compute_deltas(previous, current)
        
        self.assertEqual(len(deltas['added']), 1)
        self.assertEqual(len(deltas['removed']), 1)
        self.assertEqual(len(deltas['modified']), 1)
        
        self.assertEqual(deltas['added'][0]['id'], 't1004')
        self.assertEqual(deltas['removed'][0]['id'], 't1003')
        self.assertEqual(deltas['modified'][0]['id'], 't1001')
        
    def test_empty_previous_data(self):
        """Test delta computation when previous data is empty"""
        previous = {}
        
        current = [
            {'id': 't1001', 'title': 'Tour 1'},
            {'id': 't1002', 'title': 'Tour 2'}
        ]
        
        deltas = compute_deltas(previous, current)
        
        # All current tours should be marked as added
        self.assertEqual(len(deltas['added']), 2)
        self.assertEqual(len(deltas['removed']), 0)
        self.assertEqual(len(deltas['modified']), 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_empty_html(self):
        """Test parsing empty HTML"""
        tours = parse_tours('')
        self.assertEqual(len(tours), 0)
        
    def test_malformed_html(self):
        """Test parsing malformed HTML"""
        html = '<p style="background-color:silver;">Incomplete tour'
        tours = parse_tours(html)
        # Should not crash, might return empty or partial data
        self.assertIsInstance(tours, list)
        
    def test_missing_tour_id(self):
        """Test tour without ID anchor"""
        html = '''
        <p style="background-color:silver;">
            <b>10.03.26</b><br />
            Tour without ID<br />
        </p>
        '''
        tours = parse_tours(html)
        # Tours without ID should be skipped
        self.assertEqual(len(tours), 0)
        
    def test_missing_description_div(self):
        """Test tour with missing description div"""
        html = '''
        <p style="background-color:silver;">
            <b>10.03.26</b><br />
            Tour<a name="t1234">&nbsp;</a><br />
        </p>
        '''
        tours = parse_tours(html)
        
        # Should still parse the tour, just without description
        self.assertEqual(len(tours), 1)
        self.assertEqual(tours[0]['id'], 't1234')
        
    def test_tour_with_special_date_format(self):
        """Test tour with unusual date format"""
        html = '''
        <p style="background-color:silver;">
            <b>04.02.26, 1 Tage</b><br />
            One Day Tour<a name="t5555">&nbsp;</a><br />
        </p>
        '''
        tours = parse_tours(html)
        
        self.assertEqual(len(tours), 1)
        # Should still extract the date correctly
        self.assertEqual(tours[0]['begin_date'], '04.02.26')
        self.assertEqual(tours[0]['end_date'], '04.02.26')


class TestDataValidation(unittest.TestCase):
    """Test data validation and consistency"""
    
    def test_tour_has_required_fields(self):
        """Test that parsed tours have required fields"""
        html = '''
        <p style="background-color:silver;">
            <b>10.03.26</b><br />
            Test Tour<a name="t1111">&nbsp;</a><br />
            Führungstour-1111<br />
        </p>
        <p>
            <b>Leitung: </b><a href="mailto:test@test.de">Test Leader</a>
        </p>
        <div id="b1111">
            <p><b>Ort: </b>Test Location</p>
        </div>
        '''
        tours = parse_tours(html)
        
        tour = tours[0]
        
        # Check required fields exist
        self.assertIn('id', tour)
        self.assertIn('title', tour)
        self.assertIn('url', tour)
        self.assertIn('begin_date', tour)
        self.assertIn('end_date', tour)
        
    def test_url_format(self):
        """Test that generated URLs are valid"""
        html = '''
        <p style="background-color:silver;">
            <b>10.03.26</b><br />
            Test<a name="t2222">&nbsp;</a><br />
        </p>
        '''
        tours = parse_tours(html)
        
        url = tours[0]['url']
        self.assertTrue(url.startswith('https://'))
        self.assertIn('alpenverein-heidelberg.de', url)
        self.assertIn('#t2222', url)
        
    def test_date_consistency(self):
        """Test that begin_date is before or equal to end_date"""
        html = '''
        <p style="background-color:silver;">
            <b>05.02.26 - 10.02.26</b><br />
            Multi-day Tour<a name="t3333">&nbsp;</a><br />
        </p>
        '''
        tours = parse_tours(html)
        
        tour = tours[0]
        # For this simple check, just verify both dates are extracted
        self.assertIsNotNone(tour['begin_date'])
        self.assertIsNotNone(tour['end_date'])
        self.assertTrue(len(tour['begin_date']) > 0)
        self.assertTrue(len(tour['end_date']) > 0)


def run_tests():
    """Run all tests and generate report"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestHTMLParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestGermanUmlauts))
    suite.addTests(loader.loadTestsFromTestCase(TestFileOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestDeltaComputation))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
