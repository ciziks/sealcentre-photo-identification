from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from .database import Base


class Seal(Base):
    __tablename__ = "Seals"

    ID = Column(String, primary_key=True, index=True)
    age = Column(String, nullable=False)
    comments = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    isPregnant = Column(String, nullable=True)
    encounters = relationship("Encounter", back_populates="seal", cascade="all, delete-orphan")


class Sighting(Base):
    __tablename__ = "Sightings"

    SightingID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Date = Column(DateTime)
    Location = Column(String)
    encounters = relationship("Encounter", back_populates="sighting", cascade="all, delete-orphan")


class Encounter(Base):
    __tablename__ = "Encounter"

    WildBookID = Column(Integer, primary_key=True)
    SightingID = Column(Integer, ForeignKey("Sightings.SightingID"))
    SealID = Column(String, ForeignKey("Seals.ID"))
    sighting = relationship("Sighting", back_populates="encounters")
    seal = relationship("Seal", back_populates="encounters")