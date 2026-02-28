"""
Pytest configuration file.

This adds the app/ folder to Python's module search path so that:
1. Tests can import from app package: from app.extractor import ...
2. App modules can use plain imports: from pdf_ingestion import ...
"""

import sys
from pathlib import Path

# Add the app directory to Python's module search path
app_dir = Path(__file__).parent / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))