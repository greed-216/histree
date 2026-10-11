BEGIN;
ALTER TABLE public.person ADD COLUMN status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published'));
ALTER TABLE public.person ALTER COLUMN status SET DEFAULT 'draft';
ALTER TABLE public.event ADD COLUMN status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published'));
ALTER TABLE public.event ALTER COLUMN status SET DEFAULT 'draft';
ALTER TABLE public.person_relationship ADD COLUMN status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published'));
ALTER TABLE public.person_relationship ALTER COLUMN status SET DEFAULT 'draft';
ALTER TABLE public.person_event ADD COLUMN status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published'));
ALTER TABLE public.person_event ALTER COLUMN status SET DEFAULT 'draft';
ALTER TABLE public.event_causality ADD COLUMN status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published'));
ALTER TABLE public.event_causality ALTER COLUMN status SET DEFAULT 'draft';
ALTER TABLE public.fact_claim ADD COLUMN status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published'));
ALTER TABLE public.fact_claim ALTER COLUMN status SET DEFAULT 'draft';
DROP POLICY "Allow public read access on person" ON public.person;
CREATE POLICY "Allow public read access on person" ON public.person FOR SELECT USING (status = 'published');
DROP POLICY "Allow public read access on event" ON public.event;
CREATE POLICY "Allow public read access on event" ON public.event FOR SELECT USING (status = 'published');
DROP POLICY "Allow public read access on person_relationship" ON public.person_relationship;
CREATE POLICY "Allow public read access on person_relationship" ON public.person_relationship FOR SELECT USING (
 status = 'published' AND EXISTS (SELECT 1 FROM public.person WHERE id = person_a AND status = 'published')
 AND EXISTS (SELECT 1 FROM public.person WHERE id = person_b AND status = 'published'));
DROP POLICY "Allow public read access on person_event" ON public.person_event;
CREATE POLICY "Allow public read access on person_event" ON public.person_event FOR SELECT USING (
 status = 'published' AND EXISTS (SELECT 1 FROM public.person WHERE id = person_id AND status = 'published')
 AND EXISTS (SELECT 1 FROM public.event WHERE id = event_id AND status = 'published'));
DROP POLICY "Allow public read access on event_causality" ON public.event_causality;
CREATE POLICY "Allow public read access on event_causality" ON public.event_causality FOR SELECT USING (
 status = 'published' AND EXISTS (SELECT 1 FROM public.event WHERE id = cause_event_id AND status = 'published')
 AND EXISTS (SELECT 1 FROM public.event WHERE id = effect_event_id AND status = 'published'));

CREATE FUNCTION public.claim_subject_visible(subject text, target uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
 SELECT CASE subject
 WHEN 'person' THEN EXISTS (SELECT 1 FROM person WHERE id = target AND status = 'published')
 WHEN 'event' THEN EXISTS (SELECT 1 FROM event WHERE id = target AND status = 'published')
 WHEN 'person_relationship' THEN EXISTS (SELECT 1 FROM person_relationship WHERE id = target AND status = 'published')
 WHEN 'person_event' THEN EXISTS (SELECT 1 FROM person_event WHERE id = target AND status = 'published')
 WHEN 'event_causality' THEN EXISTS (SELECT 1 FROM event_causality WHERE id = target AND status = 'published')
 ELSE false END;
$$;
DROP POLICY "Allow public read access on fact_claim" ON public.fact_claim;
CREATE POLICY "Allow public read access on fact_claim" ON public.fact_claim FOR SELECT
 USING (status = 'published' AND public.claim_subject_visible(subject_table, subject_id));
CREATE TABLE public.topic (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 slug text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
 title text NOT NULL,
 description text NOT NULL DEFAULT '',
 sections jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(sections) = 'array'),
 status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
 created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.topic ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public published topics" ON public.topic FOR SELECT USING (status = 'published');
CREATE POLICY "Admin topics" ON public.topic FOR ALL USING (public.is_admin()) WITH CHECK (public.is_admin());
COMMIT;
