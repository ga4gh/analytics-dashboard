from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import pandas as pd
from pathlib import Path


class EuropePMC:
    def __init__(self) -> None:
        self.base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
        self.token = ""

    def create_tables(self, keyword):
        articles = []
        authors = []
        articles_authors = []
        affiliations = []

        json_response = self.get_articles(keyword)
        results = json_response.get("resultList", {}).get("result", []) or []

        id = 10000
        for article in results:
            data = {
                "id": id,
                "record_id": id,
                "Source": article.get("source"),
                "Pm_id": article.get("id") or article.get("pmid"),
                "Pmc_id": article.get("pmcid"),
                "Full_text_id": "",
                "Doi": article.get("doi"),
                "Title": article.get("title"),
                "Pub_year": article.get("pubYear"),
                "Abstract_text": article.get("abstractText"),
                "Affiliation": article.get("affiliation"),
                "Publicication_status": article.get("publicationStatus"),
                "Language": article.get("language"),
                "Pub_type": (article.get("pubTypeList") or {}).get("pubType"),
                "Is_open_access": bool(article.get("isOpenAccess")),
                "inEPMC": bool(article.get("inEPMC")),
                "inPMC": bool(article.get("inPMC")),
                "hasPDF": bool(article.get("hasPDF")),
                "hasBook": bool(article.get("hasBook")),
                "hasSuppl": bool(article.get("hasSuppl")),
                "Cited_by_count": article.get("citedByCount"),
                "Has_references": bool(article.get("hasReferences")),
                "Dateofcreation": article.get("dateOfCreation"),
                "firstIndexdate": article.get("firstIndexDate"),
                "Fulltextreceivedate": article.get("fullTextReceivedDate"),
                "Revisiondate": article.get("dateOfRevision"),
                "Epubdate": article.get("electronicPublicationDate"),
                "Firstpublicationdate": article.get("firstPublicationDate"),
            }
            articles.append(data)
            id += 1
            author_order = 1
            for author in (article.get("authorList").get("author")):
                author_data = {
                    "id": "",
                    "fullname": author.get("fullName"),
                    "firstname": author.get("firstName"),
                    "lastname": author.get("lastName"),
                    "initials": author.get("initials"),
                    "orcid": (author.get("authorId") or {}).get("value"),
                }
                authors.append(author_data)

                article_authors_data = {
                    "id": "",
                    "article_id": article.get("id") or article.get("pmid"),
                    "author_id": "",
                    "author_order": author_order 
                }
                articles_authors.append(article_authors_data)
                author_order +=1
                
                for aff in (author.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []) or []:
                    org_name = aff.get("affiliation") if isinstance(aff, dict) else aff
                    affiliations_data = {
                        "id": "",
                        "author_id": "",
                        "org_name": org_name
                    }
                    affiliations.append(affiliations_data)


        articles_df = pd.DataFrame(articles)
        authors_df = pd.DataFrame(authors)
        articles_authors_df = pd.DataFrame(articles_authors)
        affiliations_df = pd.DataFrame(affiliations)

        return articles_df, authors_df, articles_authors_df, affiliations_df



    def get_articles(self, keyword):
        json_response = self.get_json(self.base_url, self.get_articles_endpoint(keyword))        
        return json_response

    def get_citations(self, id):
        json_response = self.get_json(self.base_url, self.get_citations_endpoint(id))
        return json_response

    def get_references(self, id):
        json_response = self.get_json(self.base_url, self.get_references_endpoint(id))
        return json_response

    def get_full_text(self, pmcid):
        json_response = self.get_json(self.base_url, self.get_full_text_endpoint(pmcid))
        return json_response

    def get_articles_endpoint(self, keyword):
        return f"search?query={keyword}&format=json&resultType=core"

    def get_citations_endpoint(self, id):
        return f"MED/{id}/citations"

    def get_references_endpoint(self, id):
        return f"MED/{id}/references"

    def get_full_text_endpoint(self, pmcid):
        return f"{pmcid}/fullTextXML"

    def get_json(self, base_url: str, endpoint: str, token: Optional[str] = None, per_page: int = 100) -> List[Dict[str, Any]]:

        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"

        params = {"per_page": per_page, "page": 1}
        items: List[Dict[str, Any]] = []
        url = base_url + endpoint

        while True:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if not isinstance(data, list):
                return data

            items.extend(data)

            if "next" in resp.links:
                url = resp.links["next"]["url"]
                params = None
            else:
                break

        return items

    def write_df_to_csv(self, df: pd.DataFrame, filename: str) -> Path:

        path = Path(filename)
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(path)
        print(f"Wrote CSV: {path}")
        return path

pmc = EuropePMC()
tables = pmc.create_tables("ga4gh")
pmc.write_df_to_csv(tables[0], "/Users/cchen/Documents/Workspace/analytics-dashboard/src/clients/test_articles.csv")
pmc.write_df_to_csv(tables[1], "/Users/cchen/Documents/Workspace/analytics-dashboard/src/clients/test_authors.csv")
pmc.write_df_to_csv(tables[2], "/Users/cchen/Documents/Workspace/analytics-dashboard/src/clients/test_articles_authors.csv")
pmc.write_df_to_csv(tables[3], "/Users/cchen/Documents/Workspace/analytics-dashboard/src/clients/test_affiliations.csv")
