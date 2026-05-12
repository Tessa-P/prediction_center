import pandas as pd

from sqlmodel import Session, select
from app.core.db import engine
from app.models import Datatype, Age, Gender, Region

from utils import get_UN_headers, read_un_sheet

# assumes prediction_center/backend as root
FILE = "../../WPP2000/WPP2000_EXCEL_FILES/DB02_Stock_Indicators/WPP2000_DB2_F1_TOTAL_POPULATION_BOTH_SEXES.xls"


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
        df["datatype"] = "Population"
        df["age_group"] = "None"
        df["gender"] = "Both"
        df["scenario"] = sheet

        dfs.append(df)

    dfs_combined = pd.concat(dfs, ignore_index=True)

    # delete columns I don't care about
    dfs_combined = dfs_combined.drop(["Index", "Notes"], axis=1)

    # check for missing data with
    # missing = full_data.isnull().values.any()
    # print(missing)

    return dfs_combined


def get_series_ids(series: pd.Series):
    """
    takes as input a single dataseries, outputs the relevant FKs to the datatype, age, gender, and region tables (in that order)
    """
    # generate series info
    # determine what the series should be across datatype (ex. population), age group, gender, region
    # datatype: column "datatype"
    # age: column "age_group"
    # gender: column "gender"
    # region: column "iso_num"

    metadata = series.loc[["datatype", "age_group", "gender", "iso_num"]]

    with Session(engine) as session:
        datatype_table = {
            d.datatype_description: d.id for d in session.exec(select(Datatype)).all()
        }
        datatype_id = datatype_table.get(metadata["datatype"])
        if datatype_id is None:
            raise ValueError(f"datatype '{metadata["datatype"]}' not found")

        age_table = {a.age_group: a.id for a in session.exec(select(Age)).all()}
        age_id = age_table.get(metadata["age_group"])
        if age_id is None:
            raise ValueError(f"age group '{metadata["age_group"]}' not found")

        gender_table = {
            g.gender_group: g.id for g in session.exec(select(Gender)).all()
        }
        gender_id = gender_table.get(metadata["gender"])
        if gender_id is None:
            raise ValueError(f"gender '{metadata["gender"]}' not found")

        # requires having all regions pre-loaded
        region_table = {r.iso_num: r.id for r in session.exec(select(Region)).all()}
        region_id = region_table.get(metadata["iso_num"])
        if region_id is None:
            raise ValueError(
                f"region num '{metadata["iso_num"]}' ('{series.loc["region_name"]}') not found"
            )

        return [datatype_id, age_id, gender_id, region_id]


full_data = get_dataframe_from_file(FILE)
# print(full_data)
for _, row in full_data.iterrows():
    ids = get_series_ids(row)
    


# take data and push it to database
