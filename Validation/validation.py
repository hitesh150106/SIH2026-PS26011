import json
import sys

from Validation.validation import (
    load_dataset,
    validate_dataset,
)

from Validation.rules import (
    check_unique_ulpins,
    check_geometry,
    check_elevation,
    check_area,
    check_volume,
    check_parent_exists,
    check_no_volume_overlap,
    check_required_fields,
    check_vertical_extent,
    check_within_parent,
    check_level_sequence
)


def load_dataset(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_dataset(data):

    parcels = data.get("parcels", [])

    findings = []

    # Run validation rules
    findings.extend(check_unique_ulpins(parcels))
    findings.extend(check_geometry(parcels))
    findings.extend(check_elevation(parcels))
    findings.extend(check_area(parcels))
    findings.extend(check_volume(parcels))
    findings.extend(check_parent_exists(parcels))    
    findings.extend(check_no_volume_overlap(parcels))
    findings.extend(check_required_fields(parcels))
    findings.extend(check_vertical_extent(parcels))  
    findings.extend(check_within_parent(parcels))
    findings.extend(check_level_sequence(parcels))

    errors = [
        f for f in findings
        if f["severity"] == "error"
    ]

    warnings = [
        f for f in findings
        if f["severity"] == "warning"
    ]

    infos = [
        f for f in findings
        if f["severity"] == "info"
    ]

    return {
        "clean": len(errors) == 0,

        "summary": {
            "parcels_checked": len(parcels),
            "errors": len(errors),
            "warnings": len(warnings),
            "info": len(infos)
        },

        "findings": findings
    }


def save_report(report, output_file):

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            indent=2
        )


def main():

    if len(sys.argv) < 2:

        print("Usage: python validation.py <input.json>")

        sys.exit(1)

    input_file = sys.argv[1]

    data = load_dataset(input_file)

    report = validate_dataset(data)

    print("\n==============================")
    print("3D CADASTRAL VALIDATION")
    print("==============================")

    print("Parcels checked:", report["summary"]["parcels_checked"])

    print("Errors:", report["summary"]["errors"])

    print("Warnings:", report["summary"]["warnings"])

    print("Info:",report["summary"]["info"])

    print(
        "Status:",
        "CLEAN" if report["clean"]
        else "CONFLICTS FOUND")

    output_file = "data/output/validation_report.json"

    save_report(report,output_file)

    print("\nReport saved to:",output_file)


if __name__ == "__main__":
    main()