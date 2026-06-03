from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Province(Base):
    __tablename__ = "provinces"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    municipalities = relationship("Municipality", back_populates="province", cascade="all, delete-orphan")

class Municipality(Base):
    __tablename__ = "municipalities"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    province_id = Column(Integer, ForeignKey("provinces.id"), nullable=False)
    
    province = relationship("Province", back_populates="municipalities")
    barangays = relationship("Barangay", back_populates="municipality", cascade="all, delete-orphan")

class Barangay(Base):
    __tablename__ = "barangays"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    municipality_id = Column(Integer, ForeignKey("municipalities.id"), nullable=False)
    
    municipality = relationship("Municipality", back_populates="barangays")
    mother_titles = relationship("MotherTitle", back_populates="barangay")

class Landowner(Base):
    __tablename__ = "landowners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    contact_info = Column(String, nullable=True)

    # Relationship: One Landowner can have many Mother Titles
    mother_titles = relationship("MotherTitle", back_populates="landowner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Landowner(name='{self.name}')>"


class MotherTitle(Base):
    __tablename__ = "mother_titles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title_number = Column(String, unique=True, nullable=False)
    landowner_id = Column(Integer, ForeignKey("landowners.id"), nullable=False)
    area_hectares = Column(Float, nullable=False)
    
    # New survey and legal fields
    lot_number = Column(String, nullable=True)
    survey_number = Column(String, nullable=True)
    mode_of_acquisition = Column(String, nullable=True) # e.g., Compulsory Acquisition, VOS
    
    # Plotting/Mapping vectors
    raw_text = Column(Text, nullable=True) # Technical descriptions string
    lines = Column(Text, nullable=True)    # JSON/parsed coordinates cache string
    
    # Location Hierarchy link
    barangay_id = Column(Integer, ForeignKey("barangays.id"), nullable=True)

    landowner = relationship("Landowner", back_populates="mother_titles")
    barangay = relationship("Barangay", back_populates="mother_titles")
    individual_titles = relationship("IndividualTitle", back_populates="mother_title", cascade="all, delete-orphan")


class AgrarianReformBeneficiary(Base):
    __tablename__ = "arbs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    contact_number = Column(String, nullable=True)

    # Relationship: An ARB can hold individual titles
    individual_titles = relationship("IndividualTitle", back_populates="arb")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<ARB(name='{self.full_name}')>"


class IndividualTitle(Base):
    __tablename__ = "individual_titles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title_number = Column(String, nullable=False, unique=True)
    allocated_area = Column(Float, nullable=False)
    
    mother_title_id = Column(Integer, ForeignKey("mother_titles.id", ondelete="CASCADE"), nullable=False)
    arb_id = Column(Integer, ForeignKey("arbs.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    mother_title = relationship("MotherTitle", back_populates="individual_titles")
    arb = relationship("AgrarianReformBeneficiary", back_populates="individual_titles")

    def __repr__(self):
        return f"<IndividualTitle(title_number='{self.title_number}')>"