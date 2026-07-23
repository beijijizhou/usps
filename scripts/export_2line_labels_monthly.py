import calendar
import importlib.util
import json
from datetime import date
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("export_sds_labels_excel.py")
spec = importlib.util.spec_from_file_location("sds_label_exporter", SCRIPT_PATH)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)

PLATFORM = "2号线"
START_YEAR = 2025
START_MONTH = 10
END_YEAR = 2026
END_MONTH = 7
OUTPUT_DIR = Path("output/2号线_USPS月度面单数据")


def iter_months(start_year, start_month, end_year, end_month):
    year = start_year
    month = start_month

    while (year, month) <= (end_year, end_month):
        last_day = calendar.monthrange(year, month)[1]
        yield year, month, date(year, month, 1), date(year, month, last_day)

        month += 1
        if month == 13:
            year += 1
            month = 1


def export_month(secrets, year, month, start_date, end_date):
    month_label = f"{year}-{month:02d}"
    output_path = OUTPUT_DIR / f"2号线_USPS面单数据_{month_label}.xlsx"

    if output_path.exists():
        print(f"{month_label}: 已存在，跳过 {output_path}", flush=True)
        return {
            "month": month_label,
            "output_path": str(output_path.resolve()),
            "skipped": True,
        }

    exporter.START_DATE = start_date
    exporter.END_DATE = end_date
    exporter.OUTPUT_PATH = output_path
    exporter.USPS_ONLY = True

    print(f"{month_label}: 开始导出 {start_date} 到 {end_date}", flush=True)
    rows, errors = exporter.export_platform(secrets, PLATFORM)
    sheets = {
        "面单数据": exporter.build_sheet_rows(exporter.LABEL_COLUMNS, rows),
        "错误记录": exporter.build_sheet_rows(exporter.ERROR_COLUMNS, errors),
    }
    exporter.write_xlsx(output_path, sheets)
    print(f"{month_label}: 完成，面单记录 {len(rows)}，错误 {len(errors)}", flush=True)

    return {
        "month": month_label,
        "output_path": str(output_path.resolve()),
        "label_rows": len(rows),
        "errors": errors,
        "skipped": False,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    secrets = exporter.load_secrets()
    summary = []

    for year, month, start_date, end_date in iter_months(START_YEAR, START_MONTH, END_YEAR, END_MONTH):
        summary.append(export_month(secrets, year, month, start_date, end_date))

    summary_path = OUTPUT_DIR / "导出汇总.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output_dir": str(OUTPUT_DIR.resolve()),
        "months": len(summary),
        "summary_path": str(summary_path.resolve()),
    }, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
