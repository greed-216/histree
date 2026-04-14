-- Drop existing tables if any
DROP TABLE IF EXISTS public.relationships CASCADE;
DROP TABLE IF EXISTS public.events CASCADE;
DROP TABLE IF EXISTS public.people CASCADE;

DROP TABLE IF EXISTS public.event_causality CASCADE;
DROP TABLE IF EXISTS public.person_event CASCADE;
DROP TABLE IF EXISTS public.person_relationship CASCADE;
DROP TABLE IF EXISTS public.event CASCADE;
DROP TABLE IF EXISTS public.person CASCADE;

-- Create Person Table
CREATE TABLE public.person (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    era TEXT,
    birth_year INT,
    death_year INT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create Event Table
CREATE TABLE public.event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    start_year INT,
    end_year INT,
    dynasty TEXT,
    description TEXT,
    impact_level INT CHECK (impact_level >= 1 AND impact_level <= 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create Person Relationship Table
CREATE TABLE public.person_relationship (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_a UUID NOT NULL REFERENCES public.person(id) ON DELETE CASCADE,
    person_b UUID NOT NULL REFERENCES public.person(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL, -- enemy / ally / ruler / minister
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX idx_person_rel_a ON public.person_relationship(person_a);
CREATE INDEX idx_person_rel_b ON public.person_relationship(person_b);

-- Create Person Event Table
CREATE TABLE public.person_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES public.person(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES public.event(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- commander / participant / etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX idx_person_event_p ON public.person_event(person_id);
CREATE INDEX idx_person_event_e ON public.person_event(event_id);

-- Create Event Causality Table
CREATE TABLE public.event_causality (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cause_event_id UUID NOT NULL REFERENCES public.event(id) ON DELETE CASCADE,
    effect_event_id UUID NOT NULL REFERENCES public.event(id) ON DELETE CASCADE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT no_self_causality CHECK (cause_event_id != effect_event_id)
);

CREATE INDEX idx_event_cause ON public.event_causality(cause_event_id);
CREATE INDEX idx_event_effect ON public.event_causality(effect_event_id);

-- Insert MVP Seed Data
-- Insert People
INSERT INTO public.person (id, name, era, description) VALUES
    ('00000000-0000-0000-0000-000000000001', '曹操', 'Three Kingdoms', '魏王'),
    ('00000000-0000-0000-0000-000000000002', '刘备', 'Three Kingdoms', '蜀汉昭烈帝'),
    ('00000000-0000-0000-0000-000000000003', '孙权', 'Three Kingdoms', '东吴大帝');

-- Insert Events
INSERT INTO public.event (id, title, start_year, end_year, dynasty, description, impact_level) VALUES
    ('00000000-0000-0000-0000-000000000004', '官渡之战', 200, 200, 'Eastern Han', '曹操大败袁绍', 4),
    ('00000000-0000-0000-0000-000000000005', '赤壁之战', 208, 208, 'Eastern Han', '孙刘联军大败曹操', 5);

-- Insert Person Relationships
INSERT INTO public.person_relationship (id, person_a, person_b, relation_type, description) VALUES
    ('00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'enemy', '曹操 vs 刘备'),
    ('00000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'enemy', '曹操 vs 孙权');

-- Insert Person Events
INSERT INTO public.person_event (id, person_id, event_id, role) VALUES
    ('00000000-0000-0000-0000-000000000008', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', 'commander'),
    ('00000000-0000-0000-0000-000000000009', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000005', 'commander'),
    ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000005', 'participant'),
    ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000005', 'commander');

-- Insert Event Causality
INSERT INTO public.event_causality (id, cause_event_id, effect_event_id, description) VALUES
    ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000005', '官渡之战奠定了曹操统一北方的基础，间接促成了南下赤壁之战');
