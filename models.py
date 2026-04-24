from sqlalchemy import Column, Integer, String
from database import Base

class Router(Base):
    __tablename__ = "routers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    ip = Column(String)

    username = Column(String)
    password = Column(String)

    mac = Column(String, unique=True, index=True)  # مهم
