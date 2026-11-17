BEGIN;

UPDATE public.fact_claim SET status='draft' WHERE id IN ('4e3bbd4f-76b7-54e0-948c-4bd121b29a1e','8ff4cc02-33a9-5c81-bc67-9e73b44a3a5c','3a4432c3-9417-5af5-aa7c-425700a4cfa3');

UPDATE public.person_event SET status='draft' WHERE id IN ('8d381080-1d31-5f01-b352-77e994dc11b8');



COMMIT;
