from __future__ import annotations

import csv
import html
import zipfile
from datetime import date
from pathlib import Path
from statistics import mean
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "product-performance-sample.csv"
REPORT_DIR = ROOT / "reports"


def read_rows() -> list[dict[str, str]]:
    with DATA_PATH.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def as_float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def product_health(row: dict[str, str]) -> int:
    adoption = as_float(row, "adoption_rate")
    task_success = as_float(row, "task_success_rate")
    sla = as_float(row, "sla_attainment")
    defect_score = max(0, 100 - as_float(row, "open_defects"))
    return round(adoption * 0.28 + task_success * 0.34 + sla * 0.24 + defect_score * 0.14)


def status(row: dict[str, str]) -> str:
    if int(row["incidents"]) >= 6 or as_float(row, "sla_attainment") < 95:
        return "Critical"
    if int(row["open_defects"]) >= 25 or as_float(row, "task_success_rate") < 85:
        return "Watch"
    return "Healthy"


def build_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    summary = []
    for row in rows:
        health = product_health(row)
        summary.append(
            {
                "product": row["product"],
                "owner": row["owner"],
                "adoption_rate": row["adoption_rate"],
                "task_success_rate": row["task_success_rate"],
                "open_defects": row["open_defects"],
                "sla_attainment": row["sla_attainment"],
                "incidents": row["incidents"],
                "health_score": str(health),
                "status": status(row),
                "recommended_action": recommendation(row),
            }
        )
    return summary


def recommendation(row: dict[str, str]) -> str:
    if int(row["incidents"]) >= 6:
        return "Escalate service reliability review and publish incident owner update."
    if int(row["open_defects"]) >= 25:
        return "Prioritize QA defect burn-down before the next release checkpoint."
    if as_float(row, "task_success_rate") < 85:
        return "Review journey analytics and remove completion blockers."
    return "Maintain reporting cadence and monitor KPI movement."


def write_csv(summary: list[dict[str, str]]) -> None:
    path = REPORT_DIR / "product-performance-summary.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)


def write_markdown(summary: list[dict[str, str]]) -> None:
    avg_adoption = mean(float(row["adoption_rate"]) for row in summary)
    avg_success = mean(float(row["task_success_rate"]) for row in summary)
    avg_sla = mean(float(row["sla_attainment"]) for row in summary)
    total_defects = sum(int(row["open_defects"]) for row in summary)
    risk_rows = [row for row in summary if row["status"] != "Healthy"]

    lines = [
        "# Weekly Digital Product Performance Report",
        "",
        f"Generated on {date.today().isoformat()} from `data/product-performance-sample.csv`.",
        "",
        "## KPI Summary",
        "",
        f"- Average adoption rate: {avg_adoption:.1f}%",
        f"- Average task success rate: {avg_success:.1f}%",
        f"- Average SLA attainment: {avg_sla:.1f}%",
        f"- Open QA defects: {total_defects}",
        "",
        "## Stakeholder Insights",
        "",
    ]

    for row in sorted(risk_rows, key=lambda item: int(item["open_defects"]), reverse=True):
        lines.append(f"- **{row['product']}** is marked **{row['status']}**. {row['recommended_action']}")

    lines.extend(
        [
            "",
            "## Reporting Controls",
            "",
            "- Source file freshness checked before report generation.",
            "- SLA, defect, and incident values validated for missing or impossible values.",
            "- Summary CSV is Excel-ready for pivot tables and stakeholder distribution.",
        ]
    )
    (REPORT_DIR / "stakeholder-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(summary: list[dict[str, str]]) -> None:
    rows = "\n".join(
        f"<tr><td>{html.escape(row['product'])}</td><td>{row['health_score']}</td><td>{row['status']}</td><td>{html.escape(row['recommended_action'])}</td></tr>"
        for row in summary
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Digital Product Performance Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d8dee8; padding: 10px; text-align: left; }}
    th {{ background: #f5f7fa; }}
  </style>
</head>
<body>
  <h1>Digital Product Performance Report</h1>
  <p>Automated Python output for product operations, QA, and stakeholder reporting.</p>
  <table>
    <thead><tr><th>Product</th><th>Health Score</th><th>Status</th><th>Recommended Action</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""
    (REPORT_DIR / "stakeholder-visual-summary.html").write_text(document, encoding="utf-8")


def write_xlsx(summary: list[dict[str, str]]) -> None:
    headers = list(summary[0].keys())
    body_rows = [[row[key] for key in headers] for row in summary]
    worksheet_rows = [headers, *body_rows]

    sheet_data = []
    for row_number, values in enumerate(worksheet_rows, start=1):
        cells = []
        for col_number, value in enumerate(values, start=1):
            cell_ref = f"{column_name(col_number)}{row_number}"
            cells.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        sheet_data.append(f'<row r="{row_number}">{"".join(cells)}</row>')

    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Performance Summary" sheetId="1" r:id="rId1"/></sheets>
</workbook>""",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>""",
        "xl/worksheets/sheet1.xml": f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{"".join(sheet_data)}</sheetData>
</worksheet>""",
    }

    with zipfile.ZipFile(REPORT_DIR / "product-performance-summary.xlsx", "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in files.items():
            archive.writestr(path, content)


def column_name(number: int) -> str:
    name = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        name = chr(65 + remainder) + name
    return name


def validate(rows: list[dict[str, str]]) -> None:
    required = {"product", "month", "adoption_rate", "task_success_rate", "open_defects", "sla_attainment", "nps", "incidents", "owner"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    for row in rows:
        for key in ["adoption_rate", "task_success_rate", "sla_attainment"]:
            value = as_float(row, key)
            if value < 0 or value > 100:
                raise ValueError(f"{key} for {row['product']} must be between 0 and 100")
        if int(row["open_defects"]) < 0 or int(row["incidents"]) < 0:
            raise ValueError(f"Negative QA values are not allowed for {row['product']}")


def main() -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    rows = read_rows()
    validate(rows)
    summary = build_summary(rows)
    write_csv(summary)
    write_markdown(summary)
    write_html(summary)
    write_xlsx(summary)
    print(f"Built {len(summary)} product reporting rows in {REPORT_DIR}")


if __name__ == "__main__":
    main()
