"""
Base database model and configuration.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from datetime import datetime
import json

# Create SQLAlchemy instance with custom naming convention
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)


class BaseModel(db.Model):
    """Base model class with common fields and methods."""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        """Save the model to database."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the model from database."""
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        """Update model fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def to_dict(self, exclude_fields=None):
        """Convert model to dictionary."""
        exclude_fields = exclude_fields or []
        
        data = {}
        for column in self.__table__.columns:
            field_name = column.name
            if field_name not in exclude_fields:
                value = getattr(self, field_name)
                
                # Handle datetime serialization
                if isinstance(value, datetime):
                    data[field_name] = value.isoformat()
                # Handle JSON fields
                elif isinstance(value, (dict, list)):
                    data[field_name] = value
                else:
                    data[field_name] = value
        
        return data
    
    @classmethod
    def create(cls, **kwargs):
        """Create and save a new instance."""
        instance = cls(**kwargs)
        return instance.save()
    
    @classmethod
    def get_by_id(cls, id):
        """Get instance by ID."""
        return cls.query.get(id)
    
    @classmethod
    def get_or_404(cls, id):
        """Get instance by ID or raise 404."""
        return cls.query.get_or_404(id)


class TimestampMixin:
    """Mixin for models that need timestamp fields."""
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SoftDeleteMixin:
    """Mixin for models that support soft deletion."""
    
    deleted_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    def soft_delete(self):
        """Soft delete the model."""
        self.deleted_at = datetime.utcnow()
        self.is_deleted = True
        db.session.commit()
    
    def restore(self):
        """Restore soft deleted model."""
        self.deleted_at = None
        self.is_deleted = False
        db.session.commit()
    
    @classmethod
    def active_query(cls):
        """Query for non-deleted records."""
        return cls.query.filter(cls.is_deleted == False)


class JSONFieldMixin:
    """Mixin for models with JSON fields."""
    
    @staticmethod
    def serialize_json(data):
        """Serialize data to JSON string."""
        if data is None:
            return None
        return json.dumps(data, default=str)
    
    @staticmethod
    def deserialize_json(json_str):
        """Deserialize JSON string to data."""
        if json_str is None:
            return None
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return None
