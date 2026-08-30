import json

from shapely.geometry import Polygon

from Validation.rules import _is_ancestor


DATA_FILE = "data/samples/dwarka_sector12_clean.json"


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    parcels = data.get("parcels", [])

    parcel_map = {
        parcel.get("ulpin_3d"): parcel
        for parcel in parcels
        if parcel.get("ulpin_3d")
    }

    polygons = {
        parcel["ulpin_3d"]: Polygon(parcel["footprint"])
        for parcel in parcels
        if parcel.get("ulpin_3d") and parcel.get("footprint")
    }

    overlaps_found = 0

    for index, first in enumerate(parcels):
        first_id = first.get("ulpin_3d")

        if not first_id or first_id not in polygons:
            continue

        for second in parcels[index + 1:]:
            second_id = second.get("ulpin_3d")

            if not second_id or second_id not in polygons:
                continue

            if _is_ancestor(first_id, second_id, parcel_map):
                continue

            first_polygon = polygons[first_id]
            second_polygon = polygons[second_id]

            xy_overlap = first_polygon.intersection(second_polygon).area

            z_overlap = (
                min(
                    first.get("top_z", 0),
                    second.get("top_z", 0),
                )
                - max(
                    first.get("bottom_z", 0),
                    second.get("bottom_z", 0),
                )
            )

            if xy_overlap <= 0.001 or z_overlap <= 0.01:
                continue

            overlaps_found += 1

            print(f"\n{overlaps_found}.")
            print(
                "A:",
                first_id,
                "type=",
                first.get("space_type"),
                "level=",
                first.get("level"),
                "Z=",
                first.get("bottom_z"),
                first.get("top_z"),
                "parent=",
                first.get("parent"),
            )

            print(
                "B:",
                second_id,
                "type=",
                second.get("space_type"),
                "level=",
                second.get("level"),
                "Z=",
                second.get("bottom_z"),
                second.get("top_z"),
                "parent=",
                second.get("parent"),
            )

            print("XY overlap:", round(xy_overlap, 2))
            print("Z overlap:", round(z_overlap, 2))
            print(
                "A ancestor of B:",
                _is_ancestor(first_id, second_id, parcel_map),
            )

            if overlaps_found >= 15:
                break

        if overlaps_found >= 15:
            break

    print(f"\nTotal overlaps displayed: {overlaps_found}")


if __name__ == "__main__":
    main()