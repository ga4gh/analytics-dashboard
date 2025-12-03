from fastapi import APIRouter, HTTPException, Response
from src.services.pypi import Pypi as PypiService
from src.models.pypi import (
    TotalPackagesResponse,
    ReleasesByYearResponse,
    PackageRepoRatioResponse,
    PackageVersions,
    SourcesCoverageResponse,
    PypiDetails,
    FirstRelease,
    AllPackages
)

class Pypi:
    def __init__(self, pypi_service: PypiService):
        self.router = APIRouter()
        self.pypi_service = pypi_service
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get("/pypi/total-packages", response_model=TotalPackagesResponse)
        async def get_total_packages():
            packages_count: int = self.pypi_service.get_total_packages()
            return TotalPackagesResponse(total_packages=packages_count)
        
        @self.router.get("/pypi/package-versions", response_model=list[PackageVersions])
        async def get_package_versions():
            return self.pypi_service.get_package_versions()
        
        @self.router.get("/pypi/releases-over-years", response_model=ReleasesByYearResponse)
        async def get_releases_over_years():
            return self.pypi_service.get_releases_over_years()
        
        @self.router.get("/pypi/all-sources-coverage", response_model=SourcesCoverageResponse)
        async def get_sources_coverage() -> SourcesCoverageResponse:
            return self.pypi_service.get_sources_coverage()
        
        @self.router.get("/pypi/project-details", response_model=list[PypiDetails])
        async def get_project_details():
            return self.pypi_service.get_project_details()
        
        @self.router.get("/pypi/first-releases", response_model=list[FirstRelease])
        async def get_first_releases():
            return self.pypi_service.get_first_releases()
        
        @self.router.get("/pypi/all-packages", response_model=list[AllPackages])
        async def get_all_packages():
            return self.pypi_service.get_all_packages()