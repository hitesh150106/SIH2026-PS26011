import json

from validation import load_dataset , check_unique_ulpin


def test_unique_ulpin():

    parcels = [
        {"ulpin_3d": "A"},
        {"ulpin_3d": "B"}
    ]

    findings = check_unique_ulpin(parcels)

    assert findings == []


def test_duplicate_ulpin():

    parcels = [
        {"ulpin_3d": "A"},
        {"ulpin_3d": "A"}
    ]

    findings = check_unique_ulpin(parcels)

    assert len(findings) == 1
    assert findings[0]["rule"] == "UNIQUE_ULPIN"