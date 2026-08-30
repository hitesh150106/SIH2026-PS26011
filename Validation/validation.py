import json
import sys
from pathlib import Path
import time

from .rules import (
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
    check_level_sequence,
    check_coordinate_structure,
    check_space_type,
    check_level_z_consistency,
    check_parent_vertical_containment,
    check_footprint_structure,
    check_duplicate_geometry,
    check_level_vertical_order
)

RULES = [
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
    check_level_sequence,
    check_coordinate_structure,
    check_space_type,
    check_level_z_consistency,
    check_parent_vertical_containment,
    check_footprint_structure,
    check_duplicate_geometry,
    check_level_vertical_order
]


def load_dataset(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_rule_summary(findings):
    """
    Groups findings by rule name, with a severity breakdown per rule.

    {
      "NO_VOLUME_OVERLAP": {"errors": 11, "warnings": 0, "info": 0},
      "WITHIN_PARENT":     {"errors": 2,  "warnings": 0, "info": 0},
      ...
    }

    Every rule that produced at least one finding appears here -
    rules with zero findings are simply absent (not listed with all-zero
    counts), so the frontend only has to iterate over rules that actually
    have something to show.
    """

    summary = {}

    for f in findings:

        rule = f["rule"]

        if rule not in summary:
            summary[rule] = {
                "errors": 0,
                "warnings": 0,
                "info": 0
            }

        severity = f["severity"]

        if severity == "error":
            summary[rule]["errors"] += 1
        elif severity == "warning":
            summary[rule]["warnings"] += 1
        elif severity == "info":
            summary[rule]["info"] += 1

    return summary


def validate_dataset(data):

    start_time = time.perf_counter()

    parcels = data.get("parcels", [])

    findings = []

    # Run validation rules
    for rule in RULES:
        findings.extend(rule(parcels))

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

    validation_time_ms = (
        time.perf_counter() - start_time
    ) * 1000

    return {
        "clean": len(errors) == 0,

        "summary": {
            "parcels_checked": len(parcels),
            "errors": len(errors),
            "warnings": len(warnings),
            "info": len(infos)
        },

        "performance": {
            "validation_time_ms": round(
                validation_time_ms,
                2
            )
        },

        "rule_summary": build_rule_summary(findings),

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

    print("Info:", report["summary"]["info"])

    print(
        "Validation time:",
        report["performance"]["validation_time_ms"],
        "ms"
    )

    print(
        "Status:",
        "CLEAN" if report["clean"]
        else "CONFLICTS FOUND")

    if report["rule_summary"]:

        print("\n------------------------------")
        print("Top Issues")
        print("------------------------------")

        ranked = sorted(
            report["rule_summary"].items(),
            key=lambda item: (item[1]["errors"], item[1]["warnings"]),
            reverse=True
        )

        for rule_name, counts in ranked:

            parts = []

            if counts["errors"]:
                parts.append(f"{counts['errors']} error(s)")

            if counts["warnings"]:
                parts.append(f"{counts['warnings']} warning(s)")

            if counts["info"]:
                parts.append(f"{counts['info']} info")

            print(f"{rule_name:<28} {', '.join(parts)}")

    output_file = "data/output/validation_report.json"

    save_report(report, output_file)

    print("\nReport saved to:", output_file)


if __name__ == "__main__":
    main()