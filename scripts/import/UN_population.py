from pathlib import Path
import pandas as pd
import re

from sqlmodel import Session, select
from app.core.db import engine
from app.models import (
    Datatype,
    Age,
    Gender,
    Region,
    Context,
    Datapoint,
    Scenario,
    Report,
)

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
    sheets_to_read = all_sheets[:4]  # only constructs estimates, low, high, medium
    # TODO: other sheets may have different sheets where you don't just want the first 4

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
            var_name="year_analyzed",  # new name of header column
            value_name="value",  # new name of value column
        )

        # cast to new types
        df["year_analyzed"] = df["year_analyzed"].astype(int)
        df["value"] = (df["value"] * 1000).astype(int)

        # attach metadata
        df["datatype"] = "Population"  # TODO: pull from sheet properly
        df["age_group"] = "None"  # TODO: pull from sheet properly
        df["gender"] = "Both"  # TODO: pull from sheet properly
        df["scenario"] = sheet
        # TODO: this data exists in the "variant" col, can pull from that directly (and dont have to deal with the regex nonsense)

        dfs.append(df)

    dfs_combined = pd.concat(dfs, ignore_index=True)

    # delete columns I don't care about
    dfs_combined = dfs_combined.drop(["Index", "Notes"], axis=1)

    # check for missing data with
    # missing = full_data.isnull().values.any()
    # print(missing)

    return dfs_combined


def get_series_ids(
    series: pd.Series, datatype_lookup, age_lookup, gender_lookup, region_lookup
) -> dict[str, int]:
    """
    takes as input a single dataseries, returns a Context object with the correct IDs
    """

    metadata = series.loc[["datatype", "age_group", "gender", "iso_num"]]

    datatype_id = datatype_lookup.get(metadata["datatype"])
    if datatype_id is None:
        raise ValueError(f"datatype '{metadata["datatype"]}' not found")

    age_id = age_lookup.get(metadata["age_group"])
    if age_id is None:
        raise ValueError(f"age group '{metadata["age_group"]}' not found")

    gender_id = gender_lookup.get(metadata["gender"])
    if gender_id is None:
        raise ValueError(f"gender '{metadata["gender"]}' not found")

    # requires having all regions pre-existing in the regions table
    region_id = region_lookup.get(metadata["iso_num"])
    if region_id is None:
        raise ValueError(
            f"region num '{metadata["iso_num"]}' ('{series.loc["region_name"]}') not found"
        )

    new_context = {
        "datatype_id": datatype_id,
        "age_id": age_id,
        "gender_id": gender_id,
        "region_id": region_id,
    }
    return new_context


def build_key(context_dict: dict[str, int]) -> tuple[int, int, int, int]:
    """
    takes in a dictionary of header : id pairs, builds a tuple of the form (datatype_id, age_id, gender_id, region_id)
    """
    return (
        context_dict["datatype_id"],
        context_dict["age_id"],
        context_dict["gender_id"],
        context_dict["region_id"],
    )


def get_scenario(scenario: str, scenario_lookup) -> int:
    scenario_id = None
    for scenario_description in scenario_lookup:
        if re.search(scenario_description, scenario, re.IGNORECASE):
            scenario_id = scenario_lookup.get(scenario_description)
            break
    if scenario_id is None:
        raise ValueError(f"scenario '{scenario}' not found")
    return scenario_id


def get_report_id(file: str) -> int:
    """
    input: a string representing the file location.
    output: the corresponding id in the database
    """
    path = Path(file)
    year_published = int(path.stem[3:7])
    with Session(engine) as session:
        # TODO: assumes only one report per year, should match on other characteristics to guarantee uniqueness
        report = session.exec(select(Report).where(Report.year_published == year_published)).first()
        if report is None:
            raise ValueError(f"report for published year '{year_published}' not found")
    if report.id is None:
        raise ValueError(f"report PK is 'None'")
    return report.id


def populate_datapoints(df: pd.DataFrame, report_id: int):
    """
    takes as input a dataframe, populates the datapoint table with all data in the dataframe
    """
    with Session(engine) as session:
        datatype_lookup = {
            d.datatype_description: d.id for d in session.exec(select(Datatype)).all()
        }
        age_lookup = {a.age_group: a.id for a in session.exec(select(Age)).all()}
        gender_lookup = {
            g.gender_group: g.id for g in session.exec(select(Gender)).all()
        }
        region_lookup = {r.iso_num: r.id for r in session.exec(select(Region)).all()}
        # builds key directly from the context object
        context_lookup = {
            (c.datatype_id, c.age_id, c.gender_id, c.region_id): c.id
            for c in session.exec(select(Context)).all()
        }
        scenario_lookup = {
            s.scenario_description: s.id for s in session.exec(select(Scenario)).all()
        }
        for _, row in df.iterrows():
            context_dict = get_series_ids(
                row, datatype_lookup, age_lookup, gender_lookup, region_lookup
            )
            key = build_key(context_dict)
            context_id = context_lookup.get(key)
            if context_id is None:  # if there is no matching context
                # push new context to the Context table
                context = Context(
                    datatype_id=context_dict["datatype_id"],
                    age_id=context_dict["age_id"],
                    gender_id=context_dict["gender_id"],
                    region_id=context_dict["region_id"],
                )
                session.add(context)
                session.flush()
                session.refresh(context)
                context_id = context.id
                context_lookup[key] = context_id
                if context_id is None:  # check in testing
                    raise ValueError(f"context not populated - key: {key}")

            # context object is now in database, context_id holds the relevant id (also accessible with context.id)
            new_datapoint = Datapoint(
                report_id=report_id,  # TODO: Can handle UN reports, can't do anything else
                context_id=context_id,
                scenario_id=get_scenario(row["scenario"], scenario_lookup),
                year_analyzed=row["year_analyzed"],
                value=row["value"],
            )

            session.add(new_datapoint)
        session.commit()


full_data = get_dataframe_from_file(FILE)
print(full_data)
report_id = get_report_id(FILE)
populate_datapoints(full_data, report_id)
print("success")

# take data and push it to database
