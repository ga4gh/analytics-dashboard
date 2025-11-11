from pydantic import BaseModel


class InsertArticlesRequest(BaseModel):
    keyword: str
    pubmed_db: str = "pubmed"


class InsertArticlesResponse(BaseModel):
    processed: int
    created: int
    updated: int
    skipped: int
