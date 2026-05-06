from importlib.metadata import metadata
import pandas as pd
from utils import get_UN_headers, read_un_sheet

FILE = "../WPP2000/WPP2000_EXCEL_FILES/DB02_Stock_Indicators/WPP2000_DB2_F1_TOTAL_POPULATION_BOTH_SEXES.xls"
# df = pd.read_excel(FILE, sheet_name="MEDIUM", header=None, nrows=18)


def get_single_sheet():
    sheet = "MEDIUM"
    df = read_un_sheet(FILE, sheet)

    df = df.rename(columns = {
        'Major area, region, country or area': 'region_name',
        'Country code': 'iso_num'
    })

    year_columns = [col for col in df.columns if str(col).isdigit()]
    metadata_columns = [col for col in df.columns if not str(col).isdigit()]
    print(year_columns)
    print(metadata_columns)

    df = df.melt(
        id_vars=metadata_columns, #columns to keep
        value_vars=year_columns, #columns to pivot
        var_name="for_year", #new name of header column
        value_name="value" #new name of value column
    )

    print(df.dtypes)

    # want to cast for_year to int
    df["for_year"] = df["for_year"].astype(int)

    # want to multiply value by 1000, then cast to int
    df["value"] = (df["value"]*1000).astype(int)

    # assigning more metadata
    df["gender"] = "Both"
    df["scenario"] = sheet

    print(df.head(10))
    print(df.dtypes)

# stitching all sheets together

# 1 - pop off notes sheet
all_sheets = pd.ExcelFile(FILE).sheet_names
sheets_to_read = all_sheets[:-1]

dfs = []
for sheet in sheets_to_read:
    df = read_un_sheet(FILE, sheet)
    
    # rename columns
    df = df.rename(columns = {
        'Major area, region, country or area': 'region_name',
        'Country code': 'iso_num'
    })

    # parse year vs metadata headers
    year_columns = [col for col in df.columns if str(col).isdigit()]
    metadata_columns = [col for col in df.columns if not str(col).isdigit()]

    # make tall
    df = df.melt(
        id_vars=metadata_columns, #columns to keep
        value_vars=year_columns, #columns to pivot
        var_name="for_year", #new name of header column
        value_name="value" #new name of value column
    )

    # cast to new types
    df["for_year"] = df["for_year"].astype(int)
    df["value"] = (df["value"]*1000).astype(int)

    # attach metadata
    df["gender"] = "Both"
    df["scenario"] = sheet

    dfs.append(df)

dfs_combined = pd.concat(dfs, ignore_index=True)
print(f"Combined Shape: {dfs_combined.shape}")
print(dfs_combined["gender"].unique())
