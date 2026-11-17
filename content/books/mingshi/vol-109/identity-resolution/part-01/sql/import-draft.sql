BEGIN;

SET LOCAL standard_conforming_strings = on;

INSERT INTO public.source (id, title, source_type, author, edition, url, note)
SELECT id, title, source_type, author, edition, url, note FROM jsonb_populate_recordset(NULL::public.source, '[{"title": "明史·卷134·卷一百三十四·mingshi-2f603db3d81e-p021794", "source_type": "primary", "author": null, "edition": "选定电子TXT逐字快照；已核本次上下文，纸本及异文未全面校核。", "url": "https://github.com/greed-216/histree/blob/190e5fec5eba910aa2c04bd2e7dcb23864aebe38/content/books/mingshi/vol-109/identity-resolution/part-01/sources/mingshi-2f603db3d81e-p021794/source.txt", "note": "《明史》卷一百三十四，段落 mingshi-2f603db3d81e-p021794；EPUB电子本，纸本及异文待核", "id": "1c0dacbe-53e7-579e-98cb-5d90ae793afe"}]'::jsonb)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.person (id, name, aliases, era, birth_year, death_year, description, biography, status)
SELECT id, name, aliases, era, birth_year, death_year, description, biography, status FROM jsonb_populate_recordset(NULL::public.person, '[{"name": "王溥（陈友谅建昌守将）", "aliases": [], "era": "元末", "birth_year": null, "death_year": null, "description": "陈平章，守建昌后降吴。", "biography": null, "status": "draft", "id": "8106f6d1-94c7-56af-ba58-48f6cb1b7b4d"}]'::jsonb)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.event (id, title, start_year, end_year, time_original, dynasty, description, phases, location_name, location_modern_name, location_lat, location_lng, location_precision, location_note, status)
SELECT id, title, start_year, end_year, time_original, dynasty, description, phases, location_name, location_modern_name, location_lat, location_lng, location_precision, location_note, status FROM jsonb_populate_recordset(NULL::public.event, '[{"title": "朱元璋设朝臣兼任东宫官，不采用元太子中书令制", "description": "周宗请求重视教导太子，获准。中书省、都督府请仿元制，以太子为中书令，朱元璋拒绝，命詹同考察历代制度，由李善长、徐达、常遇春等兼任东宫官，以免另设府僚后发生嫌隙。", "start_year": 1368, "end_year": 1368, "time_original": "《续资治通鉴》卷220；本事原载纪年折合公元1368年，具体月日依引文。", "dynasty": "元及同时诸政权", "location_name": null, "location_lat": null, "location_lng": null, "location_precision": "unknown", "location_modern_name": null, "location_note": null, "status": "draft", "id": "f470c02c-e216-5c59-a88b-e84faa1d2611"}]'::jsonb)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.person_event (id, person_id, event_id, role, status)
SELECT id, person_id, event_id, role, status FROM jsonb_populate_recordset(NULL::public.person_event, '[{"role": "兼任副詹事", "status": "draft", "id": "8d381080-1d31-5f01-b352-77e994dc11b8", "person_id": "8106f6d1-94c7-56af-ba58-48f6cb1b7b4d", "event_id": "f470c02c-e216-5c59-a88b-e84faa1d2611"}]'::jsonb)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.fact_claim (id, subject_table, subject_id, field_path, claim_text, source_id, citation, note, status)
SELECT id, subject_table, subject_id, field_path, claim_text, source_id, citation, note, status FROM jsonb_populate_recordset(NULL::public.fact_claim, '[{"subject_table": "person", "field_path": "biography", "claim_text": "洪武元年，中书右丞王溥兼任詹事府副詹事；本书附传将他明确承接为此前陈友谅的建昌守将。", "citation": "《明史》卷134·卷一百三十四·mingshi-2f603db3d81e-p021794；洪武元年，即1368年；仅补证卷109待考身份，不推进卷134连续录入。", "note": "原文：從克武昌，進中書右丞。洪武元年，命兼詹事府副詹事。；核对说明：同书王溥附传明确连接陈友谅建昌守将、降附后中书右丞和洪武元年副詹事；排除晚唐、后周宋初同名王溥及洪武末桂林籍广东参政。", "status": "draft", "id": "4e3bbd4f-76b7-54e0-948c-4bd121b29a1e", "subject_id": "8106f6d1-94c7-56af-ba58-48f6cb1b7b4d", "source_id": "1c0dacbe-53e7-579e-98cb-5d90ae793afe"}, {"subject_table": "event", "field_path": "description", "claim_text": "洪武元年朝臣兼任东宫官的安排中，王溥以中书右丞兼任副詹事。", "citation": "《明史》卷134·卷一百三十四·mingshi-2f603db3d81e-p021794；洪武元年，即1368年；仅补证卷109待考身份，不推进卷134连续录入。", "note": "原文：從克武昌，進中書右丞。洪武元年，命兼詹事府副詹事。；核对说明：同书王溥附传明确连接陈友谅建昌守将、降附后中书右丞和洪武元年副詹事；排除晚唐、后周宋初同名王溥及洪武末桂林籍广东参政。", "status": "draft", "id": "8ff4cc02-33a9-5c81-bc67-9e73b44a3a5c", "subject_id": "f470c02c-e216-5c59-a88b-e84faa1d2611", "source_id": "1c0dacbe-53e7-579e-98cb-5d90ae793afe"}, {"subject_table": "person_event", "field_path": "role", "claim_text": "王溥兼任詹事府副詹事。", "citation": "《明史》卷134·卷一百三十四·mingshi-2f603db3d81e-p021794；洪武元年，即1368年；仅补证卷109待考身份，不推进卷134连续录入。", "note": "原文：從克武昌，進中書右丞。洪武元年，命兼詹事府副詹事。；核对说明：同书王溥附传明确连接陈友谅建昌守将、降附后中书右丞和洪武元年副詹事；排除晚唐、后周宋初同名王溥及洪武末桂林籍广东参政。", "status": "draft", "id": "3a4432c3-9417-5af5-aa7c-425700a4cfa3", "subject_id": "8d381080-1d31-5f01-b352-77e994dc11b8", "source_id": "1c0dacbe-53e7-579e-98cb-5d90ae793afe"}]'::jsonb)
ON CONFLICT (id) DO NOTHING;

COMMIT;
