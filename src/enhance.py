"""
Scripts to obtain Worldcat records and enhance their match in Sierra.
"""
import csv
from datetime import datetime
import json
import os
from typing import Optional
from io import BytesIO


# from bookops_marc import Bib
from bookops_worldcat import WorldcatAccessToken, MetadataSession
from bookops_worldcat.errors import WorldcatSessionError
import pandas as pd
from pymarc import Field, Record, parse_xml_to_array
from requests import Response
from utils import save2csv, save2marc


from bookops_marc import SierraBibReader


def start_from_scratch(fh):
    """
    Deletes any exsiting files
    """
    if os.path.isfile(fh):
        os.remove(fh)


def prepare_identifiers(src_dir: str, library: str) -> None:
    """
    Also combines all BibCrossRef reports and strips out from them leading Sierra # period.

    Args:
        src_dir:              directory where the reports reside
        library:              'BPL' or 'NYPL'
    """
    cross_ref_fh = f"./files/enhanced/{library}/ALL-enhance-cross-ref.csv"
    start_from_scratch(cross_ref_fh)

    for file in os.listdir(src_dir):
        with open(f"{src_dir}/{file}", "r") as f:
            reader = csv.reader(f)
            for row in reader:
                bibNo = row[0][1:]
                oclcNo = row[1]

                save2csv(cross_ref_fh, [bibNo, oclcNo])


def select_for_processing(library: str, start: int, end: int) -> None:
    """
    Selects data to be run through the enhacement process.

    Args:
        library:                'BPL' or 'NYPL'
        start:                  start row of the `ALL-enhance-cross-ref.csv`
        end:                    end row of the `ALL-enhance-cross-ref.csv`
    """
    df = pd.read_csv(
        f"./files/enhanced/{library}/ALL-enhance-cross-ref.csv",
        names=["bibNo", "oclcNo"],
        dtype={"oclcNo": str},
    )

    selected_df = df.iloc[start:end]
    timestamp = datetime.now()

    # file for Sierra list creation
    selected_df.to_csv(
        f"./files/enhanced/{library}/batch-{timestamp:%y%m%d}-sierra-nos.csv",
        index=False,
        header=False,
        columns=["bibNo"],
    )
    # file with oclcNos
    selected_df.to_csv(
        f"./files/enhanced/{library}/batch-{timestamp:%y%m%d}-oclc-nos.csv",
        index=False,
        header=False,
    )


def add_sierra_codes(library: str) -> None:
    """
    Merges OCLC matching report with Sierra bib format and suppression codes.
    Use for full matching routine. Use Bib Cross Reference report in this process.

    Args:
        library:                'BPL' or 'NYPL'
    """
    timestamp = datetime.now()
    oclc_nos_fh = f"./files/enhanced/{library}/batch-{timestamp:%y%m%d}-oclc-nos.csv"
    sierra_codes_fh = (
        f"./files/enhanced/{library}/batch-{timestamp:%y%m%d}-sierra-codes.txt"
    )
    combined_fh = (
        f"./files/enhanced/{library}/batch-{timestamp:%y%m%d}-combined-data.csv"
    )

    odf = pd.read_csv(oclc_nos_fh, names=["bibNo", "oclcNo"], dtype={"oclcNo": str})
    odf["bibNo"] = odf["bibNo"].str.replace(".", "")
    sdf = pd.read_csv(
        sierra_codes_fh, names=["bibNo", "bFormat", "bDisplay"], skiprows=[0]
    )
    assert odf.shape[0] == sdf.shape[0]

    df = pd.merge(odf, sdf, on="bibNo")
    df.to_csv(combined_fh, index=False, header=False)


def get_worldcat_bib(
    session: MetadataSession, oclcNo: str, n: int
) -> Optional[Response]:
    """
    Queries Worldcat for given OCLC record #

    Args:
        oclcNo:                 OCLC #
    """
    response = session.get_full_bib(oclcNo)
    if response.status_code == 200:
        print(f"{n}: {response.url} = OK")
        return response
    else:
        print(f"{n}: {response.request.url} = {response.status_code}")
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


