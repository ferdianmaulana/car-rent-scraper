"""Save scraped cars to JSON or CSV."""

import csv
import json


def save_json(cars: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cars, f, ensure_ascii=False, indent=2)


def save_csv(cars: list[dict], path: str) -> None:
    """One row per car + vendor; facilities stored as a JSON array string."""
    fields = ["car_name", "koper", "penumpang", "transmission",
              "vendor_name", "price", "original_price", "facilities"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # -sig so Excel reads UTF-8
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for car in cars:
            base = {"car_name": car["name"], "koper": car["koper"],
                    "penumpang": car["penumpang"], "transmission": car["transmission"]}
            for v in car.get("vendors") or [{}]:
                writer.writerow({
                    **base,
                    "vendor_name": v.get("name"),
                    "price": v.get("price"),
                    "original_price": v.get("original_price"),
                    "facilities": json.dumps(v["facilities"], ensure_ascii=False) if "facilities" in v else None,
                })


def save(cars: list[dict], path: str) -> None:
    """Pick the format from the file extension: .csv, otherwise JSON."""
    (save_csv if path.lower().endswith(".csv") else save_json)(cars, path)
