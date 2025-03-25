from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..templates.constants import DATABASE_URL

engine = create_engine(DATABASE_URL)

Base = declarative_base()


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


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
