import csv
from datetime import datetime, date
import os
from typing import Optional

from sqlalchemy import insert
from sqlalchemy.orm import Session
from sqlalchemy.engine import Connection

try:
    from .nyp_datastore import (
        OUTCOMES,
        HoldDelete,
        OclcMatch,
        Report,
        get_engine,
        session_scope,
    )
except ImportError:
    from nyp_datastore import (
        OUTCOMES,
        HoldDelete,
        OclcMatch,
        Report,
        get_engine,
        session_scope,
    )


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


def ocn_str2int(ocn_str: str) -> Optional[int]:
    try:
        return int(ocn_str)
    except ValueError:
        return None


def norm_ocn(ocn_str: str) -> Optional[int]:
    if ocn_str.lower().startswith("ocm") or ocn_str.lower().startswith("ocn"):
        ocn = ocn_str2int(ocn_str[3:])
    elif ocn_str.lower().startswith("on"):
        ocn = ocn_str2int(ocn_str[2:])
    elif ocn_str.lower().startswith("(ocolc)"):
        ocn = ocn_str2int(ocn_str[7:])
    else:
        ocn = ocn_str2int(ocn_str)
    return ocn


def norm_title(title_str: str) -> str:
    if "@" in title_str:
        title_lst = title_str.split("@")
        title_str = title_lst[0]
    title = (
        title_str.replace(".", "")
        .replace(",", "")
        .replace(":", "")
        .replace(";", "")
        .replace("/", "")
        .replace("\\", "")
        .replace("'", "")
        .replace('"', "")
    )
    return title.lower().strip()


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


def read_report(fh: str) -> None:
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


def read_deletions(fh: str) -> None:
    """
    Parses, normalizes and stores in db OCLC deletion report
    """
    engine = get_engine()
    with engine.connect() as conn:
        with open(fh, "r") as f:
            print(f"Processing {fh}.")
            reader = csv.reader(f, delimiter="|")
            n = 0
            for row in reader:
                n += 1
                ocn = norm_ocn(row[0])
                title = norm_title(row[1])
                stmt = insert(HoldDelete).values(
                    ocn=ocn,
                    title=title,
                )
                conn.execute(stmt)
            print(f"Saved {n} rows.")


def find_oclc_ids(row: list) -> list:
    """
    Extracts OCNs from Sierra export
    """
    ocns = []
    if row[2]:
        pass


def read_sierra_export(fh: str) -> None:
    """
    Sierra's export config:
        RECORD #(BIBLIO)
        245|a
        BIB UTIL #
        035|a
        910|a
        991|y

        text qualifier: ""
        field delimiter: ^
        repeated field delimiter: @
    """
    with open(fh, "r") as f:
        print(f"Processing {fh}.")
        reader = csv.reader(f, delimter="^")
        next(reader)  # skip header
        n = 0
        for row in reader:
            n += 1
            bibNo = row[0]
            title = norm_title(row[1])
            ocns = find_oclc_ids(row)


if __name__ == "__main__":
    # fdir = "./files/NYPL/orig_reports"
    # reports = find_bib_proc_reports(fdir)
    # print(f"Identified {len(reports)} in {fdir}")
    # for report in reports:
    #     read_report(report)

    read_deletions(
        "./files/NYPL/orig_reports/metacoll.NYP.NYP-1419-20220602-report.20220806-070829.txt"
    )
