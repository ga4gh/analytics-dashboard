from datetime import datetime
from typing import Any, Dict, List, Optional
from src.models.pmc_article import PMCArticle as Article, PMCFullText, PMCCitation, PMCReference
from src.models.pmc_author import PMCAuthor as Author, PMCAffiliation as Affiliation, ArticleAuthor
from src.models.grant import Grant

import requests
import pandas as pd
from pathlib import Path
import os
import xmltodict


class EPMCClient:
    def __init__(self) -> None:
        self.base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
        self.grants_url = "https://www.ebi.ac.uk/europepmc/GristAPI/rest/"
        self.token = ""

    def create_article(self, article_data, id):
        return Article(
            id=id,
            record_id=id,
            Source=article_data.get("source"),
            Pm_id=article_data.get("id"),
            Pmc_id=article_data.get("pmcid"),
            Full_text_id="",
            Doi=article_data.get("doi"),
            Title=article_data.get("title"),
            Pub_year=article_data.get("pubYear"),
            Abstract_text=article_data.get("abstractText"),
            Affiliation=article_data.get("affiliation"),
            Publicication_status=article_data.get("publicationStatus"),
            Language=article_data.get("language"),
            Pub_type=(article_data.get("pubTypeList") or {}).get("pubType"),
            Is_open_access=bool(article_data.get("isOpenAccess")),
            inEPMC=bool(article_data.get("inEPMC")),
            inPMC=bool(article_data.get("inPMC")),
            hasPDF=bool(article_data.get("hasPDF")),
            hasBook=bool(article_data.get("hasBook")),
            hasSuppl=bool(article_data.get("hasSuppl")),
            Cited_by_count=article_data.get("citedByCount"),
            Has_references=bool(article_data.get("hasReferences")),
            Dateofcreation=article_data.get("dateOfCreation"),
            firstIndexdate=article_data.get("firstIndexDate"),
            Fulltextreceivedate=article_data.get("fullTextReceivedDate"),
            Revisiondate=article_data.get("dateOfRevision"),
            Epubdate=article_data.get("electronicPublicationDate"),
            Firstpublicationdate=article_data.get("firstPublicationDate"),
        )

    def create_author(self, author_data):
        return Author(
            id= "",
            fullname= author_data.get("fullName"),
            firstname= author_data.get("firstName"),
            lastname= author_data.get("lastName"),
            initials= author_data.get("initials"),
            orcid= (author_data.get("authorId") or {}).get("value"),
        )

    def create_article_author(self, article_data, author_data, author_order, author_id):
        
        return ArticleAuthor(
            id= "",
            article_id= article_data.get("id") or article_data.get("pmid"),
            author_id= author_id,
            author_order= author_order 
        )

    def create_affiliation(self, affiliation_data, author_id):
        org_name = affiliation_data.get("affiliation") if isinstance(affiliation_data, dict) else affiliation_data
        
        return Affiliation(
            id= "",
            author_id= author_id,
            org_name= org_name
        )

    def create_grant(self, article_data, record_id):
            
        return Grant(
            id= "",
            record_id = record_id,
            article_id= article_data.get("id") or article_data.get("pmid"),
            grant_id= article_data.get("grantId") or article_data.get("grant_id"),
            agency= article_data.get("agency"),
            family_name= "",
            given_name= "",
            orcid= "",
            funder_name= "",
            grant= "", 
            doi= "",
            title= "",
            start_date= "",
            end_date= "",
            institution_name= "",
        )

    def create_citation(self, cite, pmid, count):

        return PMCCitation(
            id= "",
            article_id= pmid,
            citation_id= cite.get("id"),
            source= cite.get("source"),
            citation_type= cite.get("citationType") or cite.get("citation_type"),
            title= cite.get("title"),
            authors= cite.get("authors"),
            pub_year= cite.get("pubYear") or cite.get("pub_year"),
            citation_count= count,
        )

    def create_reference(self, article_data):

        return PMCReference(
            id= "",
            article_id= article_data.get("id"),
            reference_id= article_data.get("id"),
            source= article_data.get("source"),
            citation_type= article_data.get("citationType") or article_data.get("citation_type"),
            title= article_data.get("title"),
            authors= article_data.get("authors"),
            pub_year= article_data.get("pubYear") or article_data.get("pub_year"),
            issn= article_data.get("ISSN") or article_data.get("issn"),
            essn= article_data.get("ESSN") or article_data.get("essn"),
            cited_order= article_data.get("citedOrder") or article_data.get("cited_order"),
            match= bool(article_data.get("match")) if article_data.get("match") is not None else None,
        )

    def create_grant_api(self, gr, record_id):

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
        return Grant(
            id= "",
            record_id= record_id,
            grant_id= grant_info.get("Id"),
            agency= funder.get("Name"),
            family_name= person.get("FamilyName"),
            given_name= person.get("GivenName"),
            orcid= orcid,
            funder_name= funder.get("Name"),
            grant= grant_info.get("Title"), 
            doi= grant_info.get("Doi"),
            title= grant_info.get("Title"),
            start_date= grant_info.get("StartDate"),
            end_date= grant_info.get("EndDate"),
            institution_name= institution.get("Name"),
        )

    def create_fulltext(self, article_data, ft):
        return PMCFullText(
            id= "",
            article_id= article_data.get("id"),
            availability= ft.get("availability"),
            availability_code= ft.get("availabilityCode"),
            document_style= ft.get("documentStyle"),
            site= ft.get("site"),
            url= ft.get("url"),
        )

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
