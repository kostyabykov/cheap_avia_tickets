from datetime import datetime
from sqlalchemy import Boolean, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Flight(Base):
    __tablename__ = "flights"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    departure_from: Mapped[str] = mapped_column(String)
    departure_to: Mapped[str] = mapped_column(String)
    date_from: Mapped[str] = mapped_column(String)
    date_to: Mapped[str | None] = mapped_column(String, nullable=True)
    transfers_cnt: Mapped[int] = mapped_column(Integer)
    one_way: Mapped[bool] = mapped_column(Boolean)
    price: Mapped[int] = mapped_column(Integer)
    days_between: Mapped[int | None] = mapped_column(Integer, nullable=True)

class FlightDay(Base):
    __tablename__ = "flights_days"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    aggregation_date: Mapped[str] = mapped_column(String)
    departure_from: Mapped[str] = mapped_column(String)
    departure_to: Mapped[str] = mapped_column(String)
    date_from: Mapped[str] = mapped_column(String)
    date_to: Mapped[str | None] = mapped_column(String, nullable=True)
    one_way: Mapped[bool] = mapped_column(Boolean)
    days_between: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_price: Mapped[int] = mapped_column(Integer) 