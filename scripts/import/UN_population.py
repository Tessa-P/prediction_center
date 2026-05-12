from pandas.api.typing.aliases import Axis
import pandas as pd
from utils import get_UN_headers, read_un_sheet

FILE = "../WPP2000/WPP2000_EXCEL_FILES/DB02_Stock_Indicators/WPP2000_DB2_F1_TOTAL_POPULATION_BOTH_SEXES.xls"


def get_dataframe_from_file(file: str) -> pd.DataFrame:
    """
    Pulls all relevant data from a given file.  Takes a file path as input and outputs a combined and labelled dataframe of only the relevant data
    """

    # stitching all sheets together

    # pop off notes sheet
    all_sheets = pd.ExcelFile(file).sheet_names
    sheets_to_read = all_sheets[:-1]

    dfs = []
    for sheet in sheets_to_read:
        df = read_un_sheet(FILE, sheet)

        # rename columns
        df = df.rename(
            columns={
                "Major area, region, country or area": "region_name",
                "Country code": "iso_num",
            }
        )

        # parse year vs metadata headers
        year_columns = [col for col in df.columns if str(col).isdigit()]
        metadata_columns = [col for col in df.columns if not str(col).isdigit()]

        # make tall
        df = df.melt(
            id_vars=metadata_columns,  # columns to keep
            value_vars=year_columns,  # columns to pivot
            var_name="for_year",  # new name of header column
            value_name="value",  # new name of value column
        )

        # cast to new types
        df["for_year"] = df["for_year"].astype(int)
        df["value"] = (df["value"] * 1000).astype(int)

        # attach metadata
        df["gender"] = "Both"
        df["scenario"] = sheet

        dfs.append(df)

    dfs_combined = pd.concat(dfs, ignore_index=True)

    # delete notes I don't care about
    dfs_combined = dfs_combined.drop(["Index", "Notes"], axis=1)

    return dfs_combined


full_data = get_dataframe_from_file(FILE)
print(full_data)

# take data and push it to database
