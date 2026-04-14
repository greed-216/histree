-- Create People Table
CREATE TABLE public.people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    era TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create Events Table
CREATE TABLE public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    time_start INT NOT NULL,
    time_end INT NOT NULL,
    description TEXT,
    dynasty TEXT,
    impact_level INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create Relationships Table
CREATE TABLE public.relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source UUID NOT NULL,
    target UUID NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Insert some mock data
INSERT INTO public.people (id, name, era, description) VALUES
    ('00000000-0000-0000-0000-000000000001', 'Liu Bei', 'Three Kingdoms', 'Founder of Shu Han'),
    ('00000000-0000-0000-0000-000000000002', 'Zhuge Liang', 'Three Kingdoms', 'Chancellor of Shu Han');

INSERT INTO public.events (id, title, time_start, time_end, description, dynasty, impact_level) VALUES
    ('00000000-0000-0000-0000-000000000003', 'Battle of Red Cliffs', 208, 208, 'Decisive battle at the end of the Han dynasty', 'Eastern Han', 10);

INSERT INTO public.relationships (id, source, target, type, description) VALUES
    ('00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'ruler', 'Liu Bei recruited Zhuge Liang'),
    ('00000000-0000-0000-0000-000000000005', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003', 'participant', 'Zhuge Liang planned the alliance'),
    ('00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'participant', 'Liu Bei led allied forces');
