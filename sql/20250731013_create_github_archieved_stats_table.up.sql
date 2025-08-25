-- Main table
CREATE TABLE github_archieved_stats (
    id BIGSERIAL PRIMARY KEY,
    repo_id BIGSERIAL NOT NULL,
    weekly_commit_add INT NOT NULL,
    weekly_commit_del INT NOT NULL,
    yearly_commit_count INT[] NOT NULL, -- Expected array length 52
    daily_clone_count INT NOT NULL,
    daily_view_count INT NOT NULL,
    last_14_day_top_referral_sources JSONB[] NOT NULL,
    last_14_day_top_referral_path JSONB[] NOT NULL,
    created_by VARCHAR(64) NOT NULL,
  	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	updated_by VARCHAR(64) NOT NULL,
  	updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  	deleted_by VARCHAR(64),
  	deleted_at TIMESTAMPTZ,
  	version INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_github_archieved_stats_repo_id ON github_archieved_stats(repo_id);

-- Audit table
CREATE TABLE github_archieved_stats_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    action_by TEXT,
    github_archieved_stats_id UUID,
    weekly_commit_add_before                   INT,
    weekly_commit_add_after                    INT,
    weekly_commit_del_before                   INT,
    weekly_commit_del_after                    INT,
    yearly_commit_count_before                 INT[],
    yearly_commit_count_after                  INT[],
    daily_clone_count_before                   INT,
    daily_clone_count_after                    INT,
    daily_view_count_before                    INT,
    daily_view_count_after                     INT,
    last_14_day_top_referral_sources_before    JSONB[],
    last_14_day_top_referral_sources_after     JSONB[],
    last_14_day_top_referral_path_before       JSONB[],
    last_14_day_top_referral_path_after        JSONB[],
    created_at_before                          TIMESTAMPTZ,
    created_at_after                           TIMESTAMPTZ,
    created_by_before                          VARCHAR,
    created_by_after                           VARCHAR,
    updated_at_before                          TIMESTAMPTZ,
    updated_at_after                           TIMESTAMPTZ,
    updated_by_before                          VARCHAR,
    updated_by_after                           VARCHAR,
    deleted_at_before                          TIMESTAMPTZ,
    deleted_at_after                           TIMESTAMPTZ,
    deleted_by_before                          VARCHAR,
    deleted_by_after                           VARCHAR,
    version_before                             INT,
    version_after                              INT,

    UNIQUE(github_archieved_stats_id, version_after)
);

-- Trigger function
CREATE OR REPLACE FUNCTION github_archieved_stats_audit_trigger_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_action    TEXT := TG_OP;  -- 'INSERT' | 'UPDATE' | 'DELETE'
    v_action_by TEXT;
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO github_archieved_stats_audit (
            action, action_by, github_archieved_stats_id,
            weekly_commit_add_before, weekly_commit_add_after,
            weekly_commit_del_before, weekly_commit_del_after,
            yearly_commit_count_before, yearly_commit_count_after,
            daily_clone_count_before, daily_clone_count_after,
            daily_view_count_before, daily_view_count_after,
            last_14_day_top_referral_sources_before, last_14_day_top_referral_sources_after,
            last_14_day_top_referral_path_before, last_14_day_top_referral_path_after,
            created_at_before, created_at_after,
            created_by_before, created_by_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NULL, NEW.weekly_commit_add,
            NULL, NEW.weekly_commit_del,
            NULL, NEW.yearly_commit_count,
            NULL, NEW.daily_clone_count,
            NULL, NEW.daily_view_count,
            NULL, NEW.last_14_day_top_referral_sources,
            NULL, NEW.last_14_day_top_referral_path,
            NULL, NEW.created_at,
            NULL, NEW.created_by,
            NULL, NEW.updated_at,
            NULL, NEW.updated_by,
            NULL, NEW.deleted_at,
            NULL, NEW.deleted_by,
            NULL, NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'UPDATE' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO github_archieved_stats_audit (
            action, action_by, github_archieved_stats_id,
            weekly_commit_add_before, weekly_commit_add_after,
            weekly_commit_del_before, weekly_commit_del_after,
            yearly_commit_count_before, yearly_commit_count_after,
            daily_clone_count_before, daily_clone_count_after,
            daily_view_count_before, daily_view_count_after,
            last_14_day_top_referral_sources_before, last_14_day_top_referral_sources_after,
            last_14_day_top_referral_path_before, last_14_day_top_referral_path_after,
            created_at_before, created_at_after,
            created_by_before, created_by_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.weekly_commit_add, NEW.weekly_commit_add,
            OLD.weekly_commit_del, NEW.weekly_commit_del,
            OLD.yearly_commit_count, NEW.yearly_commit_count,
            OLD.daily_clone_count, NEW.daily_clone_count,
            OLD.daily_view_count, NEW.daily_view_count,
            OLD.last_14_day_top_referral_sources, NEW.last_14_day_top_referral_sources,
            OLD.last_14_day_top_referral_path, NEW.last_14_day_top_referral_path,
            OLD.created_at, NEW.created_at,
            OLD.created_by, NEW.created_by,
            OLD.updated_at, NEW.updated_at,
            OLD.updated_by, NEW.updated_by,
            OLD.deleted_at, NEW.deleted_at,
            OLD.deleted_by, NEW.deleted_by,
            OLD.version, NEW.version
        );
        RETURN NEW;

    ELSIF v_action = 'DELETE' THEN
        v_action_by := COALESCE(OLD.deleted_by, OLD.updated_by, OLD.created_by, current_user);
        INSERT INTO github_archieved_stats_audit (
            action, action_by, github_archieved_stats_id,
            weekly_commit_add_before, weekly_commit_add_after,
            weekly_commit_del_before, weekly_commit_del_after,
            yearly_commit_count_before, yearly_commit_count_after,
            daily_clone_count_before, daily_clone_count_after,
            daily_view_count_before, daily_view_count_after,
            last_14_day_top_referral_sources_before, last_14_day_top_referral_sources_after,
            last_14_day_top_referral_path_before, last_14_day_top_referral_path_after,
            created_at_before, created_at_after,
            created_by_before, created_by_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.weekly_commit_add, NULL,
            OLD.weekly_commit_del, NULL,
            OLD.yearly_commit_count, NULL,
            OLD.daily_clone_count, NULL,
            OLD.daily_view_count, NULL,
            OLD.last_14_day_top_referral_sources, NULL,
            OLD.last_14_day_top_referral_path, NULL,
            OLD.created_at, NULL,
            OLD.created_by, NULL,
            OLD.updated_at, NULL,
            OLD.updated_by, NULL,
            OLD.deleted_at, NULL,
            OLD.deleted_by, NULL,
            OLD.version, NULL
        );
        RETURN OLD;
    END IF;

    RAISE WARNING 'github_archieved_stats_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

-- Trigger binding
CREATE TRIGGER github_archieved_stats_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.github_archieved_stats
FOR EACH ROW EXECUTE FUNCTION github_archieved_stats_audit_trigger_func();
