from datetime import datetime

import requests
import xmltodict

from src.config import constants
from src.models.article import Article
from src.models.article import Status as ArticleStatus
from src.models.author import ArticleType, Author
from src.utils.utils import parse_date


class Pubmed:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.api_key = api_key

    def get_uids(self, db: str, term: str, retmode:str="json", retmax:int=20) -> list:
        uids = []
        count = 1
        retstart = 0
        while len(uids) < count:
            term_with_filter = f"{term}[tw]"
            params = self.build_get_uid_params(db, self.api_key, term_with_filter, retmode, retstart, retmax)
            url = f"{self.base_url}{constants.PUBMED_GET_UIDS_ENDPOINT}"
            headers = {"User-Agent": constants.USER_AGENT_HEADER}

            response = requests.get(url, params=params, headers=headers, timeout=120)
            response.raise_for_status()
            resp = response.json()
            res = resp.get("esearchresult", {})

            uids = self.append_uids(uids, res)
            count = int(res.get("count", 0))
            retstart += retmax

        return uids

    def get_article_summaries(self, db: str, ids: list, retmode:str="json", batch_size: int = 200) -> list:
        all_articles = []

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            try:
                params = self.build_get_articles_params(db, self.api_key, batch_ids, retmode)
                url = f"{self.base_url}{constants.PUBMED_GET_ARTICLE_SUMMARY_ENDPOINT}"
                headers = {"User-Agent": constants.USER_AGENT_HEADER}

                response = requests.get(url, params=params, headers=headers, timeout=120)
                response.raise_for_status()
                resp = response.json()
                res = resp.get("result", {})

                if "uids" in res:
                    del res["uids"]

                raw_articles = self.get_articles(res)
                articles = self.to_article_model(raw_articles)
                all_articles.extend(articles)

            except (requests.RequestException, ValueError, KeyError, TypeError):
                continue

        return all_articles

    def get_detailed_article_info(self, db: str, article_id: str, retmode:str="xml") -> tuple[Article, str] | None:
        params = self.build_get_articles_params(db, self.api_key, [article_id], retmode)
        url = f"{self.base_url}{constants.PUBMED_GET_DETAILED_ARTICLE}"
        headers = {"User-Agent": constants.USER_AGENT_HEADER}
        response = requests.get(url, params=params, headers=headers, timeout=120)
        response.raise_for_status()

        if retmode == "xml":
            resp = response.text
            resp_json = xmltodict.parse(resp)

            if db.lower() == constants.PUBMED_DBS[1]:
                parsed_data = self.parse_pmc_article(resp_json, article_id)
            elif db.lower() == constants.PUBMED_DBS[0]:
                parsed_data = self.parse_pubmed_article(resp_json)

            return Article(
                title="",
                abstract=parsed_data["abstract"],
                journal="",
                status=ArticleStatus.UNKNOWN,
                source_id=article_id,
                doi=None,
                publish_date=None,
                link=parsed_data["link"],
                authors=parsed_data["authors"]
            ), parsed_data["status"]

        return None

    def build_get_uid_params(self, db: str, api_key: str, term: str, retmode: str, retstart: int, retmax: int) -> dict: # noqa: PLR0913
        return {
          "db": db,
          "retmode": retmode,
          "api_key": api_key,
          "term": term,
          "retstart": retstart,
          "retmax": retmax,
          "tool": "analytics-dashboard",
        }

    def append_uids(self, uids: list, res: dict) -> list:
        return uids + list(res.get("idlist", []))

    def build_get_articles_params(self, db: str, api_key: str, ids: list, retmode: str) -> dict:
        return {
          "db": db,
          "id": ",".join(ids),
          "retmode": retmode,
          "api_key": api_key,
          "tool": "analytics-dashboard",
        }

    def get_articles(self, res: dict) -> list:
        return list(res.values())

    def to_article_model(self, raw_articles: list) -> list[Article]:
        articles = []

        for a in raw_articles:
            article = Article(
                title = a.get("title", ""),
                journal = a.get("fulljournalname", ""),
                source_id = a.get("uid", ""),
                doi = self.get_doi(a.get("articleids", [])),
                status = ArticleStatus.UNKNOWN,
                publish_date = self.get_publication_date(a.get("pubdate"), a.get("epubdate"))
            )
            articles.append(article)
        return articles

    def get_doi(self, ids: list) -> str:
        for id_type in ids:
            if id_type.get("idtype", "") == "doi":
                return id_type.get("value", "")
        return ""

    def get_publication_date(self, pubdate: str, epubdate: str) -> datetime | None:
        dates = []
        for date_str in [pubdate, epubdate]:
            if date_str:
                parsed_date = parse_date(date_str)
                if parsed_date:
                    dates.append(parsed_date)

        return min(dates) if dates else None

    def parse_pubmed_article(self, xml_data: dict) -> dict:
        try:
            pubmed_article_set = xml_data.get("PubmedArticleSet", {})
            if isinstance(pubmed_article_set, list):
                pubmed_article = pubmed_article_set[0] if pubmed_article_set else {}
            else:
                pubmed_article = pubmed_article_set.get("PubmedArticle", {})

            medline_citation = pubmed_article.get("MedlineCitation", {})
            pubmed_data = pubmed_article.get("PubmedData", {})

            article = medline_citation.get("Article", {})

            abstract = self.parse_abstract(article)
            authors = self.parse_authors(article)
            status = pubmed_data.get("PublicationStatus", "")
            link = self.parse_link(pubmed_data)

            return { # noqa: TRY300
                "abstract": abstract,
                "authors": authors,
                "status": status,
                "link": link,
            }
        except (KeyError, TypeError, AttributeError, ValueError):
            return { # noqa: TRY300
                "abstract": "",
                "authors": None,
                "status": "",
                "link": "",
            }
        
    def parse_abstract(self, article: dict) -> str | None:
        abstract_section = article.get("Abstract", {})
        if not abstract_section:
            return None

        abstract_texts = abstract_section.get("AbstractText", [])
        if isinstance(abstract_texts, str):
            return abstract_texts
        if isinstance(abstract_texts, list):
            return abstract_texts[0].get("#text", "")
        if isinstance(abstract_texts, dict):
            return abstract_texts.get("#text", "")

        return None

    def parse_authors(self, article: dict) -> list[Author]:
        authors = []
        author_list = article.get("AuthorList", {}).get("Author", [])

        if not isinstance(author_list, list):
            author_list = [author_list]

        for i, author_data in enumerate(author_list):
            if not author_data:
                continue

            last_name = author_data.get("LastName", "")
            first_name = author_data.get("ForeName", "")
            initials = author_data.get("Initials", "")

            full_name = f"{first_name} {last_name}".strip()
            if not full_name:
                full_name = f"{initials} {last_name}".strip()

            if full_name == "":
                continue

            author = Author(
                article_id=0,
                name=full_name,
                contact=None,
                is_primary=(i == 0),  # First author is primary
                article_type=ArticleType.ARTICLE,
                affiliations=[] # TODO: add parser logic
            )
            authors.append(author)

        return authors

    def parse_link(self, pubmed_data: dict) -> str | None:
        article_ids = pubmed_data.get("ArticleIdList", {}).get("ArticleId", [])

        if not isinstance(article_ids, list):
            article_ids = [article_ids]

        for article_id in article_ids:
            if isinstance(article_id, dict) and article_id.get("@IdType") == "pubmed":
                    pmid = article_id.get("#text", "")
                    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        return ""

    def parse_pmc_article(self, xml_data: dict, pmc_id: str) -> dict:
        try:
            pmc_article_set = xml_data.get("pmc-articleset", {})
            if isinstance(pmc_article_set, list):
                article_data = pmc_article_set[0] if pmc_article_set else {}
            else:
                article_data = pmc_article_set.get("article", {})

            front = article_data.get("front", {})
            article_meta = front.get("article-meta", {})

            abstract = self.parse_pmc_abstract(article_meta)
            authors = self.parse_pmc_authors(article_meta)
            link = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc_id}/"
            status = article_meta.get("article-categories", {}).get("subj-group", {}).get("subject", "")

            return { # noqa: TRY300
                "abstract": abstract,
                "status": status,
                "link": link,
                "authors": authors
            }
        except (KeyError, TypeError, AttributeError, ValueError):
            return { # noqa: TRY300
                "abstract": "",
                "status": "",
                "link": "",
                "authors": None
            }
        
    def parse_pmc_abstract(self, article_meta: dict) -> str | None:
        abstract_section = article_meta.get("abstract", {})
        if isinstance(abstract_section, dict):
            paragraphs = abstract_section.get("p", "")
            if isinstance(paragraphs, list):
                return paragraphs[0].get("p", "")
            if isinstance(paragraphs, str):
                return paragraphs
        return ""

    def parse_pmc_authors(self, article_meta: dict) -> list[Author]:
        authors = []
        contrib_group = article_meta.get("contrib-group", {})
        contribs = contrib_group.get("contrib", [])

        if not isinstance(contribs, list):
            contribs = [contribs]

        for i, contrib in enumerate(contribs):
            if contrib.get("@contrib-type") == "author":
                name_data = contrib.get("name", {})
                given_names = name_data.get("given-names", {}).get("#text", "")
                surname = name_data.get("surname", "")
                full_name = f"{given_names} {surname}".strip()

                author = Author(
                    article_id=0,
                    name=full_name,
                    contact=None,
                    is_primary=(i == 0),
                    article_type=ArticleType.ARTICLE,
                    affiliations=[] # TODO: add parser logic
                )
                authors.append(author)

        return authors

    def parse_pmc_link(self, article_meta: dict) -> str | None:
        article_ids = article_meta.get("article-id", [])

        if not isinstance(article_ids, list):
            article_ids = [article_ids]

        for article_id in article_ids:
            if isinstance(article_id, dict) and article_id.get("@IdType") == "pmcid":
                    pmid = article_id.get("#text", "")
                    return f"https://pmc.ncbi.nlm.nih.gov/articles/{pmid}/"

        return ""
