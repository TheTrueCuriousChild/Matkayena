from app.db.base import Base
from app.db.database import engine

from app.models.identity import *
from app.models.crm import *
from app.models.events import *
from app.models.intelligence import *
from app.models.actions import *
from app.models.performance import *
from app.models.audit import *


Base.metadata.create_all(bind=engine)

print("Tables Created Successfully")