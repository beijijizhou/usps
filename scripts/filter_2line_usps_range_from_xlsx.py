import json
import sys
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from SDS.usps_label_range_export import DEFAULT_SOURCE_PATH, export_usps_range


def main():
    result = export_usps_range(
        source=DEFAULT_SOURCE_PATH,
        start_date=date(2026, 5, 20),
        end_date=date(2026, 7, 20),
        platform="2号线",
    )
    print(json.dumps({
        "source_path": str(DEFAULT_SOURCE_PATH.resolve()),
        "output_path": str(result["output_path"].resolve()),
        "source_rows": result["source_rows"],
        "filtered_rows": result["filtered_rows"],
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
