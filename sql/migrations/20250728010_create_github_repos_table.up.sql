-- Create main table github_repos

CREATE TABLE IF NOT EXISTS github_repos (
	id SERIAL PRIMARY KEY,
	record_id INTEGER NOT NULL,
	name VARCHAR(128) NOT NULL,
	repo_link VARCHAR(128) NOT NULL,
	owner VARCHAR(128) NOT NULL,
	description VARCHAR NOT NULL,
	is_fork BOOLEAN NOT NULL,
	last_updated TIMESTAMP NOT NULL,
	pushed_at TIMESTAMP NOT NULL,
	is_archived BOOLEAN NOT NULL,
	license VARCHAR(64) NOT NULL,
	stargazers_counts INTEGER NOT NULL,
	watchers_count INTEGER NOT NULL,
	forks_count INTEGER NOT NULL,
	open_issues_count INTEGER NOT NULL,
	network_count INTEGER NOT NULL,
	subscribers_count INTEGER NOT NULL,
	branches_count INTEGER NOT NULL,
	created_by VARCHAR(64) NOT NULL,
  	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	updated_by VARCHAR(64) NOT NULL,
  	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	deleted_by VARCHAR(64),
  	deleted_at TIMESTAMPTZ,
  	version INTEGER NOT NULL,
	CONSTRAINT fk_record
        FOREIGN KEY (id)
        REFERENCES records (id)
        ON DELETE CASCADE
);

-- Create indexes on main table

CREATE INDEX IF NOT EXISTS idx_github_repos_name ON github_repos(name);
CREATE INDEX IF NOT EXISTS idx_github_repos_owner ON github_repos(owner);
CREATE INDEX IF NOT EXISTS idx_github_repos_is_archived ON github_repos(is_archived);
CREATE INDEX IF NOT EXISTS idx_github_repos_is_fork ON github_repos(is_fork);

-- Create audit table for github_repos

CREATE TABLE IF NOT EXISTS github_repos_audit (
	audit_id SERIAL PRIMARY KEY,
	action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
	action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
	action_by VARCHAR(64),
	github_repo_id INTEGER NOT NULL,
	name_before VARCHAR(128),
	name_after VARCHAR(128),
	repo_link_before VARCHAR(128),
	repo_link_after VARCHAR(128),
	owner_before VARCHAR(128),
	owner_after VARCHAR(128),
	description_before VARCHAR,
	description_after VARCHAR,
	is_fork_before BOOLEAN,
	is_fork_after BOOLEAN,
	last_updated_before TIMESTAMP,
	last_updated_after TIMESTAMP,
	pushed_at_before TIMESTAMP,
	pushed_at_after TIMESTAMP,
	is_archived_before BOOLEAN,
	is_archived_after BOOLEAN,
	license_before VARCHAR(64),
	license_after VARCHAR(64),
	stargazers_counts_before INTEGER,
	stargazers_counts_after INTEGER,
	watchers_count_before INTEGER,
	watchers_count_after INTEGER,
	forks_count_before INTEGER,
	forks_count_after INTEGER,
	open_issues_count_before INTEGER,
	open_issues_count_after INTEGER,
	network_count_before INTEGER,
	network_count_after INTEGER,
	subscribers_count_before INTEGER,
	subscribers_count_after INTEGER,
	branches_count_before INTEGER,
	branches_count_after INTEGER,
	created_by_before VARCHAR(64),
	created_by_after VARCHAR(64),
	created_at_before TIMESTAMPTZ,
	created_at_after TIMESTAMPTZ,
	updated_by_before VARCHAR(64),
	updated_by_after VARCHAR(64),
	updated_at_before TIMESTAMPTZ,
	updated_at_after TIMESTAMPTZ,
	deleted_by_before VARCHAR(64),
	deleted_by_after VARCHAR(64),
	deleted_at_before TIMESTAMPTZ,
	deleted_at_after TIMESTAMPTZ,
	version_before INTEGER,
	version_after INTEGER,
	UNIQUE(github_repo_id,version_after)
);

-- Create indexes on audit table

CREATE INDEX IF NOT EXISTS idx_github_repos_audit_repo_id ON github_repos_audit(github_repo_id);
CREATE INDEX IF NOT EXISTS idx_github_repos_audit_action_tstamp ON github_repos_audit(action_tstamp);

-- Create trigger function

CREATE OR REPLACE FUNCTION github_repos_audit_trigger_func()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
DECLARE
	v_action TEXT := TG_OP;
	v_action_by VARCHAR(64);
