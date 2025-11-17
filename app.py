"""
GeneLingua Application - Redirects to new modular structure
For the new organized structure, use: python main.py
"""

import sys
import os
import warnings

# Deprecation warning
warnings.warn(
    "app.py is deprecated. Please use 'python main.py' for the new modular structure.",
    DeprecationWarning,
    stacklevel=2
)

# Redirect to new structure
if __name__ == "__main__":
    print("🔄 Redirecting to new application structure...")
    print("💡 For better performance, use: python main.py")

    # Import and run the new app
    from main import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
else:
    # For imports, provide the app
    from main import app
