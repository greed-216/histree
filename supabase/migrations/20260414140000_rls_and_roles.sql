-- Create user roles table to manage admins
CREATE TABLE IF NOT EXISTS public.user_roles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'user')) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Helper function to check if current user is admin
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.user_roles
        WHERE user_id = auth.uid() AND role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable RLS on all business tables
ALTER TABLE public.person ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.person_relationship ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.person_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_causality ENABLE ROW LEVEL SECURITY;

-- Policies for public.person
DROP POLICY IF EXISTS "Allow public read access on person" ON public.person;
DROP POLICY IF EXISTS "Allow admin write access on person" ON public.person;
CREATE POLICY "Allow public read access on person" ON public.person FOR SELECT USING (true);
CREATE POLICY "Allow admin write access on person" ON public.person FOR ALL USING (public.is_admin());

-- Policies for public.event
DROP POLICY IF EXISTS "Allow public read access on event" ON public.event;
DROP POLICY IF EXISTS "Allow admin write access on event" ON public.event;
CREATE POLICY "Allow public read access on event" ON public.event FOR SELECT USING (true);
CREATE POLICY "Allow admin write access on event" ON public.event FOR ALL USING (public.is_admin());

-- Policies for public.person_relationship
DROP POLICY IF EXISTS "Allow public read access on person_relationship" ON public.person_relationship;
DROP POLICY IF EXISTS "Allow admin write access on person_relationship" ON public.person_relationship;
CREATE POLICY "Allow public read access on person_relationship" ON public.person_relationship FOR SELECT USING (true);
CREATE POLICY "Allow admin write access on person_relationship" ON public.person_relationship FOR ALL USING (public.is_admin());

-- Policies for public.person_event
DROP POLICY IF EXISTS "Allow public read access on person_event" ON public.person_event;
DROP POLICY IF EXISTS "Allow admin write access on person_event" ON public.person_event;
CREATE POLICY "Allow public read access on person_event" ON public.person_event FOR SELECT USING (true);
CREATE POLICY "Allow admin write access on person_event" ON public.person_event FOR ALL USING (public.is_admin());

-- Policies for public.event_causality
DROP POLICY IF EXISTS "Allow public read access on event_causality" ON public.event_causality;
DROP POLICY IF EXISTS "Allow admin write access on event_causality" ON public.event_causality;
CREATE POLICY "Allow public read access on event_causality" ON public.event_causality FOR SELECT USING (true);
CREATE POLICY "Allow admin write access on event_causality" ON public.event_causality FOR ALL USING (public.is_admin());
