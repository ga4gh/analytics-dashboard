import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.routers.pypi import Pypi as PypiRouter
from src.services.pypi import Pypi as PypiService
from src.models.pypi import (
    TotalPackagesResponse,
    PackageVersions,
    ReleasesByYearResponse,
    SourcesCoverageResponse,
    PypiDetails,
)


@pytest.fixture
def mock_service():
    return MagicMock(spec=PypiService)


@pytest.fixture
def client(mock_service):
    """Create a FastAPI test client with the Pypi router mounted."""
    from fastapi import FastAPI

    app = FastAPI()
    router = PypiRouter(mock_service)
    app.include_router(router.router)
    return TestClient(app)


def test_get_total_packages(client, mock_service):
    mock_service.get_total_packages.return_value = 82

    response = client.get("/pypi/total-packages")

    assert response.status_code == 200
    data = response.json()
    assert data == {"total_packages": 82}
    mock_service.get_total_packages.assert_called_once()


def test_get_package_versions(client, mock_service):
    mock_service.get_package_versions.return_value = [
        PackageVersions(package_name="ga4gh", versions=9)
    ]

    response = client.get("/pypi/package-versions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["package_name"] == "ga4gh"
    assert data[0]["versions"] == 9
    mock_service.get_package_versions.assert_called_once()


def test_get_releases_over_years(client, mock_service):
    mock_service.get_releases_over_years.return_value = ReleasesByYearResponse(
        releases_over_years=[]
    )

    response = client.get("/pypi/releases-over-years")

    assert response.status_code == 200
    data = response.json()
    assert "releases_over_years" in data
    mock_service.get_releases_over_years.assert_called_once()


def test_get_sources_coverage(client, mock_service):
    mock_service.get_sources_coverage.return_value = SourcesCoverageResponse(coverages=[])

    response = client.get("/pypi/all-sources-coverage")

    assert response.status_code == 200
    data = response.json()
    assert "coverages" in data
    mock_service.get_sources_coverage.assert_called_once()


def test_get_project_details(client, mock_service):
    mock_service.get_project_details.return_value = [
        PypiDetails(
            project_name="ga4gh",
            description="A reference implementation of the GA4GH API",
            package_url="https://pypi.org/project/ga4gh/",
            release_url="https://pypi.org/project/ga4gh/",
            github_url="https://github.com/ga4gh/server",
            author_name="Global Alliance for Genomics and Health",
            author_email="theglobalalliance@genomicsandhealth.org",
            category="GA4GH Standard",
            versions=[PackageVersions(package_name="ga4gh", versions=9)],
        )
    ]

    response = client.get("/pypi/project-details")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["project_name"] == "ga4gh"
    assert "versions" in data[0]
    mock_service.get_project_details.assert_called_once()
