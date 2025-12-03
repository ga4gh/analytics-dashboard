from src.services.pypi import Pypi as PypiService
from src.models.pypi import (
    PackageVersions,
    ReleasesByYearResponse,
    SourcesCoverageResponse,
    PypiDetails,
)

def test_get_package_versions(mock_repo, mock_service):
    mock_repo.get_package_versions.return_value = [
        PackageVersions(package_name="ga4gh", versions=9)
    ]

    result = mock_service.get_package_versions()

    mock_repo.get_package_versions.assert_called_once()
    assert isinstance(result, list)
    assert isinstance(result[0], PackageVersions)
    assert result[0].package_name == "ga4gh"


def test_get_releases_over_years(mock_repo, mock_service):
    mock_repo.get_releases_over_years.return_value = ReleasesByYearResponse(releases_over_years=[])

    result = mock_service.get_releases_over_years()

    mock_repo.get_releases_over_years.assert_called_once()
    assert isinstance(result, ReleasesByYearResponse)
    assert hasattr(result, "releases_over_years")


def test_get_sources_coverage(mock_repo, mock_service):
    mock_repo.get_sources_coverage.return_value = SourcesCoverageResponse(coverages=[])

    result = mock_service.get_sources_coverage()

    mock_repo.get_sources_coverage.assert_called_once()
    assert isinstance(result, SourcesCoverageResponse)
    assert hasattr(result, "coverages")


def test_get_project_details(mock_repo, mock_service):
    mock_repo.get_project_details.return_value = [
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

    result = mock_service.get_project_details()

    mock_repo.get_project_details.assert_called_once()
    assert isinstance(result, list)
    assert isinstance(result[0], PypiDetails)
    assert result[0].project_name == "ga4gh"
