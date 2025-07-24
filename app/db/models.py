from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    priority = Column(Integer, nullable=False)
    buckets = relationship("Bucket", back_populates="order")


class Position(Base):
    __tablename__ = "position"
    id = Column(Integer, primary_key=True, index=True)
    position_x = Column(Integer, nullable=False)
    position_y = Column(Integer, nullable=False)
    position_z = Column(Integer, nullable=False)
    bucket = relationship(
        "Bucket",
        back_populates="position",
        uselist=False
    )


class Bucket(Base):
    __tablename__ = "bucket"
    id = Column(Integer, primary_key=True, index=True)
    material_type = Column(String, nullable=False)
    material_qty = Column(Integer, nullable=False)

    position_id = Column(
        Integer,
        ForeignKey("position.id"),
        unique=True
    )
    position = relationship(
        "Position",
        back_populates="bucket",
        uselist=False
    )
    order_id = Column(Integer,
                      ForeignKey(
                          "orders.id",
                          ondelete="SET NULL"
                      ),
                      nullable=True)
    order = relationship(
        "Order",
        back_populates="buckets",
        passive_deletes=True
    )
