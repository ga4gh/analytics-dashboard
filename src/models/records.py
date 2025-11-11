from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Record(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_type: str
    source: str
    status: str
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    deleted_by: str | None
    deleted_at: datetime | None
    version: int
