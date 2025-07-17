CREATE TABLE animals (
    id BIGSERIAL PRIMARY KEY, 
    name VARCHAR NOT NULL, 
    age INT NOT NULL, 
    species VARCHAR NOT NULL, 
    breed VARCHAR NOT NULL, 
    owner VARCHAR, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), 
    created_by VARCHAR NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), 
    updated_by VARCHAR NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR, 
    version INT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_animals_species ON animals(species);
CREATE INDEX IF NOT EXISTS idx_animals_breed ON animals(breed);

CREATE TABLE animals_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    action_tstamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    action TEXT NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    action_by TEXT,
    animals_id INTEGER,

    name_before            VARCHAR,
    name_after             VARCHAR,
    age_before             INT,
    age_after              INT,
    species_before         VARCHAR,
    species_after          VARCHAR,
    breed_before           VARCHAR,
    breed_after            VARCHAR,
    owner_before           VARCHAR,
    owner_after            VARCHAR,
    created_at_before      TIMESTAMPTZ,
    created_at_after       TIMESTAMPTZ,
    created_by_before      VARCHAR,
    created_by_after       VARCHAR,
    updated_at_before      TIMESTAMPTZ,
    updated_at_after       TIMESTAMPTZ,
    updated_by_before      VARCHAR,
    updated_by_after       VARCHAR,
    deleted_at_before      TIMESTAMPTZ,
    deleted_at_after       TIMESTAMPTZ,
    deleted_by_before      VARCHAR,
    deleted_by_after       VARCHAR,
    version_before         INT,
    version_after          INT,

    UNIQUE(animals_id, version_after)
);

CREATE OR REPLACE FUNCTION animals_audit_trigger_func()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_action    TEXT := TG_OP;  -- 'INSERT' | 'UPDATE' | 'DELETE'
    v_action_by TEXT;
BEGIN
    IF v_action = 'INSERT' THEN
        v_action_by := COALESCE(NEW.updated_by, NEW.created_by, current_user);
        INSERT INTO animals_audit (
            action, action_by, animals_id,
            name_before, name_after,
            age_before, age_after,
            species_before, species_after,
            breed_before, breed_after,
            owner_before, owner_after,
            created_at_before, created_at_after,
            created_by_before, created_by_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            NULL, NEW.name,
            NULL, NEW.age,
            NULL, NEW.species,
            NULL, NEW.breed,
            NULL, NEW.owner,
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
        INSERT INTO animals_audit (
            action, action_by, animals_id,
            name_before, name_after,
            age_before, age_after,
            species_before, species_after,
            breed_before, breed_after,
            owner_before, owner_after,
            created_at_before, created_at_after,
            created_by_before, created_by_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, NEW.id,
            OLD.name, NEW.name,
            OLD.age, NEW.age,
            OLD.species, NEW.species,
            OLD.breed, NEW.breed,
            OLD.owner, NEW.owner,
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
        INSERT INTO animals_audit (
            action, action_by, animals_id,
            name_before, name_after,
            age_before, age_after,
            species_before, species_after,
            breed_before, breed_after,
            owner_before, owner_after,
            created_at_before, created_at_after,
            created_by_before, created_by_after,
            updated_at_before, updated_at_after,
            updated_by_before, updated_by_after,
            deleted_at_before, deleted_at_after,
            deleted_by_before, deleted_by_after,
            version_before, version_after
        ) VALUES (
            v_action, v_action_by, OLD.id,
            OLD.name, NULL,
            OLD.age, NULL,
            OLD.species, NULL,
            OLD.breed, NULL,
            OLD.owner, NULL,
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

    RAISE WARNING 'animals_audit_trigger_func() fired for unexpected operation: %', TG_OP;
    RETURN NULL;
END;
$$;

CREATE TRIGGER animals_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.animals
FOR EACH ROW EXECUTE FUNCTION animals_audit_trigger_func();