BEGIN;


UPDATE public.event SET status='published' WHERE id IN ('a112dc41-df1a-5710-bfac-008ba733a172','ed8e2b8c-6c08-5888-94a6-1d97e2dbc7b8','cd18f36c-2e08-5bc8-bb30-2e0a067764ff','2aefdbd9-2b4d-5ca8-a985-99fc0f244ace','e3241f26-bccb-554b-9be2-12ee4815010a');

UPDATE public.person_event SET status='published' WHERE id IN ('cfbc0767-7612-591d-999e-912d466ec7a6','2612b0a9-9e03-5e0f-966c-4e7265d8d2fb','bc9bf735-c6a7-5666-b82d-92377e0b9792','3a9a2fbd-c4e0-5cb0-a2b8-d2f373f7d769');

UPDATE public.fact_claim SET status='published' WHERE id IN ('e5e381d3-d058-5e31-bccf-576f8d4eb731','b54dd9e1-131c-55e9-b433-ce3fe9d4caba','5f587eb1-df92-5a5b-8e00-fba444929dca','79fb489b-7a9a-5908-ab5b-0bfe1eedf686','c4a27ed8-68d9-5922-a3c3-01f5e801a73d','67179fdb-3c55-5db6-a5b7-fdb29ffde5b2','798614eb-c711-50c7-9e51-28d048b9a8fe','eff1b960-4d00-5b7b-8db9-7a23fb9b8561','6feb9f59-49c5-5b8b-a5fe-afbbe0a82cc0','799a1554-ea33-516c-a2e3-3ac8d81e3652','1c747453-68fe-51ac-a0ab-afca208f3bc4','32810f6d-0e73-56cb-9ad3-04111cb88fa0','8edabc67-22a5-5b83-9db9-517e5e2aea9d','e2333e8f-aa95-5212-bcd1-34f222461dfe','33522cdb-bd4a-54c9-a053-cb64d5d29cf3','f164406d-3e94-5d38-8272-5ac48c8f49f9','007b3feb-7c4b-5df6-be73-2336882fae54','b234f700-b655-5f9c-82e6-ac9db8a99d48','f7158ab0-2d61-50a4-b80f-288eea0ff948','61cee2bd-9223-549d-9d6e-dc812a8c930a','af6ee721-e99e-5346-8603-c2a181af4d93');

COMMIT;
