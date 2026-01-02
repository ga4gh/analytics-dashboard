from typing import List
from src.models.pmc_article import PMCArticleFull
from src.repositories.epmc import EPMCRepo as EPMCRepo

class EPMCService:
    def __init__(self, repo: EPMCRepo) -> None:
        self.epmc_repo = repo
        
    def get_all_articles(self) -> List[PMCArticleFull]:
        return self.epmc_repo.get_all_articles()