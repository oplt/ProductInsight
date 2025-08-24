#!/usr/bin/env python3
"""
Database initialization script for ProductInsights.
Creates all database tables and optional sample data.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import create_app
from app.infrastructure.database.models import db, User, Analysis


def init_database(create_sample_data=False):
    """Initialize the database."""
    print("🚀 Initializing ProductInsights database...")
    
    # Create application
    app = create_app('development')
    
    with app.app_context():
        print("📦 Creating database tables...")
        
        # Drop all tables first (for clean start)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("✅ Database tables created successfully!")
        
        if create_sample_data:
            print("📝 Creating sample data...")
            create_sample_user()
            print("✅ Sample data created!")
        
        print("🎉 Database initialization complete!")


def create_sample_user():
    """Create a sample user for testing."""
    # Check if user already exists
    existing_user = User.query.filter_by(email='admin@productinsights.com').first()
    if existing_user:
        print("⚠️ Sample user already exists")
        return
    
    # Create sample user
    user = User(
        username='admin',
        email='admin@productinsights.com',
        first_name='Admin',
        last_name='User',
        role='admin',
        status='active'
    )
    user.set_password('admin123')
    user.verify_email()
    
    db.session.add(user)
    db.session.commit()
    
    print(f"✅ Sample user created: {user.email} (password: admin123)")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize ProductInsights database')
    parser.add_argument('--sample-data', action='store_true', 
                       help='Create sample data for testing')
    
    args = parser.parse_args()
    
    try:
        init_database(create_sample_data=args.sample_data)
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
