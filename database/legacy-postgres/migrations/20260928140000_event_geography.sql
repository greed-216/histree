BEGIN;
ALTER TABLE public.event
  ADD COLUMN time_original text,
  ADD COLUMN location_modern_name text,
  ADD COLUMN location_precision text NOT NULL DEFAULT 'unknown'
    CHECK (location_precision IN ('site','approximate','region','unknown')),
  ADD COLUMN location_note text,
  ADD CONSTRAINT event_coordinate_pair CHECK ((location_lat IS NULL) = (location_lng IS NULL)),
  ADD CONSTRAINT event_latitude_range CHECK (location_lat BETWEEN -90 AND 90),
  ADD CONSTRAINT event_longitude_range CHECK (location_lng BETWEEN -180 AND 180),
  ADD CONSTRAINT event_year_range CHECK (start_year IS NULL OR end_year IS NULL OR start_year <= end_year);
COMMIT;
