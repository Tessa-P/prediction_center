import pandas as pd

def get_UN_headers(dataframe: pd.DataFrame, header_row: int = 15, series_row: int = 16):
    """
    dataframe should be the specific sheet you want to look at, parsed as a dataframe object.  It must be parsed to at least the rows containing the headers
    """

    headers = dataframe.iloc[header_row].tolist()
    series = dataframe.iloc[series_row].tolist()

    header_list = []
    for head, ser in zip(headers, series):
        if pd.notna(ser):
            header_list.append(str(int(ser)) if isinstance(ser, float) else str(ser))
        else:
            header_list.append(str(head))
    return header_list

def read_un_sheet(file: str, sheetName: str) -> pd.DataFrame:
    """
    takes in a file and a worksheet and produces a labeled dataframe
    """
    df = pd.read_excel(file, sheet_name=sheetName, header=None, nrows=17)
    headers = get_UN_headers(df)
    data = pd.read_excel(file, sheet_name=sheetName, header=None, skiprows=17)
    data.columns = headers
    return data