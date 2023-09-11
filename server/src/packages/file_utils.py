from openpyxl import Workbook
import json
from io import BytesIO
from typing import Union
from pathlib import Path
from string import ascii_uppercase

COLUMN_LETTER_SKIP = ['A','B','C','D','E']

def dict_to_xlsx_bytes(data:dict, column_headers:Union[list, set]) -> bytes:
    try:
        ## Setup workbook
        workbook = Workbook()
        sheet = workbook.active
        ucase:list = [ x for x in ascii_uppercase if x not in COLUMN_LETTER_SKIP ]
        ucase.append([ f"A{x}" for x in ascii_uppercase ])

        ## First write column headers using keys from data
        ## Known column headers
        sheet['A1'] = "Request ID"
        sheet['B1'] = "Date Taken"
        sheet['C1'] = "Employee Name"
        sheet['D1'] = "Vendor"
        sheet['E1'] = "Destination"

        ## Dynamic beer name headers from the query
        col_key_map = {}
        for ind, col_name in enumerate(column_headers):
            col_key_map[col_name] = f"{ucase[ind]}"
            sheet[f"{col_key_map[col_name]}1"] = col_name + "oz"

        ## Set the row values based on the data provided
        row_index = 2
        for submission in data:
            sheet[f'A{row_index}'] = submission['id']
            sheet[f'B{row_index}'] = submission['dateTaken']
            sheet[f'C{row_index}'] = submission['employeeName']
            sheet[f'D{row_index}'] = submission['vendor']
            sheet[f'E{row_index}'] = submission['destination']
            for k, v in submission['beersTaken'].items():
                sheet[f"{col_key_map[k]}{row_index}"] = v['caseEquivalent']
            row_index += 1

        ## Convert the workbook to bytes
        bytes_io = BytesIO()
        workbook.save(bytes_io)
        bytes_value = bytes_io.getvalue()
        return bytes_value
    except Exception as e:
        raise e
    finally:
        if bytes_io:
            bytes_io.close()
        workbook.close()

def dict_to_json_file(data:dict, file_path:Union[Path, str]) -> None:
    file_path = Path(file_path) if isinstance(file_path, str) else file_path
    if file_path.suffix == '' or file_path.suffix != '.json':
        raise ValueError("Invalid or missing file path suffix")
    with open(file_path,'w') as f:
        json.dump(data,f, indent=4)