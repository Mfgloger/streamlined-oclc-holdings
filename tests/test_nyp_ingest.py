from datetime import datetime, date
import pytest


from src.nyp_ingest import (
    find_oclc_ids,
    get_file_date,
    get_status_id,
    is_research,
    norm_ocn,
    norm_title,
    ocn_str2int,
)


@pytest.mark.parametrize(
    "arg,expectation", [("1", 1), ("", None), ("NYPG724068095-B", None)]
)
def test_ocn_str2int(arg, expectation):
    assert ocn_str2int(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("ocm00000001", 1),
        ("ocn000000001", 1),
        ("on0000000001", 1),
        ("(OCoLC)1234", 1234),
        ("(WaOLN)nyp0067978", None),
        ("NN724068095", None),
    ],
)
def test_norm_ocn(arg, expectation):
    assert norm_ocn(arg) == expectation


@pytest.mark.parametrize(
    "arg, expectation",
    [
        ("match", 1),
        ("create", 2),
        ("unresolved", 3),
        ("data error", 4),
        ("processing error", 5),
        (" data error ", 4),
    ],
)
def test_get_status_id(arg, expectation):
    assert get_status_id(arg) == expectation


def test_file_date():
    handle = "NYP-NYP.1042671.IN.BIB.D20220803.T101322131.1042671.NYP.20220803.StreamlinedHoldings.OCNs.file6.mrc.LbdExceptionReport.txt"
    assert get_file_date(handle) == datetime(2022, 8, 3).date()


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("Foo.", "foo"),
        ("Foo /", "foo"),
        ("Foo \\", "foo"),
        ("Foo, Spam", "foo spam"),
        ("Foo: spam", "foo spam"),
        ("Foo; spam", "foo spam"),
        (" Foo ", "foo"),
        ("'Foo'", "foo"),
        ('"Foo"', "foo"),
        ("Foo@Foo", "foo"),
    ],
)
def test_norm_title(arg, expectation):
    assert norm_title(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ([None, None, "12345", "(OCoLC)12345", None, "12345"], {12345}),
        ([None, None, "ocm00000001", "(WaOLN)0067978", None, "2"], {1, 2}),
        ([None, None, "", "", "", ""], set()),
        (
            [
                None,
                None,
                "NYPG1342-S",
                "(WaOLN)0067978@(OCoLC)12345",
                None,
                "22345@nyp32345",
            ],
            {12345, 22345},
        ),
    ],
)
def test_find_oclc_ids(arg, expectation):
    assert find_oclc_ids(arg) == expectation


@pytest.mark.parametrize(
    "arg,expectation",
    [("RL", True), ("BL", False), ("", False), ("RL@BL", True), ("BL@RL", True)],
)
def is_research(arg, expectation):
    assert is_research(arg) == expectation
