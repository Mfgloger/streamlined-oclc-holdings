from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    PickleType,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class EnhancedBib(Base):
    __tablename__ = "enhanced_bib"

    bibNo = Column(Integer, primary_key=True, autoincrement=False)
    oclcNo = Column(Integer, nullable=False)
    bibFormat = Column(String(1))
    opacDisplay = Column(String(1))
    isbns = Column(PickleType)
    enhanced = Column(Boolean, nullable=False, default=False)
    enhanced_timestamp = Column(DateTime)


def get_engine(db: str = "bpl_db.db"):
    return create_engine(f"sqlite:///{db}")


def init_datastore(db: str = "bpl_db.db"):
    """Initiates datastore"""

    engine = create_engine(f"sqlite:///{db}")
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_datastore()
