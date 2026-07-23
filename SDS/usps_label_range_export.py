import importlib.util
import re
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_SOURCE_PATH = Path("output/sds_labels_2号线_2026-05_to_2026-07.xlsx")
OUTPUT_DIR = Path("output")
NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

EXPORTER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "export_sds_labels_excel.py"
spec = importlib.util.spec_from_file_location("sds_label_exporter", EXPORTER_PATH)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def read_shared_strings(workbook):
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    strings = []
    for item in root.findall("main:si", NS):
        text_parts = [node.text or "" for node in item.findall(".//main:t", NS)]
        strings.append("".join(text_parts))
    return strings


def column_index(cell_ref):
    letters = re.sub(r"[^A-Z]", "", cell_ref)
    index = 0
    for letter in letters:
        index = index * 26 + ord(letter) - ord("A") + 1
    return index - 1


def read_first_sheet(source):
    with zipfile.ZipFile(source) as workbook:
        shared_strings = read_shared_strings(workbook)
        root = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))

    rows = []
    for row_node in root.findall(".//main:sheetData/main:row", NS):
        values = []
        for cell in row_node.findall("main:c", NS):
            cell_ref = cell.attrib.get("r", "")
            target_index = column_index(cell_ref)
            while len(values) <= target_index:
                values.append("")

            value_node = cell.find("main:v", NS)
            raw_value = value_node.text if value_node is not None else ""
            if cell.attrib.get("t") == "s" and raw_value:
                values[target_index] = shared_strings[int(raw_value)]
            else:
                values[target_index] = raw_value
        rows.append(values)
    return rows


def parse_time(value):
    value = str(value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def is_usps_row(row):
    tracking = str(row.get("物流单号", "")).strip()
    carrier = str(row.get("物流渠道", "")).upper()
    provider = str(row.get("服务商", "")).upper()
    logistics_code = str(row.get("物流代码ID", "")).upper()
    return (
        tracking.startswith("9")
        or "USPS" in carrier
        or "USPS" in provider
        or "USPS" in logistics_code
    )


def normalize_records(raw_rows):
    if not raw_rows:
        return []
    headers = raw_rows[0]
    return [dict(zip(headers, row)) for row in raw_rows[1:]]


def filter_usps_records(records, start_at, end_at, platform="全部平台"):
    filtered = []
    for record in records:
        if platform != "全部平台" and str(record.get("平台", "")).strip() != platform:
            continue

        start_time = parse_time(record.get("开始时间"))
        if not start_time or not (start_at <= start_time <= end_at):
            continue

        if is_usps_row(record):
            filtered.append(record)

    return sorted(filtered, key=lambda row: (row.get("物流单号", ""), row.get("SDS订单号", "")))


def build_xlsx(path, records):
    sheets = {
        "面单数据": exporter.build_sheet_rows(exporter.LABEL_COLUMNS, records),
        "错误记录": exporter.build_sheet_rows(exporter.ERROR_COLUMNS, []),
    }
    exporter.write_xlsx(path, sheets)


def export_usps_range(source, start_date, end_date, platform="2号线"):
    start_at = datetime.combine(start_date, datetime.min.time())
    end_at = datetime.combine(end_date, datetime.max.time()).replace(microsecond=0)
    raw_rows = read_first_sheet(source)
    records = normalize_records(raw_rows)
    filtered = filter_usps_records(records, start_at, end_at, platform=platform)

    safe_platform = platform.replace("/", "-")
    output_name = f"{safe_platform}_USPS面单数据_{start_date:%Y-%m-%d}_to_{end_date:%Y-%m-%d}.xlsx"
    output_path = OUTPUT_DIR / output_name
    build_xlsx(output_path, filtered)
    workbook_bytes = output_path.read_bytes()

    return {
        "source_rows": len(records),
        "filtered_rows": len(filtered),
        "output_path": output_path,
        "output_name": output_name,
        "workbook_bytes": workbook_bytes,
        "records": filtered,
    }


def uploaded_file_to_buffer(uploaded_file):
    return BytesIO(uploaded_file.getvalue())
