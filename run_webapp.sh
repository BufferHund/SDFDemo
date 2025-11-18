#!/bin/bash
# Launcher script for Supermarket Brochure AI Web Interface

echo "🛒 Supermarket Brochure AI - Web Interface Launcher"
echo "=================================================="
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit is not installed."
    echo "Please install it with: pip install streamlit"
    exit 1
fi

# Check which interface to run
if [ "$1" == "enhanced" ] || [ "$1" == "" ]; then
    echo "🚀 Starting Enhanced Interface..."
    echo ""
    echo "Features:"
    echo "  • Single file processing with 3 methods (OCR/VLM/Hybrid)"
    echo "  • Batch processing with parallel execution"
    echo "  • Method comparison tool"
    echo "  • Visual deal highlighting"
    echo "  • Interactive configuration"
    echo ""
    echo "Opening at http://localhost:8501"
    echo "Press Ctrl+C to stop"
    echo ""
    streamlit run src/webapp/app_enhanced.py
elif [ "$1" == "basic" ]; then
    echo "🚀 Starting Basic Interface..."
    echo ""
    echo "Features:"
    echo "  • Simple OCR extraction"
    echo "  • Bounding box visualization"
    echo "  • Basic data export"
    echo ""
    echo "Opening at http://localhost:8501"
    echo "Press Ctrl+C to stop"
    echo ""
    streamlit run src/webapp/app.py
else
    echo "Usage: $0 [enhanced|basic]"
    echo ""
    echo "Options:"
    echo "  enhanced (default) - Full-featured interface with pipeline"
    echo "  basic              - Simple OCR-only interface"
    echo ""
    echo "Examples:"
    echo "  $0              # Run enhanced interface"
    echo "  $0 enhanced     # Run enhanced interface"
    echo "  $0 basic        # Run basic interface"
    exit 1
fi
