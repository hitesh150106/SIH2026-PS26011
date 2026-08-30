import json

from Validation.validation import (
    load_dataset,
    validate_dataset,
)



data = load_dataset("data/samples/dwarka_sector12_clean.json")
report = validate_dataset(data)

errors = [f for f in report["findings"] if f["severity"] == "error"]
print(f"{len(errors)} error(s):")
for e in errors:
    print(json.dumps(e, indent=2))