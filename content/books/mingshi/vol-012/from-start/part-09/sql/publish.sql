BEGIN;


UPDATE public.event SET status='published' WHERE id IN ('6f255b72-31a3-5f70-bd0a-d7862a61c73c','2e29517b-486b-564d-85f3-9aca0e981fa0','f237b1b5-a22b-5920-ad74-60670fc1d1db','5bdf8e1a-0acf-500d-b2e8-6a29ce39df3a','ed643588-6618-5b22-aedc-e05aa0d01665','aac54348-0628-5a7b-83cb-97819af70f24');

UPDATE public.person_event SET status='published' WHERE id IN ('8a995724-ac12-587a-a6c0-5898d1ef05c5','79304672-1ad4-5e12-886c-d62799b360f1','a409ed38-680e-5ab8-b257-b7addaf84000','c9c3ecb5-5e0b-5a4c-8b0c-a2bdbcb1f1d8','0d87f3e2-3bd5-5349-a4bc-9c8039aaee69','a1c7afe5-c798-5d27-a24e-7b149a823865');

UPDATE public.fact_claim SET status='published' WHERE id IN ('03be0909-94b5-5a81-bc33-484216bda83c','30043908-a863-58c2-9ea0-7e0ce4fd5762','85d6e105-03d9-5beb-98bc-27a3a59785b9','9aea65f8-c79c-523d-a230-2576fd4de8da','d2a2e9a6-e53b-5a6f-a1fa-4a00d5a17cac','74a3e51a-49a1-50b4-8280-0d9be4c9b312','cda329cf-091d-5aaa-a82f-77219c7fa31e','87ddb40b-75f3-5ba9-ab3d-e8d19a88087d','503e6686-c706-5b8d-bf6c-cd03fde92fed','c917af93-30b6-5cee-a3d8-347d2a0eade6','7b82ce9a-26c9-546f-9a85-1b4e0876dc88','d9641cd3-1e5b-5201-8181-96348b76dcd2','2c600002-1ed0-5904-9a00-fc021b0ce9f4','0da4e2c0-fe08-5cfc-bb12-f1167f998f27','2e8c56fd-28d9-5fb4-bbbe-203a0ea58686','47ca6015-0453-55fd-9b6e-a70a99154998','967633a4-765b-5f2b-b59f-e115af05c657','7b341536-b2a0-5d48-867e-afe1e9619598','78178b43-2c1b-560a-ac47-a8f3df69e2a5','bd7a927d-3e64-5fe0-a216-eed26e4c1847','ec1a3113-5ff2-5ea7-86a7-f5960d358e23','6a3f93cb-eb30-5c90-a56f-0df8b193d4ba','6a78c5be-5093-5d88-9a1a-cf5e0d2999c4','37eacf72-b656-5165-b719-34dab62600b9','5d2ee207-2b0d-587f-a167-07fb7be76bd6');

COMMIT;
