from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models only at the bottom to avoid circular import
import app.models.user
import app.models.restaurant
import app.models.menu
import app.models.order
import app.models.analytics
import app.models.notification
import app.models.shift
import app.models.chef
from app.models.chef_activity import ChefActivityLog

