import json

from Validation.validation import (
    load_dataset,
    validate_dataset,
    build_rule_summary,
)

from Validation.rules import (
    check_geometry,
    check_vertical_extent,
    check_parent_exists,
    check_elevation,
    check_area,
    check_volume,
    check_no_volume_overlap,
    check_required_fields,
    check_within_parent,
    check_level_sequence,
    check_coordinate_structure,
    check_space_type,
    check_level_z_consistency,
    check_parent_vertical_containment,
    check_footprint_structure,
    check_duplicate_geometry,
    check_level_vertical_order
)

def test_validation_contains_rule_summary():

    data = {
        "parcels": []
    }

    report = validate_dataset(data)

    assert "rule_summary" in report
    assert isinstance(report["rule_summary"], dict)
    

def test_build_rule_summary():

    findings = [
        {
            "rule": "TEST_RULE",
            "severity": "error"
        },
        {
            "rule": "TEST_RULE",
            "severity": "warning"
        },
        {
            "rule": "TEST_RULE",
            "severity": "error"
        },
        {
            "rule": "OTHER_RULE",
            "severity": "info"
        }
    ]

    summary = build_rule_summary(findings)

    assert summary["TEST_RULE"]["errors"] == 2
    assert summary["TEST_RULE"]["warnings"] == 1
    assert summary["TEST_RULE"]["info"] == 0

    assert summary["OTHER_RULE"]["errors"] == 0
    assert summary["OTHER_RULE"]["warnings"] == 0
    assert summary["OTHER_RULE"]["info"] == 1



def test_validation_contains_performance():

    data = load_dataset(
        "data/samples/dwarka_sector12_clean.json"
    )

    report = validate_dataset(data)

    assert "performance" in report
    assert "validation_time_ms" in report["performance"]

    assert isinstance(
        report["performance"]["validation_time_ms"],
        (int, float)
    )

    assert report["performance"]["validation_time_ms"] >= 0

def test_validation_performance_is_not_in_summary():

    data = load_dataset(
        "data/samples/dwarka_sector12_clean.json"
    )

    report = validate_dataset(data)

    assert "performance" not in report["summary"]
    assert "performance" in report



    
def test_conflict_dataset_expected_summary():

    data = load_dataset(
        "data/samples/dwarka_sector12_conflicts.json"
    )

    report = validate_dataset(data)

    assert report["summary"]["parcels_checked"] == 243
    assert report["summary"]["errors"] == 14
    assert report["summary"]["warnings"] == 1

    assert (
        report["rule_summary"]["NO_VOLUME_OVERLAP"]["errors"]
        == 11
    )

    assert (
        report["rule_summary"]["WITHIN_PARENT"]["errors"]
        == 2
    )

    assert (
        report["rule_summary"]["UNIQUE_ULPIN"]["errors"]
        == 1
    )

    assert (
        report["rule_summary"]["LEVEL_Z_CONSISTENCY"]["warnings"]
        == 1
    )





def test_duplicate_ulpin_is_detected():

    data = load_dataset(
        "data/samples/dwarka_sector12_conflicts.json"
    )

    report = validate_dataset(data)

    duplicate_findings = [
        f
        for f in report["findings"]
        if f["rule"] == "UNIQUE_ULPIN"
    ]

    assert len(duplicate_findings) == 1

    assert (
        "DL07TTNF9JN9P4-A-A00-0001-V"
        in duplicate_findings[0]["subjects"]
    )




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
            "bottom_z": 10,
            "top_z": 5
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



def test_invalid_coordinate_structure():

    parcels = [
        {
            "ulpin_3d": "BAD-COORD-001",
            "footprint": [
                [0, 0],
                [10],
                [10, 10],
                [0, 10]
            ]
        }
    ]

    findings = check_coordinate_structure(parcels)

    assert len(findings) > 0
    assert findings[0]["rule"] == "COORDINATE_STRUCTURE"

def test_valid_coordinate_structure():

    parcels = [
        {
            "ulpin_3d": "GOOD-COORD-001",
            "footprint": [
                [0, 0],
                [10, 0],
                [10, 10],
                [0, 10]
            ]
        }
    ]

    findings = check_coordinate_structure(parcels)

    assert findings == []


# 13
def test_invalid_space_type():

    parcels = [
        {
            "ulpin_3d": "TEST-001",
            "space_type": "X",
            "footprint": [
                [0, 0],
                [10, 0],
                [10, 10],
                [0, 10],
                [0, 0]
            ],
            "bottom_z": 0,
            "top_z": 3
        }
    ]

    findings = check_space_type(parcels)

    assert len(findings) == 1
    assert findings[0]["rule"] == "SPACE_TYPE_VALIDATION"
    assert findings[0]["severity"] == "error"

def test_valid_space_type():

    parcels = [
        {
            "ulpin_3d": "TEST-002",
            "space_type": "A"
        }
    ]

    findings = check_space_type(parcels)

    assert len(findings) == 0


