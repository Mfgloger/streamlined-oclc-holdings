import csv
from datetime import datetime
import os
import pickle
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from bookops_marc import SierraBibReader

from src.bpl_datastore import EnhancedBib
from src.db_access import session_scope, insert_or_ignore
from src.utils import save2csv, start_from_scratch


def start_from_scratch(fh):
    """
    Deletes any exsiting files
    """
    if os.path.isfile(fh):
        os.remove(fh)


def ingest_cross_ref_data():
    with open("./files/enhanced/BPL/ALL-enhance-cross-ref.csv", "r") as f:
        reader = csv.reader(f)
        with session_scope("bpl_db.db") as session:
            for row in reader:
                insert_or_ignore(session, EnhancedBib, bibNo=row[0], oclcNo=row[1])


def select_for_sierra_list_creation(n=int) -> str:
    """
    Select next n number of identifiers for processing.
    Creates a csv file with sierra bib numbers to be used for list creation.

    Args:
        n:              number of identifiers to take
    """
    timestamp = datetime.now()
    out_fh = f"./src/files/enhanced/BPL/batch-{timestamp:%y%m%d}-sierra-nos.csv"  # for archival purposes
    temp_fh = os.path.join(
        os.getenv("USERPROFILE"),
        f"documents/bpl-batch2enrich-{timestamp:%y%m%d}-sierra-nos.csv",
    )
    start_from_scratch(out_fh)
    start_from_scratch(temp_fh)

    with session_scope("./src/bpl_db.db") as session:
        results = (
            session.query(EnhancedBib)
            .filter_by(enhanced=False)
            .order_by(EnhancedBib.bibNo)
            .limit(n)
            .all()
        )
        for row in results:
            save2csv(out_fh, [row.bibNo])
            save2csv(temp_fh, [f"b{row.bibNo}a"])

    return temp_fh


def parse_sierra_bib(src_fh: str = None) -> None:
    if src_fh is None:
        timestamp = datetime.now()
        src_fh = os.path.join(
            os.getenv("USERPROFILE"),
            f"documents/bpl-batch2enrich-{timestamp:%y%m%d}.out",
        )
    with open(src_fh, "rb") as marcfile:
        print(f"Reading {src_fh}.")
        reader = SierraBibReader(marcfile)
        with session_scope("./src/bpl_db.db") as session:
            for bib in reader:
                bibNo = bib.sierra_bib_id_normalized()
                isbns = bib.get_fields("020")
                pickled_isbns = pickle.dumps(isbns)
                kwargs = dict(
                    bibFormat=bib.sierra_bib_format(),
                    opacDisplay=bib["998"]["e"],
                    isbns=pickled_isbns,
                )
                instance = (
                    session.query(EnhancedBib).filter_by(bibNo=bibNo).one_or_none()
                )
                if instance:
                    for key, value in kwargs.items():
                        setattr(instance, key, value)
                else:
                    print(f"Unable to find {bibNo} in the datastore.")


if __name__ == "__main__":
    # ingest_cross_ref_data()
    # select_for_sierra_list_creation(1000)
    parse_sierra_bib()
