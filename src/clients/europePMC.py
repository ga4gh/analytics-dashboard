from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import pandas as pd
from pathlib import Path
import os
import xmltodict


class EuropePMC:
    def __init__(self) -> None:
        self.base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
        self.token = ""

    def create_tables(self, keyword):
        articles = []
        authors = []
        articles_authors = []
        affiliations = []
        temp_affiliations = []
        citations = []
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

            citations = self.create_citation(article.get("id"), citations)

            id += 1
            author_order = 1
            for author in (article.get("authorList").get("author")):
                
                authors = self.create_author(author, authors)

                articles_authors =self.create_article_author(article, author, articles_authors, author_order)
                author_order +=1
                
                for aff in (author.get("authorAffiliationDetailsList") or {}).get("authorAffiliation", []) or []:
                    org_name = aff.get("affiliation") if isinstance(aff, dict) else aff
                    if org_name not in temp_affiliations:
                        affiliations = self.create_affiliation(aff, affiliations)


        articles_df = pd.DataFrame(articles)
        authors_df = pd.DataFrame(authors)
        articles_authors_df = pd.DataFrame(articles_authors)
        affiliations_df = pd.DataFrame(affiliations)
        citations_df = pd.DataFrame(citations)

        return articles_df, authors_df, articles_authors_df, affiliations_df, citations_df

    def create_author(self, author_data, authors: list):
        author = {
            "id": "",
            "fullname": author_data.get("fullName"),
            "firstname": author_data.get("firstName"),
            "lastname": author_data.get("lastName"),
            "initials": author_data.get("initials"),
            "orcid": (author_data.get("authorId") or {}).get("value"),
        }
        authors.append(author)
        return authors

    def create_article_author(self, article_data, author_data, articles_authors: list, author_order):
        articles_authors_data = {
            "id": "",
            "article_id": article_data.get("id") or article_data.get("pmid"),
            "author_id": "",
            "author_order": author_order 
        }
        articles_authors.append(articles_authors_data)
        return articles_authors

    def create_affiliation(self, affiliation_data, affiliations: list):
        org_name = affiliation_data.get("affiliation") if isinstance(affiliation_data, dict) else affiliation_data
        affiliations_data = {
            "id": "",
            "author_id": "",
            "org_name": org_name
        }
        affiliations.append(affiliations_data)
        return affiliations

    def create_grant(self, article_data, grant_data, grants: list):
        grants_data = {
            "id": "",
            "article_id": article_data.get("id") or article_data.get("pmid"),
            "grant_id": grant_data.get("grantId") or grant_data.get("grant_id"),
            "agency": grant_data.get("agency"),
        }
        grants.append(grants_data)
        return grants

    def create_fulltext(self, article_data, fulltext_data, fulltexts: list):

        fulltext = {
            "id": "",
            "article_id": article_data.get("id") or article_data.get("pmid"),
            "availability": fulltext_data.get("availability"),
            "availability_code": fulltext_data.get("availabilityCode") or fulltext_data.get("availability_code"),
            "document_style": fulltext_data.get("documentStyle") or fulltext_data.get("document_style"),
            "site": fulltext_data.get("site"),
            "url": fulltext_data.get("url"),
        }
        fulltexts.append(fulltext)
        return fulltexts

    def create_citation(self, pmid, citations: list):
        citation_data = self.get_json(self.base_url, self.get_citations_endpoint(pmid))

        citation = {
            "id": "",
            "article_id": pmid,
            "citation_id": citation_data.get("citationId") or citation_data.get("citation_id"),
            "source": citation_data.get("source"),
            "citation_type": citation_data.get("citationType") or citation_data.get("citation_type"),
            "title": citation_data.get("title"),
            "authors": citation_data.get("authors"),
            "pub_year": citation_data.get("pubYear") or citation_data.get("pub_year"),
            "citation_count": citation_data.get("citationCount") or citation_data.get("citation_count"),
        }
        citations.append(citation)
        return citations

    def create_reference(self, article_data, reference_data, references: list):
        reference = {
            "id": "",
            "article_id": article_data.get("id") or article_data.get("pmid"),
            "reference_id": reference_data.get("referenceId") or reference_data.get("reference_id") or reference_data.get("referenceId"),
            "source": reference_data.get("source"),
            "citation_type": reference_data.get("citationType") or reference_data.get("citation_type"),
            "title": reference_data.get("title"),
            "authors": reference_data.get("authors"),
            "pub_year": reference_data.get("pubYear") or reference_data.get("pub_year"),
            "issn": reference_data.get("ISSN") or reference_data.get("issn"),
            "essn": reference_data.get("ESSN") or reference_data.get("essn"),
            "cited_order": reference_data.get("citedOrder") or reference_data.get("cited_order"),
            "match": bool(reference_data.get("match")) if reference_data.get("match") is not None else None,
        }
        references.append(reference)
        return references

    def get_articles(self, keyword):
        json_response = self.get_json(self.base_url, self.get_articles_endpoint(keyword))        
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
            try:
                data = resp.json()
            except ValueError:
                data = xmltodict.parse(resp.text)

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
current_directory = os.getcwd()
pmc.write_df_to_csv(tables[0], current_directory + "/test_articles.csv")
pmc.write_df_to_csv(tables[1], current_directory + "/test_authors.csv")
pmc.write_df_to_csv(tables[2], current_directory + "/test_articles_authors.csv")
pmc.write_df_to_csv(tables[3], current_directory + "/test_affiliations.csv")
pmc.write_df_to_csv(tables[4], current_directory + "/test_citations.csv")