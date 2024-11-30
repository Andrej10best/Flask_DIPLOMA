"""
Данный файл представляет собой код для работы с базой данных, который использует SQLAlchemy для определения
моделей данных и Pydantic для валидации входящих данных.
"""

import logging.config
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from log_set.log_setting import LOGGING

# Настройка логирования
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('log')

# URL для подключения к базе данных
DATABASE_URL = "sqlite:///../data.db"

# Создание движка базы данных с использованием SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Создание локальной сессии для работы с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание метаданных и базового класса для декларативного определения моделей
metadata = MetaData()
Base = declarative_base()


class TourTable(Base):
    """
        Модель таблицы 'tours' для хранения информации о турах.

        Атрибуты:
            id (int): Уникальный идентификатор тура.
            title (str): Название тура.
            description (str): Описание тура.
            place (str): Место проведения тура.
            start_date_tour (str): Дата начала тура.
            duration (int): Длительность тура в днях.
            max_people (int): Максимальное количество участников.
            available_places (int): Количество доступных мест.
            occupied_places (int): Количество занятых мест.
            price_per_person (int): Цена за человека.
            image_path (str): Путь к изображению тура.

        Связи:
            users (relationship): Связь с моделью UserTable.
        """
    __tablename__ = 'tours'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    place = Column(String, nullable=False)
    start_date_tour = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    max_people = Column(Integer, nullable=False)
    available_places = Column(Integer, nullable=False)
    occupied_places = Column(Integer, nullable=False)
    price_per_person = Column(Integer, nullable=False)
    image_path = Column(String, nullable=False)

    users = relationship("UserTable", back_populates="tour")


class UserTable(Base):
    """
        Модель таблицы 'users' для хранения информации о пользователях.

        Атрибуты:
            id (int): Уникальный идентификатор пользователя.
            name (str): Имя пользователя.
            email (str): Email пользователя.
            phone (int): Телефон пользователя.
            number_of_people (int): Количество людей в группе пользователя.
            tour_id (int): Идентификатор тура, на который записан пользователь.

        Связи:
            tour (relationship): Связь с моделью TourTable.
        """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(Integer)
    number_of_people = Column(Integer)
    tour_id = Column(Integer, ForeignKey('tours.id'))

    tour = relationship("TourTable", back_populates="users")


class SchemaTour(BaseModel):
    """
       Схема для валидации данных тура с использованием Pydantic.

       Атрибуты:
           title (str): Название тура.
           description (str): Описание тура.
           place (str): Место проведения тура.
           start_date_tour (str): Дата начала тура.
           duration (int): Длительность тура в днях.
           max_people (int): Максимальное количество участников.
           available_places (int): Количество доступных мест.
           occupied_places (int): Количество занятых мест.
           price_per_person (int): Цена за человека.
           image_path (str): Путь к изображению тура.
       """
    title: str
    description: str
    place: str
    start_date_tour: str
    duration: int
    max_people: int
    available_places: int
    occupied_places: int
    price_per_person: int
    image_path: str


class Tour(SchemaTour):
    """
        Расширенная схема для тура, включающая идентификатор.

        Атрибуты:
            id (int): Уникальный идентификатор тура.
        """
    id: int


class SchemaUser(BaseModel):
    """
        Схема для валидации данных пользователя с использованием Pydantic.

        Атрибуты:
            name (str): Имя пользователя
            email (str): Email пользователя
            phone (int): Телефон пользователя
            number_of_people (int): Количество людей в группе пользователя
            tour_id (int): Идентификатор тура, на который записан пользователь.
        """
    name: str
    email: str
    phone: int
    number_of_people: int
    tour_id: int


class User(SchemaUser):
    """
        Расширенная схема для пользователя, включающая идентификатор.

        Атрибуты:
            id (int): Уникальный идентификатор пользователя.
        """
    id: int


def create_tables():
    """
        Создает таблицы в базе данных на основе определенных моделей.

        Логирует успешное создание таблиц или ошибку, если создание не удалось.
        """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info('Таблицы успешно созданы в базе данных.')
    except Exception as e:
        logger.error('Ошибка при создании таблиц: %s', str(e))
