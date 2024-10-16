from sqlalchemy import Column, Integer, String, Float, Text
from .database import Base

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    image_url = Column(String(255))
    rating = Column(Float)
