#!/bin/bash
#
# Setup script to install the Git pre-commit hook
# This hook will automatically run tests before every commit
#

echo "Setting up Git pre-commit hook..."

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Error: Not in a Git repository root directory"
    echo "Please run this script from the project root (where .git/ exists)"
    exit 1
fi

# Create the pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
#
# Pre-commit hook: Run tests before allowing commit
#

echo ""
echo "🧪 Running tests before commit..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 test_scraper.py

EXIT_CODE=$?

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Tests failed! Commit aborted."
    echo ""
    echo "Please fix the failing tests before committing."
    echo ""
    echo "💡 Tips:"
    echo "  • Run tests manually: python3 test_scraper.py"
    echo "  • Run verbose tests: python3 -m unittest test_scraper -v"
    echo "  • Run specific test: python3 -m unittest test_scraper.TestHTMLParsing.test_parse_tours_basic"
    echo ""
    echo "⚠️  To bypass this hook (NOT recommended):"
    echo "  git commit --no-verify"
    echo ""
    exit 1
fi

echo ""
echo "✅ All tests passed! Proceeding with commit..."
echo ""
EOF

# Make it executable
chmod +x .git/hooks/pre-commit

echo ""
echo "✅ Pre-commit hook installed successfully!"
echo ""
echo "What happens now:"
echo "  • Tests will run automatically before every 'git commit'"
echo "  • If tests fail, the commit will be blocked"
echo "  • This ensures you never commit broken code"
echo ""
echo "To test it:"
echo "  1. Make a small change to a file"
echo "  2. Run: git add <file>"
echo "  3. Run: git commit -m 'test commit'"
echo "  4. You should see tests running automatically"
echo ""
