from sqlalchemy import Column, Integer, String, Text, Float
from geoalchemy2 import Geometry  # DÜZELTME: geom sütunu eklendi
from database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, index=True)
    description = Column(Text, nullable=True)
    floor = Column(Integer)
    # DÜZELTME: Veritabanındaki geom sütunu artık modelde de tanımlı
    geom = Column(Geometry(geometry_type="POINT", srid=3857), nullable=True)


class Node(Base):
    __tablename__ = "edges_vertices_pgr"

    id = Column(Integer, primary_key=True, index=True)


class Edge(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(Integer)
    target = Column(Integer)
    cost = Column(Float)
    reverse_cost = Column(Float)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    # NOT: Şifreler artık bcrypt ile hashlenmiş olarak saklanmalı
    password = Column(String, nullable=False)
    role = Column(String, default="user")  # "admin" veya "user"
