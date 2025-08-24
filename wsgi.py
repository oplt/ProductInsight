"""
WSGI entry point for ProductInsights application.
"""

import os
from app.main import create_app

# Create application instance
app = create_app(os.environ.get('FLASK_CONFIG'))

if __name__ == "__main__":
    app.run()
