from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class GithubRepo(BaseModel):
    id: int
    record_id: str
    name: str
    repo_link: str
    owner: str
    description: Optional[str] = None
    fork: bool
    last_update: datetime
    pushed_at: datetime
    archived: bool
    license: Optional[str] = None
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    network_count: int
    subscribers_count: int
    branches_count: int
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    version: int


class GithubRepoRequest(BaseModel):
    name: str
    repo_link: str
    owner: str
    description: Optional[str] = None
    fork: bool
    last_update: datetime
    pushed_at: datetime
    archived: bool
    license: Optional[str] = None
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    network_count: int
    subscribers_count: int
    branches_count: int


class GithubEntity(BaseModel):
    id: int
    name: str
    user_id: str
    company: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    type: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    version: int


class GithubEntityRequest(BaseModel):
    name: str
    user_id: str
    company: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    type: str


class GithubEntityAction(BaseModel):
    id: int
    repo_id: str
    action_type: str
    user_id: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    version: int


class GithubEntityActionRequest(BaseModel):
    repo_id: str
    action_type: str
    user_id: str


class GithubArchivedStat(BaseModel):
    id: int
    repo_id: str
    weekly_commit_add: int
    weekly_commit_del: int
    yearly_commit_count: int
    daily_clone_count: int
    daily_view_count: int
    last_14_day_top_referral_sources: List[str]
    last_14_day_top_referral_path: List[str]
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    version: int


class GithubArchivedStatRequest(BaseModel):
    repo_id: str
    weekly_commit_add: int
    weekly_commit_del: int
    yearly_commit_count: int
    daily_clone_count: int
    daily_view_count: int
    last_14_day_top_referral_sources: List[str]
    last_14_day_top_referral_path: List[str]
