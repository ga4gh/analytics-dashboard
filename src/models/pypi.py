from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Pypi(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_id: int
    project_name: str
    description: str
    download_history: dict | None
    package_url: str
    project_url: str
    release_url: str
    github_url: str | None
    author_name: str | None
    author_email: str | None
    package_version: str
    is_latest: bool
    category: str
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    deleted_by: str | None
    deleted_at: datetime | None
    version: int

class PypiVersion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    python_version: str | None
    package_version: str
    release_date: datetime | None
    download_url: str
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    deleted_by: str | None
    deleted_at: datetime | None
    version: int

class TotalPackagesResponse(BaseModel):
    total_packages: int

class PackageVersions(BaseModel):
    package_name: str
    versions: int

class ReleasesByYearItem(BaseModel):
    year: int
    releases: int

class ReleasesByYearResponse(BaseModel):
    releases_over_years: list[ReleasesByYearItem]

class SourceCoverageItem(BaseModel):
    source: str
    total_records: int
    covered_records: int
    coverage_percent: float

class SourcesCoverageResponse(BaseModel):
    coverages: list[SourceCoverageItem]

class PackageRepoRatioResponse(BaseModel):
    package_repo_ratio_percent: float

class PypiDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_name: str
    description: str | None
    package_url: str
    release_url: str
    github_url: str | None
    author_name: str | None
    author_email: str | None
    category: str
    versions: list[PackageVersions]
