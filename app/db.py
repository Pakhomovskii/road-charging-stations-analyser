from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from templates.constants import DATABASE_URL

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a base class for declarative models
Base = declarative_base()


# Here I define my base route model using SQLAlchemy declarative base
class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    city1 = Column(String)
    city2 = Column(String)
    road = Column(String)
    distance = Column(Float)
    is_possible = Column(Boolean)
    problem_point1 = Column(String, nullable=True)
    problem_point2 = Column(String, nullable=True)


# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
