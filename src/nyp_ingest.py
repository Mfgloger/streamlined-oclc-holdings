import csv
from datetime import datetime, date
import os
from typing import Optional

from sqlalchemy import insert
from sqlalchemy.orm import Session
from sqlalchemy.engine import Connection

try:
    from .nyp_datastore import OUTCOMES, OclcMatch, Report, get_engine, session_scope
except ImportError:
    from nyp_datastore import OUTCOMES, OclcMatch, Report, get_engine, session_scope


def find_bib_proc_reports(fdir: str) -> list[str]:
    """
    Finds BibProcessingReports in given directory

    Returns:
            list of file handles
    """
    files = []
    for file in os.listdir(fdir):
        if "BibProcessingReport" in os.path.basename(file):
            files.append(os.path.join(fdir, file))

    return files


def norm_ocn(ocn_str: str) -> Optional[int]:
    try:
        return int(ocn_str)
    except ValueError:
        return None


def get_status_id(status: str) -> int:
    status = status.strip().replace(" ", "_")
    return OUTCOMES[status]


def add_report(conn: Connection, handle: str) -> int:
    stmt = insert(Report).values(handle=handle)
    result = conn.execute(stmt)
    return result.inserted_primary_key[0]


def is_ocn_process(handle: str) -> bool:
    if ".OCNs." in handle:
        return True
    else:
        return False


def get_file_date(handle: str) -> date:
    date_str = os.path.basename(handle)[56:64]
    date = datetime.strptime(date_str, "%Y%m%d").date()
    return date


def read_report(fh: str) -> list[OclcMatch]:
    engine = get_engine()
    with engine.connect() as conn:
        with open(fh, "r") as f:
            print(f"Processing {fh}.")
            reportId = add_report(conn, fh)
            isOcnProcess = is_ocn_process(fh)
            procDate = get_file_date(fh)
            reader = csv.reader(f, delimiter="|")
            n = 0
            for row in reader:
                n += 1
                bibNo = row[1][2:]
                ocn = norm_ocn(row[-2])
                statusId = get_status_id(row[-1])

                stmt = insert(OclcMatch).values(
                    bibNo=bibNo,
                    reportId=reportId,
                    isOcnProcess=isOcnProcess,
                    statusId=statusId,
                    procDate=procDate,
                    ocn=ocn,
                )
                conn.execute(stmt)

            print(f"Saved {n} rows.")


if __name__ == "__main__":
    fdir = "./files/NYPL/orig_reports"
    reports = find_bib_proc_reports(fdir)
    print(f"Identified {len(reports)} in {fdir}")
    for report in reports:
        read_report(report)