#14
def test_level_z_consistent():

    parcels = [
        {
            "ulpin_3d": "TEST-003",
            "level": 2,
            "bottom_z": 6.4
        }
    ]

    findings = check_level_z_consistency(
        parcels,
        floor_height=3.2,
        tolerance=1.5
    )

    assert len(findings) == 0

def test_level_z_inconsistent():

    parcels = [
        {
            "ulpin_3d": "TEST-004",
            "level": 2,
            "bottom_z": 15.0
        }
    ]

    findings = check_level_z_consistency(
        parcels,
        floor_height=3.2,
        tolerance=1.5
    )

    assert len(findings) == 1
    assert findings[0]["rule"] == "LEVEL_Z_CONSISTENCY"



#15
def test_parent_vertical_valid():

    parcels = [
        {
            "ulpin_3d": "PARENT",
            "bottom_z": 0,
            "top_z": 10
        },
        {
            "ulpin_3d": "CHILD",
            "parent": "PARENT",
            "bottom_z": 2,
            "top_z": 5
        }
    ]

    findings = check_parent_vertical_containment(parcels)

    assert len(findings) == 0

def test_parent_vertical_invalid():

    parcels = [
        {
            "ulpin_3d": "PARENT",
            "bottom_z": 0,
            "top_z": 10
        },
        {
            "ulpin_3d": "CHILD",
            "parent": "PARENT",
            "bottom_z": 2,
            "top_z": 15
        }
    ]

    findings = check_parent_vertical_containment(parcels)

    assert len(findings) == 1
    assert findings[0]["rule"] == "PARENT_VERTICAL_CONTAINMENT"


#16
def test_open_footprint():

    parcels = [
        {
            "ulpin_3d": "TEST-005",
            "footprint": [
                [0, 0],
                [10, 0],
                [10, 10],
                [0, 10]
            ]
        }
    ]

    findings = check_footprint_structure(parcels)

    assert len(findings) == 1
    assert findings[0]["rule"] == "FOOTPRINT_STRUCTURE"

def test_valid_footprint():

    parcels = [
        {
            "ulpin_3d": "TEST-006",
            "footprint": [
                [0, 0],
                [10, 0],
                [10, 10],
                [0, 10],
                [0, 0]
            ]
        }
    ]

    findings = check_footprint_structure(parcels)

    assert len(findings) == 0



#17
def test_duplicate_geometry():

    footprint = [
        [0, 0],
        [10, 0],
        [10, 10],
        [0, 10],
        [0, 0]
    ]

    parcels = [
        {
            "ulpin_3d": "A",
            "footprint": footprint,
            "bottom_z": 0,
            "top_z": 3
        },
        {
            "ulpin_3d": "B",
            "footprint": footprint,
            "bottom_z": 1,
            "top_z": 4
        }
    ]

    findings = check_duplicate_geometry(parcels)

    assert len(findings) == 1
    assert findings[0]["rule"] == "DUPLICATE_GEOMETRY"

def test_same_footprint_different_levels():

    footprint = [
        [0, 0],
        [10, 0],
        [10, 10],
        [0, 10],
        [0, 0]
    ]

    parcels = [
        {
            "ulpin_3d": "A",
            "footprint": footprint,
            "bottom_z": 0,
            "top_z": 3
        },
        {
            "ulpin_3d": "B",
            "footprint": footprint,
            "bottom_z": 3.2,
            "top_z": 6
        }
    ]

    findings = check_duplicate_geometry(parcels)

    assert len(findings) == 0

def test_ground_roof_same_footprint_allowed():

    footprint = [
        [0, 0],
        [10, 0],
        [10, 10],
        [0, 10],
        [0, 0]
    ]

    parcels = [
        {
            "ulpin_3d": "BUILDING-G",
            "base_ulpin": "BUILDING",
            "space_type": "G",
            "level": 0,
            "footprint": footprint,
            "bottom_z": -12,
            "top_z": 19.2
        },
        {
            "ulpin_3d": "BUILDING-R",
            "base_ulpin": "BUILDING",
            "space_type": "R",
            "level": 5,
            "footprint": footprint,
            "bottom_z": 16,
            "top_z": 19.2
        }
    ]

    findings = check_duplicate_geometry(parcels)

    assert findings == []




#18
def test_level_vertical_order_invalid():

    parcels = [
        {
            "ulpin_3d": "L0",
            "level": 0,
            "space_type": "A",
            "bottom_z": 0,
            "top_z": 5
        },
        {
            "ulpin_3d": "L1",
            "level": 1,
            "space_type": "A",
            "bottom_z": 3,
            "top_z": 8
        }
    ]

    findings = check_level_vertical_order(parcels)

    assert len(findings) == 1
    assert findings[0]["rule"] == "LEVEL_VERTICAL_ORDER"

def test_level_vertical_order_valid():

    parcels = [
        {
            "ulpin_3d": "L0",
            "level": 0,
            "space_type": "A",
            "bottom_z": 0,
            "top_z": 3
        },
        {
            "ulpin_3d": "L1",
            "level": 1,
            "space_type": "A",
            "bottom_z": 3.2,
            "top_z": 6
        }
    ]

    findings = check_level_vertical_order(parcels)

    assert len(findings) == 0


