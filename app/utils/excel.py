from io import BytesIO

import openpyxl


def build_xlsx(headers: list, rows: list, sheet_title: str = "Sheet1") -> BytesIO:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = sheet_title
    sheet.append(headers)
    for row in rows:
        sheet.append(list(row))
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream
