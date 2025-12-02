from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class Pypi(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    record_id: int
    project_name: str
    description:  Optional[str] = None
    download_history: Optional[dict]
    package_url: str
    project_url: str
    release_url: str
    github_url: Optional[str]
    author_name: Optional[str]
    author_email: Optional[str]
    package_version: str
    is_latest: bool
    category: str
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    deleted_by: Optional[str]
    deleted_at: Optional[datetime]
    version: Optional[int] = None
        
class PypiVersion(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    python_version: Optional[str]
    package_version: str
    release_date: Optional[datetime]
    download_url: str
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime
    deleted_by: Optional[str]
    deleted_at: Optional[datetime]
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
    description: Optional[str]
    package_url: str
    release_url: str
    github_url: Optional[str]
    author_name: Optional[str]
    author_email: Optional[str]
    category: str
    versions: list[PackageVersions]
    
class AllPackages(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    package: Pypi
    version: PypiVersion
    
class FirstRelease(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_name: str
    version: str
    release_date: datetime
    
