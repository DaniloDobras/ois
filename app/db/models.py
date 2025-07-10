from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    bucket_id = Column(Integer, nullable=False)
    material_id = Column(Integer, nullable=False)
    qty = Column(Integer, nullable=False)
