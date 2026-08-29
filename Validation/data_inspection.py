import json
import sys


def inspect_dataset(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("\n==============================")
    print("DATASET INSPECTION")
    print("==============================")

    print("Name:", data.get("name"))
    print("Description:", data.get("description"))

    summary = data.get("summary", {})

    print("\nSummary:")
    print("Parcels:", summary.get("parcels"))
    print("Base parcels:", summary.get("base_parcels"))
    print("Levels:", summary.get("levels"))
    print("Total volume:", summary.get("total_volume_m3"))

    parcels = data.get("parcels", [])

    print("\nActual parcel records:", len(parcels))

    if parcels:
        parcel = parcels[0]

        print("\nFirst parcel fields:")
        for key in parcel.keys():
            print(" -", key)

        print("\nFirst parcel:")
        print(json.dumps(parcel, indent=2)[:5000])


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("python data_inspection.py <json_file>")
        sys.exit(1)

    inspect_dataset(sys.argv[1])