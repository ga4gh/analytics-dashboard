DROP TRIGGER IF EXISTS animals_audit_trigger ON public.animals;
DROP FUNCTION IF EXISTS animals_audit_trigger_func;
DROP TABLE IF EXISTS animals_audit;
DROP INDEX IF EXISTS idx_animals_breed;
DROP INDEX IF EXISTS idx_animals_species;
DROP TABLE IF EXISTS animals;