BEGIN;


UPDATE public.person_relationship SET status='published' WHERE id IN ('7e7fb224-983d-58b3-ae35-4c1b12b156eb','3d160930-c79d-51d8-afcd-890cf94f3343','d925d8e5-fff5-508f-8826-eb1dd4be4ac2','b18a9f04-6418-5cf4-9808-d02205a42e94','b1c43974-3702-5da4-81d6-fec4aee68724','a4ad9ea0-2ae7-5bef-b866-cf2c3533245f');

UPDATE public.fact_claim SET status='published' WHERE id IN ('c2bc114d-dd66-5ac3-8b56-2407e2a7f3c5','ba8a8c76-bced-59d0-be7f-ea472f2e1599','2097e3c8-a78f-5b6d-b231-80a679803b74','d6b203f4-5939-5179-a3fa-b0d55ba12ca4','0f4be387-3787-5acf-9bf6-8a925012f543','1ab303c9-295b-52a4-9ea6-d82d8ba3df58','a2af5c71-2be0-5b10-b900-8b5c1ab1940b','66e03738-7798-5fee-b772-93fbdfa8cd7b','2c953883-6a29-5699-b3c3-056b8c65fdcf','18551f82-3456-5f04-8f9d-7f37d368e0c2','ff9ba538-5beb-5822-bd9a-f170f13e5b9f','d200df78-96ed-59d9-af6b-5c9a9c4eda99','b3606da9-b4f1-5da8-9f37-55fd7fca9415','62281ca1-a594-55ac-98eb-142474056337','2f77bef8-1fa5-52a0-9dab-3cd50e26a81d');

COMMIT;