BEGIN
	IF v_action = 'INSERT' THEN
		v_action_by := current_user;
		INSERT INTO github_repos_audit (
			action, action_by, github_repo_id,
			name_after, repo_link_after, owner_after, description_after,
			is_fork_after, last_updated_after, pushed_at_after, is_archived_after, license_after,
			stargazers_counts_after, watchers_count_after, forks_count_after,
			open_issues_count_after, network_count_after, subscribers_count_after, branches_count_after,
			created_by_after, created_at_after, updated_by_after, updated_at_after,
			deleted_by_after, deleted_at_after, version_after
		) VALUES (
			v_action, v_action_by, NEW.id,
			NEW.name, NEW.repo_link, NEW.owner, NEW.description,
			NEW.is_fork, NEW.last_updated, NEW.pushed_at, NEW.is_archived, NEW.license,
			NEW.stargazers_counts, NEW.watchers_count, NEW.forks_count,
			NEW.open_issues_count, NEW.network_count, NEW.subscribers_count, NEW.branches_count,
			NEW.created_by, NEW.created_at, NEW.updated_by, NEW.updated_at,
			NEW.deleted_by, NEW.deleted_at, NEW.version
		);
		RETURN NEW;

	ELSIF v_action = 'UPDATE' THEN
		v_action_by := current_user;
		INSERT INTO github_repos_audit (
			action, action_by, github_repo_id,
			name_before, name_after,
			repo_link_before, repo_link_after,
			owner_before, owner_after,
			description_before, description_after,
			is_fork_before, is_fork_after,
			last_updated_before, last_updated_after,
			pushed_at_before, pushed_at_after,
			is_archived_before, is_archived_after,
			license_before, license_after,
			stargazers_counts_before, stargazers_counts_after,
			watchers_count_before, watchers_count_after,
			forks_count_before, forks_count_after,
			open_issues_count_before, open_issues_count_after,
			network_count_before, network_count_after,
			subscribers_count_before, subscribers_count_after,
			branches_count_before, branches_count_after,
			created_by_before, created_by_after,
			created_at_before, created_at_after,
			updated_by_before, updated_by_after,
			updated_at_before, updated_at_after,
			deleted_by_before, deleted_by_after,
			deleted_at_before, deleted_at_after,
			version_before, version_after
		) VALUES (
			v_action, v_action_by, NEW.id,
			OLD.name, NEW.name,
			OLD.repo_link, NEW.repo_link,
			OLD.owner, NEW.owner,
			OLD.description, NEW.description,
			OLD.is_fork, NEW.is_fork,
			OLD.last_updated, NEW.last_updated,
			OLD.pushed_at, NEW.pushed_at,
			OLD.is_archived, NEW.is_archived,
			OLD.license, NEW.license,
			OLD.stargazers_counts, NEW.stargazers_counts,
			OLD.watchers_count, NEW.watchers_count,
			OLD.forks_count, NEW.forks_count,
			OLD.open_issues_count, NEW.open_issues_count,
			OLD.network_count, NEW.network_count,
			OLD.subscribers_count, NEW.subscribers_count,
			OLD.branches_count, NEW.branches_count,
			OLD.created_by, NEW.created_by,
			OLD.created_at, NEW.created_at,
			OLD.updated_by, NEW.updated_by,
			OLD.updated_at, NEW.updated_at,
			OLD.deleted_by, NEW.deleted_by,
			OLD.deleted_at, NEW.deleted_at,
			OLD.version, NEW.version
		);
		RETURN NEW;

	ELSIF v_action = 'DELETE' THEN
		v_action_by := current_user;
		INSERT INTO github_repos_audit (
			action, action_by, github_repo_id,
			name_before, repo_link_before, owner_before, description_before,
			is_fork_before, last_updated_before, pushed_at_before, is_archived_before, license_before,
			stargazers_counts_before, watchers_count_before, forks_count_before,
			open_issues_count_before, network_count_before, subscribers_count_before, branches_count_before,
			created_by_before, created_at_before, updated_by_before, updated_at_before,
			deleted_by_before, deleted_at_before, version_before
		) VALUES (
			v_action, v_action_by, OLD.id,
			OLD.name, OLD.repo_link, OLD.owner, OLD.description,
			OLD.is_fork, OLD.last_updated, OLD.pushed_at, OLD.is_archived, OLD.license,
			OLD.stargazers_counts, OLD.watchers_count, OLD.forks_count,
			OLD.open_issues_count, OLD.network_count, OLD.subscribers_count, OLD.branches_count,
			OLD.created_by, OLD.created_at, OLD.updated_by, OLD.updated_at,
			OLD.deleted_by, OLD.deleted_at, OLD.version
		);
		RETURN OLD;
	END IF;

	RAISE WARNING 'github_repos_audit_trigger_func() fired for unexpected operation: %', TG_OP;
	RETURN NULL;
END;
$$;

-- Attach trigger

CREATE TRIGGER trg_audit_github_repos
AFTER INSERT OR UPDATE OR DELETE ON github_repos
FOR EACH ROW EXECUTE FUNCTION github_repos_audit_trigger_func();
