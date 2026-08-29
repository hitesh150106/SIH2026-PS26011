import json

from validation import load_dataset, check_geometry


def test_valid_geometry():

    parcels = [
        {
            "ulpin_3d": "A",
            "footprint": [
                [0, 0],
                [10, 0],
                [10, 10],
                [0, 10]
            ]
        }
    ]

    findings = check_geometry(parcels)

    assert findings == []


def test_invalid_geometry():

    parcels = [
        {
            "ulpin_3d": "A",
            "footprint": [
                [0, 0],
                [10, 10],
                [0, 10],
                [10, 0]
            ]
        }
    ]

    findings = check_geometry(parcels)

    assert len(findings) > 0  