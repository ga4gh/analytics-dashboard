from src.models.pypi import (
    ReleasesByYearResponse,
    PackageRepoRatioResponse,
    PackageVersions,
    SourcesCoverageResponse,
    PypiDetails
)
from src.repositories.pypi import Pypi as PypiRepo

class Pypi:
    def __init__(self, repo: PypiRepo) -> None:
        self.pypi_repo = repo
        
    def get_total_packages(self) -> int:
        return self.pypi_repo.get_total_packages()
    
    def get_package_versions(self) -> PackageVersions:
        return self.pypi_repo.get_package_versions()

    def get_releases_over_years(self) -> ReleasesByYearResponse:
        return self.pypi_repo.get_releases_over_years()

    def get_sources_coverage(self) -> SourcesCoverageResponse:
        return self.pypi_repo.get_sources_coverage()
    
    def get_project_details(self) -> list[PypiDetails]:
        return self.pypi_repo.get_project_details()
