from flask import Flask
import sys
import os

# Add the parent directory to Python path so we can import app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your Flask app
from app import app

# Vercel expects the Flask app to be available
# This is the entry point for Vercel serverless functions
if __name__ == "__main__":
    app.run()
