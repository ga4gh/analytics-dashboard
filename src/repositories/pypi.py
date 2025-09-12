from models.pypi import (
    ReleasesByYearResponse,
    ReleasesByYearItem,
    PackageVersions,
    SourceCoverageItem,
    SourcesCoverageResponse
)

from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder
from typing import Optional, List


class Pypi:
    def __init__(self, db: DatabaseConnection, sql_builder: SQLBuilder) -> None:
        self.db = db
        self.sql_builder = sql_builder

    def get_total_packages(self) -> int:
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(DISTINCT project_name) FROM pypi;")
            return cur.fetchone()[0]
        
    def get_package_versions(self) -> list[PackageVersions]:
        query = """
            SELECT pp.project_name AS package_name,
                   COUNT(pv.package_version) AS versions
            FROM pypi_versions pv
            JOIN pypi pp ON pp.id = pv.id
            GROUP BY pp.project_name
            ORDER BY pp.project_name;
        """
        results: list[PackageVersions] = []
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                for package_name, versions in rows:
                    results.append(PackageVersions(package_name=package_name, versions=versions))
        return results
    
    def get_releases_over_years(self) -> ReleasesByYearResponse:
        query = """
            SELECT EXTRACT(YEAR FROM release_date)::INT AS year,
                   COUNT(*) AS releases
            FROM pypi_versions
            GROUP BY year
            ORDER BY year;
        """
        items: list[ReleasesByYearItem] = []
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                for (year, releases) in rows:
                    # some rows might have None year if release_date is null — optionally filter
                    if year is not None:
                        items.append(ReleasesByYearItem(year=year, releases=releases))

        return ReleasesByYearResponse(releases_over_years=items)
    
    def get_sources_coverage(self) -> SourcesCoverageResponse:
        '''modify query to include other tables'''
        query = """
            SELECT 
                r.source,
                COUNT(*) AS total_records,
                COUNT(p.id) FILTER (WHERE p.record_id IS NOT NULL) AS covered_records,
                ROUND(
                  100.0 * COUNT(p.id) FILTER (WHERE p.record_id IS NOT NULL) / NULLIF(COUNT(*), 0), 2
                ) AS coverage_percent
            FROM records r
            LEFT JOIN pypi p ON (r.id = p.record_id AND r.source = 'PyPi')
            -- LEFT JOIN github g ON (r.id = g.record_id AND r.source = 'Github')
            -- LEFT JOIN pubmed m ON (r.id = m.record_id AND r.source = 'PubMed')
            GROUP BY r.source
            ORDER BY r.source;
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                items: List[SourceCoverageItem] = []
                for (source, total, covered, percent) in rows:
                    # sometimes covered or percent may be None, handle
                    items.append(SourceCoverageItem(
                        source=source,
                        total_records=total or 0,
                        covered_records=covered or 0,
                        coverage_percent=float(percent or 0.0)
                    ))
        response = SourcesCoverageResponse(coverages=items)
        print(response)
        return SourcesCoverageResponse(coverages=items)

            
