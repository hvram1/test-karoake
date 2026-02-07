#!/bin/bash
# Install dependencies for Aeneas forced alignment on macOS

echo "Installing dependencies for Aeneas..."
echo "========================================"

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "ERROR: Homebrew not found. Please install it first:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "1. Installing ffmpeg..."
brew install ffmpeg

echo ""
echo "2. Installing espeak..."
brew install espeak

echo ""
echo "3. Installing Python dependencies..."
pip3 install numpy
pip3 install aeneas

echo ""
echo "4. Verifying installation..."
echo ""

echo "Checking ffmpeg:"
ffmpeg -version 2>&1 | head -1

echo ""
echo "Checking espeak:"
espeak --version 2>&1 | head -1

echo ""
echo "Checking aeneas:"
python3 -c "import aeneas; print('aeneas version:', aeneas.__version__)" 2>&1

echo ""
echo "Running aeneas diagnostics..."
python3 -m aeneas.diagnostics

echo ""
echo "========================================"
echo "Installation complete!"
echo ""
echo "If all checks passed, you can run:"
echo "  python3 poc/scripts/extract_text.py"
echo "  python3 poc/scripts/align_verse.py"
