from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class GithubRepo(BaseModel):
    id: Optional[int] = None
    record_id: int
    name: str
    repo_link: str
    owner: str
    description: Optional[str] = None
    is_fork: bool
    last_updated: datetime
    pushed_at: datetime
    is_archived: bool
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
    created_on: Optional[datetime] = None
    type: Optional[str] = None
    display_flag: Optional[bool] = None
    archived: Optional[bool] = None
    workstream: Optional[str] = None
    status: Optional[str] = None


class GithubRepoRequest(BaseModel):
    name: str
    repo_link: str
    owner: str
    description: Optional[str] = None
    is_fork: bool
    last_updated: datetime
    pushed_at: datetime
    is_archived: bool
    license: Optional[str] = None
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    network_count: int
    subscribers_count: int
    branches_count: int
    created_on: datetime

class GithubEntity(BaseModel):
    id: Optional[int] = None
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
    id: Optional[int] = None
    repo_id: int
    action_type: str
    user_id: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    version: int


class GithubEntityActionRequest(BaseModel):
    repo_id: int
    action_type: str
    user_id: str


class GithubArchivedStat(BaseModel):
    id: Optional[int] = None
    repo_id: int
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
    repo_id: int
    weekly_commit_add: int
    weekly_commit_del: int
    yearly_commit_count: int
    daily_clone_count: int
    daily_view_count: int
    last_14_day_top_referral_sources: List[str]
    last_14_day_top_referral_path: List[str]
