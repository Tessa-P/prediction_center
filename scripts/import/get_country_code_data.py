from app.models import Region
import pandas as pd

from sqlmodel import Session, select
from app.core.db import engine

from utils import get_UN_headers, read_un_sheet

# run from /prediction_center/backend
FILE = "../../WPP2022/EXCEL_FILES/2_Population/WPP2022_POP_F03_1_POPULATION_SELECT_AGE_GROUPS_BOTH_SEXES.xlsx"
def get_list(file: str):
    df = read_un_sheet(file, "Estimates")

    df = df.rename(
        columns={
            "Region, subregion, country or area *": "region_name",
            "Location code": "iso_num",
            "ISO3 Alpha-code": "iso3",
            "ISO2 Alpha-code": "iso2",
        }
    )
    # print(df)
    df = df[["region_name", "iso2", "iso3", "iso_num"]].copy()
    df = df.fillna("")
    df = df.drop_duplicates()
    return df

def generate_dataset(data: pd.DataFrame):
    """
    dataset must already have no duplicates
    """

    with Session(engine) as session:

        for _, p in data.iterrows():
            region = p["region_name"]
            iso2 = p["iso2"]
            iso3 = p["iso3"]
            iso_num = p["iso_num"]

            new_location = Region(region_name=region, iso2=iso2, iso3=iso3, iso_num=iso_num)

            session.add(new_location)
        
        session.commit()



df = get_list(FILE)
generate_dataset(df)

