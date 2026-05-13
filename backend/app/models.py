from datetime import datetime, timezone

from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class Source(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str


class Age(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    age_group: str


class Gender(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    gender_group: str


class Region(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    region_name: str
    region_short: str | None = Field(default=None)
    parent_id: int | None = Field(default=None, foreign_key="region.id")
    iso2: str | None = Field(default=None)
    iso3: str | None = Field(default=None)
    iso_num: int | None = Field(default=None, unique=True)


class Datatype(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    datatype_description: str


class Scenario(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    scenario_description: str


class Report(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(default=None, foreign_key="source.id")
    year_published: int
    title: str


class Context(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("datatype_id", "age_id", "gender_id", "region_id"),
    )
    id: int | None = Field(default=None, primary_key=True)
    datatype_id: int = Field(default=None, foreign_key="datatype.id")
    age_id: int = Field(default=None, foreign_key="age.id")
    gender_id: int = Field(default=None, foreign_key="gender.id")
    region_id: int = Field(default=None, foreign_key="region.id")


class Datapoint(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("report_id", "context_id", "scenario_id", "year_analyzed"),
    )

    id: int | None = Field(default=None, primary_key=True)
    input_at: datetime = Field(default_factory=get_datetime_utc)
    report_id: int = Field(default=None, foreign_key="report.id")
    context_id: int = Field(default=None, foreign_key="context.id")
    scenario_id: int = Field(default=None, foreign_key="scenario.id")
    year_analyzed: int
    value: float
