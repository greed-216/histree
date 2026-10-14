BEGIN;

UPDATE public.fact_claim SET status='draft' WHERE id IN ('63b7b8b2-1273-509e-87fc-7fd0209c5a4d','d7d4e5c3-6d7a-569a-ba7d-e322de308f06','21de7a8d-dd52-5fde-a4ec-3d4b1e065cc7','ce69183d-398c-5dc6-b344-4288a60dd47c','f13c825f-66b8-5be3-bc64-556096b1c14d','7d43db81-67e0-50d8-9c12-956bcd266285','16a341ff-90e3-51d2-b54c-bd89e4f64b12','5c0e6f6b-bea9-5c3e-95a6-4bf107eadeb5','2b14b38f-3031-5c35-ace6-8d573fd3f892','c680c2ee-16e9-5681-a8ab-a962371ca099','00704658-631c-50b6-9e91-015d98edff0b','e35bec0e-17c9-5fb0-8e28-e84067a08639','e4fabb87-2b8d-556e-8481-680b6ea24243','b83b6eb9-d3a2-5fb6-a7e4-57ceede3815b','74873bd4-b0a4-5e5b-8857-b5c8fab5460e','396132fc-a8cd-56ae-bcb1-c38344fb85d7','6172dde7-75b2-5cdb-ba49-cd36d9b9f909','b853a5b3-6185-548b-8779-29ed1eace461','b1e4144e-23e9-598d-a7f1-af20af4f7809','35ad2cd4-2f7a-543a-b279-f3326ea21adf');

UPDATE public.person_event SET status='draft' WHERE id IN ('6844f56b-5998-59d4-8ad7-922c746ec03e','f20e5317-365f-5ab3-a987-2f039bc91b22','481272f6-5d4b-5b9f-9ebf-5d066b028069','8bfad03f-95f3-5407-a044-e5cb6fcc8d0d');

UPDATE public.event SET status='draft' WHERE id IN ('88309f5d-4302-5431-97c9-98505a221fdf');


COMMIT;
