from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    priority = Column(Integer, nullable=False)
    order_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    bucket_actions = relationship(
        "BucketAction",
        back_populates="order",
        cascade="all, delete-orphan"
    )


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    position_x = Column(Integer, nullable=False)
    position_y = Column(Integer, nullable=False)
    position_z = Column(Integer, nullable=False)

    bucket = relationship(
        "Bucket",
        back_populates="position",
        uselist=False
    )

    source_actions = relationship(
        "BucketAction",
        back_populates="source_position",
        foreign_keys='BucketAction.source_position_id'
    )
    target_actions = relationship(
        "BucketAction",
        back_populates="target_position",
        foreign_keys='BucketAction.target_position_id'
    )


class Bucket(Base):
    __tablename__ = "buckets"

    id = Column(Integer, primary_key=True, index=True)

    position_id = Column(
        Integer,
        ForeignKey("positions.id"),
        unique=True,
        nullable=True
    )
    position = relationship(
        "Position",
        back_populates="bucket"
    )

    bucket_actions = relationship(
        "BucketAction",
        back_populates="bucket"
    )


class BucketAction(Base):
    __tablename__ = "bucket_actions"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey(
        "orders.id",
        ondelete="CASCADE"
    ), nullable=False)
    bucket_id = Column(
        Integer,
        ForeignKey("buckets.id"),
        nullable=False
    )

    source_position_id = Column(
        Integer,
        ForeignKey("positions.id"),
        nullable=True)

    target_position_id = Column(
        Integer,
        ForeignKey("positions.id"),
        nullable=True
    )

    order = relationship("Order", back_populates="bucket_actions")
    bucket = relationship("Bucket", back_populates="bucket_actions")

    source_position = relationship(
        "Position",
        back_populates="source_actions",
        foreign_keys=[source_position_id]
    )
    target_position = relationship(
        "Position",
        back_populates="target_actions",
        foreign_keys=[target_position_id]
    )




class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, index=True)
    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="NEW", server_default="NEW")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)