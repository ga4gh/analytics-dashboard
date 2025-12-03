from src.models.pypi import (
    ReleasesByYearResponse,
    ReleasesByYearItem,
    PackageVersions,
    SourceCoverageItem,
    SourcesCoverageResponse,
    PypiDetails,
    FirstRelease,
    AllPackages,
    PypiVersion,
    Pypi as PyPiModel
)

from .setup import DatabaseConnection
from .sqlbuilder import SQLBuilder
from psycopg.rows import dict_row


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
            LEFT JOIN github g ON (r.id = g.record_id AND r.source = 'Github')
            LEFT JOIN pubmed m ON (r.id = m.record_id AND r.source = 'PubMed')
            GROUP BY r.source
            ORDER BY r.source;
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                items: list[SourceCoverageItem] = []
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
    
    def get_project_details(self) -> list[PypiDetails]:
        """
        Returns a first release of each package
        """
        query = """
        SELECT 
            p.project_name, p.description, p.package_url, p.release_url, p.github_url, p.author_name, 
            p.author_email, p.category, COUNT(pv.package_version) AS version_count
        FROM pypi p
            LEFT JOIN pypi_versions pv ON pv.id = p.id
        GROUP BY
            p.project_name, p.description, p.package_url, p.release_url, p.github_url, p.author_name, p.author_email, p.category
        ORDER BY version_count desc;
        """

        result: list[PypiDetails] = []
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                for (
                    project_name,
                    description,
                    package_url,
                    release_url,
                    github_url,
                    author_name,
                    author_email,
                    category,
                    version_count
                ) in rows:
                    pv = PackageVersions(
                        package_name=project_name,
                        versions=version_count or 0
                    )
                    details = PypiDetails(
                        project_name=project_name,
                        description=description,
                        package_url=package_url,
                        release_url=release_url,
                        github_url=github_url,
                        author_name=author_name,
                        author_email=author_email,
                        category=category,
                        versions=[pv]
                    )
                    result.append(details)
        return result

    def get_first_releases(self) -> list[FirstRelease]:
        query = """
            SELECT 
                DISTINCT ON (pp.id) pp.id AS id, pp.project_name AS pn, pv.package_version AS version, pv.release_date AS rd
            FROM pypi pp
            JOIN pypi_versions pv ON pp.id = pv.id
            ORDER BY pp.id, pv.release_date;
        """
        results: list[FirstRelease] = []
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                for id, pn, version, rd  in rows:
                    results.append(FirstRelease(id=id, project_name=pn, version=version, release_date=rd))
        return results
    
    def get_all_packages(self) -> list[AllPackages]:
        query = """
        SELECT
        p.id    AS pkg_id,
        p.record_id,
        p.project_name,
        p.description,
        p.download_history,
        p.package_url,
        p.project_url,
        p.release_url,
        p.github_url,
        p.author_name,
        p.author_email,
        p.package_version AS pkg_current_version,
        p.is_latest,
        p.category,
        p.created_by AS pkg_created_by,
        p.created_at AS pkg_created_at,
        p.updated_by AS pkg_updated_by,
        p.updated_at AS pkg_updated_at,
        p.deleted_by AS pkg_deleted_by,
        p.deleted_at AS pkg_deleted_at,

        pv.id    AS ver_id,
        pv.python_version,
        pv.package_version AS ver_package_version,
        pv.release_date   AS ver_release_date,
        pv.download_url,
        pv.created_by AS ver_created_by,
        pv.created_at AS ver_created_at,
        pv.updated_by AS ver_updated_by,
        pv.updated_at AS ver_updated_at,
        pv.deleted_by AS ver_deleted_by,
        pv.deleted_at AS ver_deleted_at,
        pv.version AS ver_version_number
        FROM pypi p
        LEFT JOIN pypi_versions pv ON pv.id = p.id;
        """

        results: list[AllPackages] = []
        with self.db.get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query)
                rows = cur.fetchall()
    
        for row in rows:
            pkg = PyPiModel(
                id=row["pkg_id"],
                record_id=row["record_id"],
                project_name=row["project_name"],
                description=row["description"],
                download_history=row["download_history"],
                package_url=row["package_url"],
                project_url=row["project_url"],
                release_url=row["release_url"],
                github_url=row["github_url"],
                author_name=row["author_name"],
                author_email=row["author_email"],
                package_version=row["pkg_current_version"],
                is_latest=row["is_latest"],
                category=row["category"],
                created_by=row["pkg_created_by"],
                created_at=row["pkg_created_at"],
                updated_by=row["pkg_updated_by"],
                updated_at=row["pkg_updated_at"],
                deleted_by=row["pkg_deleted_by"],
                deleted_at=row["pkg_deleted_at"],
            )
            version = PypiVersion(
                id=row["ver_id"],
                python_version=row["python_version"],
                package_version=row["ver_package_version"],
                release_date=row["ver_release_date"],
                download_url=row["download_url"],
                created_by=row["ver_created_by"],
                created_at=row["ver_created_at"],
                updated_by=row["ver_updated_by"],
                updated_at=row["ver_updated_at"],
                deleted_by=row["ver_deleted_by"],
                deleted_at=row["ver_deleted_at"],
                version=row["ver_version_number"]
            )
            results.append(AllPackages(package=pkg, version=version))

        return results
            
