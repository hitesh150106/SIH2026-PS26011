import json

from validation import check_vertical_extent


def test_valid_vertical_extent():

    parcels = [
        {
            "ulpin_3d": "A",
            "bottom_z": 0,
            "top_z": 10
        }
    ]

    findings = check_vertical_extent(parcels)

    assert findings == []

    

def test_invalid_vertical_extent():

    parcels = [
        {
            "ulpin_3d": "A",
            "bottom_z": 20,
            "top_z": 10
        }
    ]

    findings = check_vertical_extent(parcels)

    assert len(findings) == 1
    assert findings[0]["rule"] == "VERTICAL_EXTENT"    