def add_import_config_tags(
    record: Record, sierra_no: str, sierra_format: str, sierra_opac: str
) -> None:
    """
    Supports only BPL at the moment!!
    """

    # add matching point
    record.add_field(
        Field(tag="907", indicators=[" ", " "], subfields=["a", f".{sierra_no}"])
    )

    # add command tag
    command_str = f"*b2={sierra_format}"
    if sierra_opac != "-":
        command_str += f";b3={sierra_opac}"
    record.add_field(
        Field(tag="949", indicators=[" ", " "], subfields=["a", f"{command_str};"])
    )

    # add initials
    record.add_field(Field(tag="947", indicators=[" ", " "], subfields=["a", "SHPbot"]))


def launch_enhancement(
    library: str,
    creds: dict,
    src_fh: str = None,
    start: int = 0,
    out_fh: str = None,
) -> None:
    """

    Args:
        library:            'BPL' or 'NYPL'
        creds:              path to Worldcat Metadata API credentials
        src_fh:             file to be used for processing
        start:              starting row in the `src_fh`  (inclusive and skipping header)
                            defaults to `./files/enhanced/{library}/batch-{yymmdd}-combined-data.csv`
        out_fh:             output MARC file
                            defaults to `./files/enhanced/{library}/batch-{yymmdd}-worldcat-bibs.mrc`
    """

    # if no src data provided assume daily batch
    timestamp = datetime.now()
    if src_fh is None:
        src_fh = (
            f"./files/enhanced/{library}/batch-{timestamp:%y%m%d}-combined-data.csv"
        )
    if out_fh is None:
        out_fh = (
            f"./files/enhanced/{library}/batch-{timestamp:%y%m%d}-worldcat-bibs.mrc"
        )

    token = get_token(creds)

    with MetadataSession(authorization=token) as session:

        # get source data for queries
        with open(src_fh, "r") as src:
            reader = csv.reader(src)
            for row in reader:
                bibNo = row[0]
                oclcNo = row[1]
                bFormat = row[2]
                bDisplay = row[3]
                response = get_worldcat_bib(session, oclcNo, start)

                if response is not None:
                    data = BytesIO(response.content)
                    worldcat_bib = parse_xml_to_array(data)[0]
                    bib = add_import_config_tags(worldcat_bib, bibNo, bFormat, bDisplay)
                    save2marc(out_fh, worldcat_bib)
                else:
                    print(f"Error in row {start}: {row}")
                    raise WorldcatSessionError("API error.")

                start += 1


def manipulate_worldcat_records(library: str, marc_fh: str = None):
    """
    Removes undesired MARC tags, cleans up subject headings.

    Args:
        libary:             'BPL' or 'NYPL'
        marc_fh:            path to MARC21 file with downloaded records
                            defaults to `./files/enhanced/{library}/streamlined-holdings-enhancement-batch-{yymmdd}.mrc`
    """
    timestamp = datetime.now()
    if marc_fh is None:
        marc_fh = (
            f"./files/enhanced/{library}/batch-{timestamp:%y%m%d}-worldcat-bibs.mrc"
        )
        out_fh = f"./files/enhanced/{library}/streamlined-holdings-enhancement-batch-{timestamp:%y%m%d}.mrc"
    else:
        fname = os.path.basename(marc_fh)[:-4]
        dname = os.path.dirname(marc_fh)
        oname = f"{fname}-PRC.mrc"
        out_fh = os.path.join(dname, oname)

    start_from_scratch(out_fh)

    with open(marc_fh, "rb") as marcfile:
        reader = SierraBibReader(marcfile)
        for bib in reader:
            bib.remove_fields("019", "029", "263", "938")
            bib.remove_unsupported_subjects()

            save2marc(out_fh, bib)


if __name__ == "__main__":
    # cross_ref_dir = "./files/full_bibs"
    # prepare_identifiers(cross_ref_dir)

    # select_for_processing("BPL", 0, 1000)

    # add_sierra_codes("BPL")

    # creds_fh = os.path.join(os.getenv("USERPROFILE"), ".oclc/bpl_overload.json")
    # launch_enhancement("BPL", creds_fh)

    # prep records
    manipulate_worldcat_records("BPL")
