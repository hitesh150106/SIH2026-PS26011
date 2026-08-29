import json

from validation import load_dataset, validate_dataset , check_geometry , check_vertical_extent , check_parent_exists , check_elevation , check_area , check_volume , check_no_volume_overlap , check_required_fields , check_vertical_extent , check_within_parent , check_level_sequence


def test_clean_dwarka():

    data = load_dataset(
        "data/samples/dwarka_sector12_clean.json"
    )

    report = validate_dataset(data)

    assert report["clean"] is True

def test_conflict_dwarka():

    data = load_dataset(
        "data/samples/dwarka_sector12_conflicts.json"
    )

    report = validate_dataset(data)

    assert report["clean"] is False

    assert report["summary"]["errors"] > 0



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



def test_missing_parent():

    data = [
        {
            "ulpin_3d": "CHILD-001",
            "parent": "PARENT-DOES-NOT-EXIST"
        }
    ]

    findings = check_parent_exists(data)

    assert len(findings) == 1
    assert findings[0]["rule"] == "PARENT_EXISTS"    



def test_invalid_elevation():

    parcel = {
        "ulpin_3d": "TEST-ELEV-001",
        "footprint": [
            [0, 0],
            [10, 0],
            [10, 10],
            [0, 10]
        ],
        "bottom_z": 10,
        "top_z": 5
    }

    findings = check_elevation([parcel])

    assert len(findings) > 0



def test_invalid_area():

    parcel = {
        "ulpin_3d": "TEST-AREA-001",
        "footprint": [
            [0, 0],
            [10, 0],
            [10, 10],
            [0, 10]
        ],
        "area_m2": 500
    }

    findings = check_area([parcel])

    assert len(findings) > 0



def test_invalid_volume():

    parcel = {
        "ulpin_3d": "TEST-VOLUME-001",
        "footprint": [
            [0, 0],
            [10, 0],
            [10, 10],
            [0, 10]
        ],
        "area_m2": 100,
        "bottom_z": 0,
        "top_z": 10,
        "volume_m3": 5000
    }

    findings = check_volume([parcel])

    assert len(findings) > 0



def test_3d_volume_overlap():

    parcels = [
        {
            "ulpin_3d": "A",
            "footprint": [
                [0, 0],
                [10, 0],
                [10, 10],
                [0, 10]
            ],
            "bottom_z": 0,
            "top_z": 10
        },
        {
            "ulpin_3d": "B",
            "footprint": [
                [5, 5],
                [15, 5],
                [15, 15],
                [5, 15]
            ],
            "bottom_z": 5,
            "top_z": 15
        }
    ]

    findings = check_no_volume_overlap(parcels)

    assert len(findings) > 0



def test_required_field_missing():

    parcel = {
        "base_ulpin": "TEST-001",
        "space_type": "A",
        "level": 1,
        "footprint": [
            [0, 0],
            [10, 0],
            [10, 10],
            [0, 10]
        ]
    }

    findings = check_required_fields([parcel])

    assert len(findings) > 0



def test_invalid_vertical_structure():

    parcels = [
        {
            "ulpin_3d": "FLOOR-0",
            "level": 0,
            "bottom_z": 0,
            "top_z": 3
        },
        {
            "ulpin_3d": "FLOOR-1",
            "level": 1,
            "bottom_z": 5,
            "top_z": 8
        }
    ]

    findings = check_vertical_extent(parcels)

    assert len(findings) > 0



def test_child_outside_parent():

    parcels = [
        {
            "ulpin_3d": "PARENT",
            "parent": None,
            "footprint": [
                [0, 0],
                [20, 0],
                [20, 20],
                [0, 20]
            ]
        },
        {
            "ulpin_3d": "CHILD",
            "parent": "PARENT",
            "footprint": [
                [30, 30],
                [40, 30],
                [40, 40],
                [30, 40]
            ]
        }
    ]

    findings = check_within_parent(parcels)

    assert len(findings) > 0



def test_invalid_level_sequence():

    parcels = [
        {
            "ulpin_3d": "L0",
            "level": 0
        },
        {
            "ulpin_3d": "L1",
            "level": 1
        },
        {
            "ulpin_3d": "L3",
            "level": 3
        }
    ]

    findings = check_level_sequence(parcels)

    assert len(findings) > 0

