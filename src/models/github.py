from array import array
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class GithubRepo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_id: str
    name: str
    repo_link: str
    owner: str
    description: str
    fork: bool
    last_update: datetime
    pushed_at: datetime
    archieved: bool
    license: str
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
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version: int

class GithubArchievedStat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repo_id: str
    weekly_commit_add: int
    weekly_commit_del: int
    yearly_commit_count: array
    daily_clone_count: int
    daily_view_count: int
    last_14_day_top_referral_sources: array
    last_14_day_top_referral_path: array
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version: int


class GithubEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    user_id: str
    company: str
    email: str
    location: str
    type: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version: int

class GithubEntityAction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repo_id: str
    action_type: str
    user_id: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    version: int

class GithubRepoRequest(BaseModel):
    name: str
    repo_link: str
    owner: str
    description: str
    fork: bool
    last_update: datetime
    pushed_at: datetime
    archieved: bool
    license: str
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    network_count: int
    subscribers_count: int
    branches_count: int

class GithubArchievedStatRequest(BaseModel):
    repo_id: str
    weekly_commit_add: int
    weekly_commit_del: int
    yearly_commit_count: array
    daily_clone_count: int
    daily_view_count: int
    last_14_day_top_referral_sources: array
    last_14_day_top_referral_path: array

class GithubEntityRequest(BaseModel):
    name: str
    user_id: str
    company: str
    email: str
    location: str
    type: str

class GithubEntityActionRequest(BaseModel):
    repo_id: str
    action_type: str
    user_id: str
