from datetime import date
from typing import Annotated, Literal, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

from .errors import RequestError, validation_details

Status = Literal["open", "in_progress", "done"]
SortField = Literal["created", "updated", "due", "priority", "title"]
Order = Literal["asc", "desc"]

STATUSES = get_args(Status)
SORT_FIELDS = get_args(SortField)
ORDERS = get_args(Order)
PRIORITY_MIN, PRIORITY_MAX = 1, 3

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Notes = Annotated[str, Field(max_length=2000)]
Priority = Annotated[int, Field(ge=PRIORITY_MIN, le=PRIORITY_MAX)]


class TodoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    notes: Notes = ""
    status: Status = "open"
    priority: Priority = 2
    due_date: date | None = None


class TodoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title = Field(default=None)
    notes: Notes = Field(default=None)
    status: Status = Field(default=None)
    priority: Priority = Field(default=None)
    due_date: date | None = None

    @model_validator(mode="after")
    def require_a_change(self):
        if not self.model_fields_set:
            raise ValueError("provide at least one field to update")
        return self


class ListParams(BaseModel):
    status: Status | None = None
    priority: Priority | None = None
    q: str | None = Field(default=None, max_length=100)
    due_from: date | None = None
    due_to: date | None = None
    sort: SortField = "created"
    order: Order = "desc"
    limit: int | None = None
    offset: int = Field(default=0, ge=0)


def parse_list_params(args, settings):
    raw = {key: value for key, value in args.items() if value != ""}
    try:
        params = ListParams.model_validate(raw)
    except ValidationError as error:
        raise RequestError(validation_details(error))

    limit = settings.default_limit if params.limit is None else params.limit
    if not 1 <= limit <= settings.max_limit:
        raise RequestError(
            [
                {
                    "field": "limit",
                    "message": f"must be between 1 and {settings.max_limit}",
                }
            ]
        )
    return params.model_copy(update={"limit": limit})
