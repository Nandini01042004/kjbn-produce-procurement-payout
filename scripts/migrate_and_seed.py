"""
Migrate and Seed Script
Sets up fresh database schema and loads realistic sample data.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from seed import seed_database

if __name__ == "__main__":
    print("Running migrate and seed...")
    seed_database()
    print("Done!")
