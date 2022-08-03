import csv
import os

from utils import save2csv


def find_created(fh_in: str, fh_out: str) -> None:
    with open(fh_in, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[-1] == "create":
                save2csv(fh_out, row)


def find_invalid_oclc_no(fh_in: str, fh_out: str) -> None:
    with open(fh_in, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[1] == "":
                save2csv(fh_out, row)


def find_509_error(fh_in: str, fh_out: str) -> None:
    with open(fh_in, "r") as f:
        reader = csv.reader(f, delimiter="|")
        for row in reader:
            if row[-1] == "Invalid tag 509.":
                save2csv(fh_out, [row[1]])
                # print(row)


def find_008_38_error(fh_in: str, fh_out: str) -> None:
    with open(fh_in, "r") as f:
        reader = csv.reader(f, delimiter="|")
        for row in reader:
            if row[-1] == "Invalid code in Modified Record (008/38).":
                save2csv(fh_out, [row[1]])


def find_provisional(fdir: str, fh_out: str) -> None:
    for file in os.listdir(fdir):
        if "BibUnresolvedCrossRefReport" in os.path.basename(file):
            print(os.path.basename(file))
            with open(f"./files/provisional/{file}", "r") as f:
                reader = csv.reader(f, delimiter="\t")
                for row in reader:
                    oclcNo = f"(OCoLC){row[1]}"
                    save2csv(fh_out, [None, oclcNo])


def find_changed_oclc_no(fdir: str, fh_out: str) -> None:
    """
    Finds and saves into a separate file records which oclc # has changed

    Args:
        fdir:               directory with Processing Report files
        fh_out:             path to output report
    """
    for file in os.listdir(fdir):
        if "BibProcessingReport" in os.path.basename(file):
            print(f"Parsing: {os.path.basename(file)}")
            with open(f"{fdir}/{file}", "r") as f:
                reader = csv.reader(f, delimiter="|")
                for row in reader:
                    bibNo = row[1][1:]
                    oldOclc = row[2]
                    newOclc = row[3]
                    if oldOclc != newOclc:
                        save2csv(fh_out, [bibNo, oldOclc, newOclc])


if __name__ == "__main__":
    # fh_in = "./files/FullMatch.efc.enhance.csv"
    # fh_out = "./files/FullMatch.efc.enhance-import-info.csv"
    # find_invalid_oclc_no(fh_in, fh_out)

    # fh_in = "./files/509/FullMatch.WL.mrc.BibExceptionReport.txt"
    # fh_out = "./files/509/008error.localNos.csv"
    # find_509_error(fh_in, fh_out)

    # fdir = "./files/provisional"
    # fh_out = "./files/provisional/all-provisional.csv"
    # find_provisional(fdir, fh_out)

    fdir = "./files/ocnBibProcReports"
    fh_out = "./files/changed_oclc_no.csv"
    find_changed_oclc_no(fdir, fh_out)
