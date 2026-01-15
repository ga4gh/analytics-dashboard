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
        self.grants_url = "https://www.ebi.ac.uk/europepmc/GristAPI/rest/"
        self.token = ""

    def create_tables(self, keyword):
        articles = []
        authors = []
        articles_authors = []
        affiliations = []
        temp_affiliations = []
        citations = []
        references = []
        grants = []
        fulltext = []

        json_response = self.get_articles(keyword)
        results = json_response.get("resultList", {}).get("result", []) or []

        grants = self.create_grant_api(keyword, grants)
        

        id = 10000
        for article in results:
            
            articles = self.create_article(article, articles, id)
            grants = self.create_grant(article, grants)
            citations = self.create_citation(article.get("id"), citations)
            references = self.create_reference(article, references)
            fulltext = self.create_fulltext(article, fulltext)

            id += 1
            author_order = 1
            for author in (article.get("authorList") or {}).get("author") or []:
                
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
        references_df = pd.DataFrame(references)
        grants_df = pd.DataFrame(grants)
        fulltext_df = pd.DataFrame(fulltext)

        return articles_df, authors_df, articles_authors_df, affiliations_df, citations_df, references_df, grants_df, fulltext_df

    def create_article(self, article_data, articles: list, id):
        data = {
                "id": id,
                "record_id": id,
                "Source": article_data.get("source"),
                "Pm_id": article_data.get("id"),
                "Pmc_id": article_data.get("pmcid"),
                "Full_text_id": "",
                "Doi": article_data.get("doi"),
                "Title": article_data.get("title"),
                "Pub_year": article_data.get("pubYear"),
                "Abstract_text": article_data.get("abstractText"),
                "Affiliation": article_data.get("affiliation"),
                "Publicication_status": article_data.get("publicationStatus"),
                "Language": article_data.get("language"),
                "Pub_type": (article_data.get("pubTypeList") or {}).get("pubType"),
                "Is_open_access": bool(article_data.get("isOpenAccess")),
                "inEPMC": bool(article_data.get("inEPMC")),
                "inPMC": bool(article_data.get("inPMC")),
                "hasPDF": bool(article_data.get("hasPDF")),
                "hasBook": bool(article_data.get("hasBook")),
                "hasSuppl": bool(article_data.get("hasSuppl")),
                "Cited_by_count": article_data.get("citedByCount"),
                "Has_references": bool(article_data.get("hasReferences")),
                "Dateofcreation": article_data.get("dateOfCreation"),
                "firstIndexdate": article_data.get("firstIndexDate"),
                "Fulltextreceivedate": article_data.get("fullTextReceivedDate"),
                "Revisiondate": article_data.get("dateOfRevision"),
                "Epubdate": article_data.get("electronicPublicationDate"),
                "Firstpublicationdate": article_data.get("firstPublicationDate"),
            }
        articles.append(data)
        return articles

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

    def create_grant(self, article_data, grants: list):
        
        for grant_data in (article_data.get("grantsList") or {}).get("grant") or []:
            grants_data = {
                "id": "",
                "article_id": article_data.get("id") or article_data.get("pmid"),
                "grant_id": grant_data.get("grantId") or grant_data.get("grant_id"),
                "agency": grant_data.get("agency"),
                "family_name": "",
                "given_name": "",
                "orcid": "",
                "funder_name": "",
                "grant": "", 
                "doi": "",
                "title": "",
                "start_date": "",
                "end_date": "",
                "institution_name": "",
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
        citation_data = self.get_citations(pmid)

        count = 1
        for cite in (citation_data.get("citationList") or {}).get("citation") or []:
            citation = {
                "id": "",
                "article_id": pmid,
                "citation_id": cite.get("id"),
                "source": cite.get("source"),
                "citation_type": cite.get("citationType") or cite.get("citation_type"),
                "title": cite.get("title"),
                "authors": cite.get("authors"),
                "pub_year": cite.get("pubYear") or cite.get("pub_year"),
                "citation_count": count,
            }
            citations.append(citation)
            count +=1
        return citations

    def create_reference(self, article_data, references: list):

        response = self.get_references(article_data.get("id"))
        reference_data = (response.get("referenceList") or {}).get("reference") or []

        if isinstance(reference_data, dict):
            reference_data = [reference_data]

        for ref in reference_data:
            reference = {
                "id": "",
                "article_id": article_data.get("id"),
                "reference_id": ref.get("id"),
                "source": ref.get("source"),
                "citation_type": ref.get("citationType") or ref.get("citation_type"),
                "title": ref.get("title"),
                "authors": ref.get("authors"),
                "pub_year": ref.get("pubYear") or ref.get("pub_year"),
                "issn": ref.get("ISSN") or ref.get("issn"),
                "essn": ref.get("ESSN") or ref.get("essn"),
                "cited_order": ref.get("citedOrder") or ref.get("cited_order"),
                "match": bool(ref.get("match")) if ref.get("match") is not None else None,
            }
            references.append(reference)
        return references

    def create_grant_api(self, keyword, grants: list):
        response = self.get_grants(keyword)
        
        record_list = (response.get("RecordList") or {}).get("Record") or []

        if isinstance(record_list, dict):
            record_list = [record_list]

        for gr in record_list:
            person = gr.get("Person") or {}
            grant_info = gr.get("Grant") or {}
            institution = gr.get("Institution") or {}
            funder = grant_info.get("Funder") or {}
            amount = grant_info.get("Amount") or {}

            person_aliases = person.get("Alias") or []
            if isinstance(person_aliases, dict):
                person_aliases = [person_aliases]
            
            orcid = ""
            for alias in person_aliases:
                if alias.get("Source") == "ORCID":
                    orcid = alias.get("value")
                    break

            grant = {
                "id": "",
                "record_id": "",
                "grant_id": grant_info.get("Id"),
                "agency": funder.get("Name"),
                "family_name": person.get("FamilyName"),
                "given_name": person.get("GivenName"),
                "orcid": orcid,
                "funder_name": funder.get("Name"),
                "grant": grant_info.get("Title"), 
                "doi": grant_info.get("Doi"),
                "title": grant_info.get("Title"),
                "start_date": grant_info.get("StartDate"),
                "end_date": grant_info.get("EndDate"),
                "institution_name": institution.get("Name"),
            }
            grants.append(grant)
        return grants

    def create_fulltext(self, article_data, fulltext: list):

        fulltext_data = (article_data.get("fullTextUrlList") or {}).get("fullTextUrl") or []
        for ft in fulltext_data:
            text = {
                "id": "",
                "article_id": article_data.get("id"),
                "availability": ft.get("availability"),
                "availability_code": ft.get("availabilityCode"),
                "document_style": ft.get("documentStyle"),
                "site": ft.get("site"),
                "url": ft.get("url"),
            }
            fulltext.append(text)
        return fulltext

    def get_articles(self, keyword):
        json_response = self.get_json(self.base_url, self.get_articles_endpoint(keyword))        
        return json_response

    def get_references(self, id):
        json_response = self.get_json(self.base_url, self.get_references_endpoint(id))
        return json_response

    def get_citations(self, pmcid):
        json_response = self.get_json(self.base_url, self.get_citations_endpoint(pmcid))
        return json_response

    def get_grants(self, keyword):
        json_response = self.get_json(self.grants_url, self.get_grants_endpoint(keyword))
        return json_response

    def get_articles_endpoint(self, keyword):
        return f"search?query={keyword}&format=json&resultType=core"

    def get_citations_endpoint(self, id):
        return f"MED/{id}/citations?format=json"

    def get_references_endpoint(self, id):
        return f"MED/{id}/references?format=json"

    def get_grants_endpoint(self, keyword):
        return f"get/query='{keyword}'&resultType=core&format=json"

    def get_json(self, base_url: str, endpoint: str, token: Optional[str] = None, per_page: int = 100) -> Dict[str, Any]:

        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"
            
        params = {"pageSize": per_page, "cursorMark": "*"} 
        items: List[Dict[str, Any]] = []
        url = base_url + endpoint
        
        wrapper_key = "resultList"
        inner_key = "result"

        while True:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()

            try:
                data = resp.json()
            except ValueError:
                data = xmltodict.parse(resp.text)

            page_items = (data.get("resultList") or {}).get("result")
            if page_items:
                wrapper_key, inner_key = "resultList", "result"
            
            if not page_items:
                page_items = (data.get("citationList") or {}).get("citation")
                if page_items:
                    wrapper_key, inner_key = "citationList", "citation"

            if not page_items:
                page_items = (data.get("referenceList") or {}).get("reference")
                if page_items:
                    wrapper_key, inner_key = "referenceList", "reference"

            if not page_items:
                page_items = (data.get("RecordList") or {}).get("Record")
                if page_items:
                    wrapper_key, inner_key = "RecordList", "Record"

            page_items = page_items or []

            if isinstance(page_items, dict):
                page_items = [page_items]
            
            items.extend(page_items)

            next_page_url = data.get("nextPageUrl")
            
            if next_page_url and page_items:
                url = next_page_url
                params = None
            else:
                break

        return {wrapper_key: {inner_key: items}}


    def write_df_to_csv(self, df: pd.DataFrame, filename: str) -> Path:

        path = Path(filename)
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(path)
        print(f"Wrote CSV: {path}")
        return path

'''
pmc = EuropePMC()
tables = pmc.create_tables("ga4gh")
current_directory = os.getcwd()
pmc.write_df_to_csv(tables[0], current_directory + "/test_articles.csv")
pmc.write_df_to_csv(tables[1], current_directory + "/test_authors.csv")
pmc.write_df_to_csv(tables[2], current_directory + "/test_articles_authors.csv")
pmc.write_df_to_csv(tables[3], current_directory + "/test_affiliations.csv")
pmc.write_df_to_csv(tables[4], current_directory + "/test_citations.csv")
pmc.write_df_to_csv(tables[5], current_directory + "/test_references.csv")
pmc.write_df_to_csv(tables[6], current_directory + "/test_grants.csv")
pmc.write_df_to_csv(tables[7], current_directory + "/test_fulltext.csv")
'''