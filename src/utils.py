import csv
import os

from pymarc import Record


def save2csv(dst_fh, row):
    """
    Appends a list with data to a dst_fh csv
    args:
        dst_fh: str, output file
        row: list, list of values to write in a row
    """

    with open(dst_fh, "a", encoding="utf-8") as csvfile:
        out = csv.writer(
            csvfile,
            delimiter=",",
            lineterminator="\n",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        out.writerow(row)


def save2marc(dst_fh: str, record: Record) -> None:
    with open(dst_fh, "ab") as out:
        out.write(record.as_marc())


def start_from_scratch(fh):
    """
    Deletes any exsiting files
    """
    if os.path.isfile(fh):
        os.remove(fh)
