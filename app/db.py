from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Параметры подключения (измените на свои)
DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost/road_helper"

# Создание движка и сессии
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Базовый класс для моделей SQLAlchemy
Base = declarative_base()


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True)
    city1 = Column(String)
    city2 = Column(String)
    road = Column(String)
    distance = Column(Integer)
    is_possible = Column(Boolean)

    def __repr__(self):  # Для удобного вывода
        return f"<Route(city1='{self.city1}', city2='{self.city2}', road='{self.road}', distance={self.distance}, is_possible={self.is_possible})>"

# Открываем сессию
with Session() as session:
    # Добавление маршрута
    new_route = Route(city1="Berlin", city2="Hamburg", road="A24", distance=286, is_possible=True)
    session.add(new_route)
    session.commit()

    # Поиск маршрутов
    routes = session.query(Route).filter(Route.city1 == "Berlin", Route.city2 == "Hamburg").all()
    for route in routes:
        print(route)

    # Обновление маршрута
    route_to_update = session.query(Route).filter_by(id=1).first()
    route_to_update.distance = 290
    session.commit()

    # Удаление маршрута
    route_to_delete = session.query(Route).filter_by(id=2).first()
    session.delete(route_to_delete)
    session.commit()
