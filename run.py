#!/usr/bin/env python3
"""
Development server entry point for ProductInsights.
"""

import os
from app.main import create_app

if __name__ == '__main__':
    # Create application with development config
    app = create_app('development')
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
