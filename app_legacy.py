"""
Legacy app.py - Redirects to new main.py structure
This file maintains backward compatibility while the new structure is being adopted.
"""

from main import app
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the new application

# For backward compatibility, export the FastAPI app
__all__ = ['app']

if __name__ == "__main__":
    import uvicorn
    print("⚠️  Running from legacy app.py - Consider using 'python main.py' instead")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
