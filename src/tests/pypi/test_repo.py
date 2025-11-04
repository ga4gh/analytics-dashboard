import pytest
from unittest.mock import MagicMock
from src.repositories.pypi import Pypi as PypiRepo
from src.models.pypi import (
    PackageVersions,
    ReleasesByYearResponse,
    ReleasesByYearItem,
    SourcesCoverageResponse,
    SourceCoverageItem,
    PypiDetails,
)

# -------------------------------
# Fixtures
# -------------------------------

@pytest.fixture
def mock_db():
    db = MagicMock()
    conn = MagicMock()
    cur = MagicMock()

    # db.get_connection() -> conn
    db.get_connection.return_value.__enter__.return_value = conn
    # conn.cursor() -> cur
    conn.cursor.return_value.__enter__.return_value = cur

    return db, conn, cur


@pytest.fixture
def mock_sqlbuilder():
    """Mock SQLBuilder."""
    return MagicMock()


@pytest.fixture
def repo(mock_db, mock_sqlbuilder):
    db, _, _ = mock_db
    return PypiRepo(db, mock_sqlbuilder)


# -------------------------------
# Tests
# -------------------------------

def test_get_total_packages(repo, mock_db):
    db, conn, cur = mock_db
    cur.fetchone.return_value = 82

    result = repo.get_total_packages()

    cur.execute.assert_called_once_with("SELECT COUNT(DISTINCT project_name) FROM pypi;")
    assert isinstance(result, int)
    assert result == 82


def test_get_package_versions(repo, mock_db):
    db, conn, cur = mock_db
    cur.fetchall.return_value = [("ga4gh", 9), ("ga4gh-cli", 3)]

    result = repo.get_package_versions()

    cur.execute.assert_called_once()
    assert isinstance(result, list)
    assert all(isinstance(p, PackageVersions) for p in result)
    assert result[0].package_name == "ga4gh"
    assert result[0].versions == 9
    assert result[1].package_name == "ga4gh-cli"
    assert result[1].versions == 3


def test_get_releases_over_years(repo, mock_db):
    db, conn, cur = mock_db
    cur.fetchall.return_value = [(2013, 1), (2014, 6), (2015, 143), (2016, 172), (2017, 101), (2018, 100), (2019, 88), (2020, 110)]

    result = repo.get_releases_over_years()

    cur.execute.assert_called_once()
    assert isinstance(result, ReleasesByYearResponse)
    assert len(result.releases_over_years) == 8
    assert result.releases_over_years[0].year == 2013
    assert result.releases_over_years[0].releases == 1
    assert result.releases_over_years[4].year == 2017
    assert result.releases_over_years[4].releases == 101
    assert result.releases_over_years[7].year == 2020
    assert result.releases_over_years[7].releases == 110
