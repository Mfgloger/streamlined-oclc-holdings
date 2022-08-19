from contextlib import contextmanager

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, sessionmaker


Base = declarative_base()


OUTCOMES = {
    "match": 1,
    "create": 2,
    "unresolved": 3,
    "data_error": 4,
    "processing_error": 5,
}


class DataAccessLayer:
    def __init__(self, db: str):
        self.conn = f"sqlite:///{db}"
        self.engine = None

    def connect(self):
        self.engine = create_engine(self.conn)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)


@contextmanager
def session_scope(db: str = "nyp_db.db"):
    """
    Provides a transactional scope around series of operations.
    """
    dal = DataAccessLayer(db)
    dal.connect()
    session = dal.Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class SierraBib(Base):
    """
    Sierra bib data
    """

    __tablename__ = "sierra_bib"
    bibNo = Column(Integer, primary_key=True, autoincrement=False)
    title = Column(String, nullable=False)
    isResearch = Column(Boolean)
    bibCode3 = Column(String(1), nullable=False)
    bibFormat = Column(String(1), nullable=False)

    sierraOcns = relationship("SierraBibOcns", cascade="all, delete-orphan")
    outcomes = relationship("OclcMatch", cascade="all, delete-orphan")


class SierraBibOcns(Base):
    """
    OCN numbers found in Sierra bib
    """

    __tablename__ = "sierra_bib_ocns"

    soid = Column(Integer, primary_key=True)
    ocn = Column(Integer, nullable=True)
    bibNo = Column(Integer, ForeignKey("sierra_bib.bibNo"), nullable=False)


class OclcMatch(Base):
    """
    Result of OCLC matching process
    """

    __tablename__ = "oclc_match"

    mid = Column(Integer, primary_key=True)
    bibNo = Column(Integer, ForeignKey("sierra_bib.bibNo"), nullable=False)
    reportId = Column(Integer, ForeignKey("report.rid"), nullable=False)
    isOcnProcess = Column(Boolean, nullable=False)
    statusId = Column(Integer, ForeignKey("status.sid"), nullable=False)
    procDate = Column(Date, nullable=False)
    ocn = Column(Integer)

    def __repr__(self):
        return (
            f"<OclcMatch(mid='mid', bibNo='{self.bibNo}', reportId='{self.reportId}, "
            f"isOcnProcess='{self.isOcnProcess}', statusId='{self.statusId}', "
            f"procDate='{self.procDate}', ocn='{self.ocn}')>"
        )


class Report(Base):
    """
    Report file handles
    """

    __tablename__ = "report"

    rid = Column(Integer, primary_key=True)
    handle = Column(String, nullable=False)

    outcomes = relationship("OclcMatch", cascade="all, delete-orphan")


class Status(Base):
    """
    Categories of OCLC matching outcomes
    """

    __tablename__ = "status"

    sid = Column(Integer, primary_key=True)
    cat = Column(String, unique=True)


class HoldDelete(Base):
    """
    Holdings deletion data
    """

    __tablename__ = "hold_delete"

    ocn = Column(Integer, primary_key=True, autoincrement=False)
    title = Column(String, nullable=False)
    keep = Column(Boolean, nullable=False, default=False)


def get_engine(db: str = "nyp_db.db"):
    return create_engine(f"sqlite:///{db}")


def init_datastore(db: str = "nyp_db.db"):
    """Initiates datastore"""

    engine = create_engine(f"sqlite:///{db}")
    Base.metadata.create_all(engine)
    with session_scope(db) as session:
        for k, v in OUTCOMES.items():
            instance = Status(sid=v, cat=k)
            session.add(instance)
        session.commit()


if __name__ == "__main__":
    init_datastore()
