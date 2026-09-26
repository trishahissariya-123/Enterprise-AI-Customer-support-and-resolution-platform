from backend.app.database.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class Document(Base):
    __tablename__="documents"
    id: Mapped[int]= mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(250),nullable=False)
    chunk_size=Mapped[int]
    file_path=Mapped[str]=mapped_column(String(250), nullable=False)