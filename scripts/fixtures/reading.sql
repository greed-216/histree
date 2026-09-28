-- Fictional records for the in-memory PostgreSQL and mocked browser tests only.
-- This file is not a migration and must never be imported into Supabase.
INSERT INTO person(id,name,aliases,era,biography,status) VALUES
 ('11111111-1111-1111-1111-111111111008','测试人物甲',ARRAY['测试别名'],'测试时期','虚构的工程测试人物。','published'),
 ('11111111-1111-1111-1111-111111111009','测试人物乙','{}','测试时期','虚构的工程测试人物。','published');
INSERT INTO event(id,title,start_year,phases,status) VALUES
 ('22222222-2222-2222-2222-222222222007','测试事件甲',1,'[{"title":"测试阶段","description":"虚构阶段说明。","start_year":1}]','published'),
 ('22222222-2222-2222-2222-222222222008','测试事件乙',2,'[]','published');
INSERT INTO person_relationship(id,person_a,person_b,relation_type,description,status) VALUES
 ('33333333-3333-3333-3333-333333333003','11111111-1111-1111-1111-111111111008','11111111-1111-1111-1111-111111111009','ally','测试关系','published');
INSERT INTO person_event(person_id,event_id,role,status) VALUES
 ('11111111-1111-1111-1111-111111111008','22222222-2222-2222-2222-222222222007','participant','published');
INSERT INTO event_causality(cause_event_id,effect_event_id,description,status) VALUES
 ('22222222-2222-2222-2222-222222222007','22222222-2222-2222-2222-222222222008','虚构测试关系','published');
INSERT INTO source(id,title,source_type,url) VALUES
 ('66666666-6666-6666-6666-666666666001','测试文献','reference','https://example.org/test-source');
INSERT INTO fact_claim(subject_table,subject_id,field_path,claim_text,source_id,citation,status) VALUES
 ('person','11111111-1111-1111-1111-111111111008','biography','虚构人物陈述','66666666-6666-6666-6666-666666666001','测试文献·人物段','published'),
 ('person_relationship','33333333-3333-3333-3333-333333333003','description','虚构关系陈述','66666666-6666-6666-6666-666666666001','测试文献·关系段','published');
INSERT INTO topic(slug,title,status,sections) VALUES
 ('test-reading','测试阅读专题','published','[{"heading":"测试章节一","body":"虚构导读。","node_ids":["11111111-1111-1111-1111-111111111008","11111111-1111-1111-1111-111111111009"]},{"heading":"测试章节二","body":"虚构导读。","node_ids":["22222222-2222-2222-2222-222222222007"]},{"heading":"测试章节三","body":"虚构导读。","node_ids":["11111111-1111-1111-1111-111111111008"]}]');

UPDATE event SET location_name='测试地点甲', location_modern_name='虚构定位', location_lat=0, location_lng=0,
 location_precision='approximate', location_note='仅供隔离测试，不代表历史事实。', time_original='测试纪年'
 WHERE id='22222222-2222-2222-2222-222222222007';
INSERT INTO event(id,title,status) VALUES ('22222222-2222-2222-2222-222222222009','测试时间不详事件','published');
UPDATE topic SET sections=jsonb_set(sections,'{1,node_ids}', '["22222222-2222-2222-2222-222222222007","22222222-2222-2222-2222-222222222008","22222222-2222-2222-2222-222222222009"]');
