import json
import sys
import tomllib
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from toyitool.api import fetch_order_page


STATUS_KEYS = [
    "status",
    "orderStatus",
    "order_status",
    "produceStatus",
    "productionStatus",
    "production_status",
    "processStatus",
    "factoryStatus",
    "assignStatus",
]


def load_token():
    with open(ROOT_DIR / ".streamlit" / "secrets.toml", "rb") as file:
        secrets = tomllib.load(file)
    config = secrets.get("toyitool", {})
    return config.get("authorization") or config.get("token") or ""


def main():
    token = load_token()
    if not token:
        raise SystemExit("toyitool token/authorization not found in .streamlit/secrets.toml")

    page = fetch_order_page(
        authorization=token,
        page_num=1,
        page_size=10,
        time_type="s.assign_time",
    )
    rows = page["rows"]
    print(json.dumps({
        "total": page["total"],
        "row_count": len(rows),
        "first_row_keys": sorted(rows[0].keys()) if rows else [],
        "normalized_rows": page["normalized_rows"][:3],
    }, ensure_ascii=False, indent=2))

    counters = {}
    for key in STATUS_KEYS:
        counter = Counter()
        for row in rows:
            value = row.get(key)
            if value not in [None, ""]:
                counter[str(value)] += 1
        if counter:
            counters[key] = dict(counter)

    print(json.dumps({"status_distributions": counters}, ensure_ascii=False, indent=2))

    nested_summary = []
    for index, row in enumerate(rows[:3], start=1):
        item = {"row": index}
        for nested_key in ["webOrderList", "gcOrderInfoSubList", "midSubList"]:
            value = row.get(nested_key)
            if isinstance(value, list) and value:
                first_value = value[0]
                item[nested_key] = {
                    "count": len(value),
                    "first_keys": sorted(first_value.keys()) if isinstance(first_value, dict) else type(first_value).__name__,
                    "first_value": first_value if isinstance(first_value, dict) else str(first_value),
                }
            else:
                item[nested_key] = type(value).__name__
        nested_summary.append(item)

    print(json.dumps({"nested_summary": nested_summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
