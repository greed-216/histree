BEGIN;

UPDATE public.fact_claim SET status='draft' WHERE id IN ('c353a696-6ce4-5124-b308-d0797a84cea8','7e429ad0-eaca-579f-8837-fcc6b077632e','fa9a1c2d-7888-5a72-bfdc-623e85cb0856','59e2ab03-4b12-5ca0-ae94-f272d4448896','79908619-54ae-5d13-9bfe-5573fd5f4d3a','4caaae77-2f3e-52ab-8d80-9e1591e29920','329dafe4-1693-5c9e-b8e8-1baffbc18151','af65dd94-7a96-53c6-bc25-4e284c49630d','37b26a51-5ee1-59ed-9e5a-ec345bd40822','28c77bc5-2729-5ccb-b064-82c8760314f6','59ce126a-6da3-533d-93f7-a4640260ac0d','6ac0470d-1b9f-5788-bf0c-d910edb82ece','12005f97-cece-5788-924b-26d1e869383f','0f4f3454-813c-5182-aec7-4c34fb6b73f7','cf6446a4-b523-57ec-a171-a44054acc436','c30131d4-b692-56e5-8a02-cc3bae2251d3','692110a9-2928-5cf8-8367-9e978859536c','7c2dd51d-8098-51d6-99c4-7fae50502a88','8e164967-33bf-5f93-92a2-b9ab4449de92','f5f35f49-7276-5b1e-bbb4-72b86a2e37ed','862e56df-e7ca-597f-bb2c-c09bc85d1110','1dff4467-14fe-571a-9b5c-1bd713d46ea3','fd8b57c4-996a-5f3f-9a32-55d30f888f1e','2c1d5ef0-a5e8-508f-aff4-674b64840e8b','6e24b365-99b7-5fa9-931d-f99408eb1924','9236133c-4567-5606-a532-eb2ab3e2f798','5734b24b-f76d-5ea1-b697-7044ccd65e8c','2d137a14-604a-54b9-8074-dbd83094f2f6','288261e6-8de2-5f4a-82f5-0c7965b3ef9f','88fc9fb2-b2f7-5c20-8861-3ffc76cbacd3','ad007f4e-5e98-5dc7-9124-efe78bccd7c1');

UPDATE public.person_event SET status='draft' WHERE id IN ('e91c1803-e2fc-51b3-917d-550e6deedaea','5f6f353f-9466-5069-aa31-903fca2276ce','5b111eee-35ba-567f-b2f1-e1d1a7cec24c','900f4e6a-19cb-559e-82ab-6b5418f8a16d','90cb23c3-9573-5602-a347-54d652032010','f4d7de62-1997-5e10-b8f4-c9fc271d78e7','0cd693fd-05a7-5b4f-880f-0ea8b5952137','05f7ab25-c0ea-5bdd-b60c-d73a4d234f9d','ecb09f8b-00bf-5ebf-b5fb-08206406e46e','0a7c5216-6c47-5479-a4c7-e5edb9972fb2','65adb44f-f1c4-54ca-879a-4a9b8ad7aaf8');

UPDATE public.person_relationship SET status='draft' WHERE id IN ('71b3be44-e86d-5efb-9d63-c5ed0d66b1a3');

UPDATE public.event SET status='draft' WHERE id IN ('f8d3bdf1-4f10-558d-9683-51dfa31a521e','1cd352fc-d005-52aa-8c37-7cc31cc4b732','82dce540-f988-5e92-ab05-8757a75564c5','ff78c2f9-5d85-5a2e-a354-93e550fbdce1','94e0f277-fb51-5429-a804-188680ae538c');

UPDATE public.person SET status='draft' WHERE id IN ('97d5fbe2-1ee3-599c-ac3f-6a94cdb85a87','39b8e4a2-9d5a-51ab-9298-41ab7114800a');

COMMIT;
