-- One-time content reset before the Five Dynasties and Ten Kingdoms corpus.
-- Keep applied migration history intact; a complete replay must end empty.
-- Do not rerun this migration after new editorial content has been added.
BEGIN;
DO $$
DECLARE content_table text;
BEGIN
  FOREACH content_table IN ARRAY ARRAY[
    'topic', 'fact_claim', 'person_event', 'person_relationship',
    'event_causality', 'person', 'event', 'source',
    'relationships', 'people', 'events'
  ] LOOP
    IF to_regclass('public.' || content_table) IS NOT NULL THEN
      EXECUTE format('DELETE FROM public.%I', content_table);
    END IF;
  END LOOP;
END $$;
COMMIT;
