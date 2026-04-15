-- Add image and location fields
ALTER TABLE public.person ADD COLUMN image_url TEXT;
ALTER TABLE public.event ADD COLUMN image_url TEXT;
ALTER TABLE public.event ADD COLUMN location_lat DOUBLE PRECISION;
ALTER TABLE public.event ADD COLUMN location_lng DOUBLE PRECISION;
ALTER TABLE public.event ADD COLUMN location_name TEXT;

-- Update seed data with some sample images and locations
UPDATE public.person SET image_url = 'https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=portrait%20of%20Cao%20Cao%20Three%20Kingdoms%20chinese%20historical%20figure&image_size=square' WHERE name = '曹操';
UPDATE public.person SET image_url = 'https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=portrait%20of%20Liu%20Bei%20Three%20Kingdoms%20chinese%20historical%20figure&image_size=square' WHERE name = '刘备';
UPDATE public.person SET image_url = 'https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=portrait%20of%20Sun%20Quan%20Three%20Kingdoms%20chinese%20historical%20figure&image_size=square' WHERE name = '孙权';

UPDATE public.event 
SET image_url = 'https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=ancient%20chinese%20battlefield%20Guandu%20river&image_size=landscape_16_9',
    location_name = '官渡 (今河南中牟)', location_lat = 34.71, location_lng = 114.02
WHERE title = '官渡之战';

UPDATE public.event 
SET image_url = 'https://coresg-normal.trae.ai/api/ide/v1/text_to_image?prompt=ancient%20chinese%20naval%20battle%20fire%20ships%20Chibi%20Yangtze%20river&image_size=landscape_16_9',
    location_name = '赤壁 (今湖北赤壁市)', location_lat = 29.72, location_lng = 113.62
WHERE title = '赤壁之战';
