from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


OUTCOMES = {
    "match": 1,
    "create": 2,
    "unresolved": 3,
    "data_error": 4,
    "processing_error": 5,
}


class SierraBib(Base):
    """
    Sierra bib data
    """

    __tablename__ = "sierra_bib"
    bibNo = Column(Integer, primary_key=True, autoincrement=False)
    title = Column(String, nullable=False)
    isResearch = Column(Boolean)
    bibCode3 = Column(String(1))
    bibFormat = Column(String(1))

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
    changedOcn = Column(Boolean)

    def __repr__(self):
        return (
            f"<OclcMatch(mid='mid', bibNo='{self.bibNo}', reportId='{self.reportId}, "
            f"isOcnProcess='{self.isOcnProcess}', statusId='{self.statusId}', "
            f"procDate='{self.procDate}', ocn='{self.ocn}', changedOcn='{self.changedOcn}')>"
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

"""
bibNo, mid
10003403 (5048117)
22221482 (5944478)
10923208 (4849520)
"""
