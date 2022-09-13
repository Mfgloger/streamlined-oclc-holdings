import sys
import argparse


from src.bpl_ingest import select_for_sierra_list_creation, parse_sierra_bib
from src.enhance import launch_bpl_enhancement


def main(args: list) -> None:
    """
    launches enrichment of local records from CLI.
    """
    parser = argparse.ArgumentParser(
        prog="EnrichBib",
        description="Enriches local bibs with Worldcat metadata based on the OCLC Streamlined Holdings project.",
    )

    parser.add_argument(
        "library", help="'BPL' or 'NYPL'", type=str, choices=["BPL", "NYPL"]
    )

    parser.add_argument(
        "action",
        help=(
            "'select2enrich' selects a batch of records for enrichment and "
            "results in a list of Sierra bib number to be used to create a "
            "list of records in Sierra, 'enrich' uses exported from "
            "Sierra MARC records and runs enrichment process."
        ),
        type=str,
        choices=["select2enrich", "enrich", "enrich-resume"],
    )

    parser.add_argument(
        "volume",
        help="size of batch for processing",
        type=int,
        nargs="?",
        default=5000,
    )

    pargs = parser.parse_args(args)

    if pargs.library == "BPL":
        if pargs.action == "select2enrich":
            print("Extracting data from BPL database for processing...")
            out_fh = select_for_sierra_list_creation(pargs.volume)
            print(f"Created a file with Sierra bib numbers to use: {out_fh}")
        elif pargs.action == "enrich":
            print("Parsing prepared MARC file...")
            parse_sierra_bib()
            print("Obtaining Worldcat records...")
            launch_bpl_enhancement()
        elif pargs.action == "enrich-resume":
            print("Resuming enrichment...")
            launch_bpl_enhancement()

    elif pargs.library == "NYPL":
        print("Workflow not implemented yet. Exiting...")


if __name__ == "__main__":
    main(sys.argv[1:])
