"""
Scripts to obtain Worldcat records and enhance their match in Sierra.
"""
import csv
from datetime import datetime
import json
import os
import pickle
from typing import Optional, Union
from io import BytesIO


# from bookops_marc import Bib
from bookops_marc import Bib, SierraBibReader
from bookops_marc.bib import pymarc_record_to_local_bib
from bookops_worldcat import WorldcatAccessToken, MetadataSession
from bookops_worldcat.errors import WorldcatSessionError, WorldcatRequestError
import pandas as pd
from pymarc import Field, Record, parse_xml_to_array
from requests import Response
from sqlalchemy.orm import Session


from src.__init__ import __version__
from src.bpl_datastore import EnhancedBib
from src.db_access import session_scope
from src.utils import save2csv, save2marc, start_from_scratch


def select_for_enhancing(session: Session) -> list[EnhancedBib]:
    instances = (
        session.query(EnhancedBib)
        .filter(EnhancedBib.enhanced == False, EnhancedBib.bibFormat != None)
        .order_by(EnhancedBib.bibNo)
    ).all()
    return instances


def get_worldcat_bib(
    session: MetadataSession, oclcNo: str, bibNo: int, i: int, n: int
) -> Optional[Response]:
    """
    Queries Worldcat for given OCLC record #

    Args:
        session:                `requests.Session` instance
        oclcNo:                 OCLC #
        bibNo:                  Sierra bib number
        i:                      request number in the process
        n:                      total number of requestsin the process

    """
    response = session.get_full_bib(oclcNo)
    if response.status_code == 200:
        print(f"{i+1}/{n} b{bibNo}a: {response.url} = OK")
        return response
    else:
        print(f"{i+1}/{n} b{bibNo}a: {response.request.url} = {response.status_code}")
        return None


def get_token(creds_fh: str) -> WorldcatAccessToken:
    """
    Obtains Worldcat access token

    Args:
        creds_fh:           path to credentials

    Returns:
        `WorldcatAccessToken` instance
    """
    with open(creds_fh, "r") as f:
        creds = json.load(f)

    token = WorldcatAccessToken(
        key=creds["key"],
        secret=creds["secret"],
        scopes="WorldCatMetadataAPI",
        principal_id=creds["principal_id"],
        principal_idns=creds["principal_idns"],
        agent=f"{creds['agent']}/SH-Enhance-Project",
    )
    return token


def manipulate_bib(
    bib: Bib,
    bibNo: str,
    library: str,
    sierra_format: str,
    sierra_opac: str,
    pickled_isbns: bytes,
) -> None:
    """
    Supports only BPL at the moment!!
    """

    # replace ISBN tags
    bib.remove_fields("020")
    isbn_fields = pickle.loads(pickled_isbns)
    for field in isbn_fields:
        bib.add_ordered_field(field)

    # remove other unwanted fields
    bib.remove_fields("019", "029", "263", "938")

    # add command tag
    command_str = f"*b2={sierra_format}"
    if sierra_opac != "-":
        command_str += f";b3={sierra_opac}"
    bib.add_field(
        Field(tag="949", indicators=[" ", " "], subfields=["a", f"{command_str};"])
    )

    # cleanup 6xx aile
    bib.remove_unsupported_subjects()


def launch_bpl_enhancement(out_fh: str = None) -> None:
    """

    Args:
        out_fh:             output MARC file
                            defaults to `documents/bpl-enriched-[yymmdd].mrc`
    """
    timestamp = datetime.now()
    if out_fh is None:
        out_fh = os.path.join(
            os.getenv("USERPROFILE"),
            f"documents/bpl-enriched-{timestamp:%y%m%d}.mrc",
        )
    print(f"Output file: {out_fh}")

    creds_fh = os.path.join(os.getenv("USERPROFILE"), f".oclc/bpl_overload.json")
    token = get_token(creds_fh)
    print("Worldcat Metadata API token obtained...")

    with MetadataSession(authorization=token) as session:
        print("Worldcat session opened...")

        # get source data for queries
        with session_scope(db=f"./src/bpl_db.db") as db_session:
            rows = select_for_enhancing(db_session)
            n = len(rows)
            if n == 0:
                print("No source Sierra MARC file found. Please export records first.")
            for i, row in enumerate(rows):
                try:
                    response = get_worldcat_bib(session, row.oclcNo, row.bibNo, i, n)
                except WorldcatRequestError:
                    raise WorldcatRequestError(
                        "API request error. Resume with 'python run.py enrich-resume' command."
                    )

                if response is not None:
                    data = BytesIO(response.content)
                    worldcat_bib = parse_xml_to_array(data)[0]
                    bib = pymarc_record_to_local_bib(worldcat_bib, "BPL")
                    manipulate_bib(
                        bib,
                        row.bibNo,
                        "BPL",
                        row.bibFormat,
                        row.opacDisplay,
                        row.isbns,
                    )
                    save2marc(out_fh, bib)
                    row.enhanced = True
                    row.enhanced_timestamp = datetime.now()
                    db_session.commit()
                else:
                    fail_fh = (
                        f"./src/files/BPL/enhanced/failed2enhance-{timestamp:%y%m%d}.csv",
                    )
                    save2csv(fail_fh, [row.bibNo, row.oclcNo])
                    raise WorldcatSessionError(f"API error. See report at {fail_fh}")
