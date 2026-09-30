BEGIN;
SET LOCAL search_path=public,extensions;
CREATE FUNCTION public.histree_topic_nodes(sections jsonb) RETURNS uuid[] LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
 SELECT coalesce(array_agg(DISTINCT node.value::uuid),'{}'::uuid[]) FROM jsonb_array_elements(sections) section CROSS JOIN LATERAL jsonb_array_elements_text(section->'node_ids') node(value);
$$;
CREATE INDEX topic_nodes_gin ON public.topic USING gin(public.histree_topic_nodes(sections)) WHERE status='published';
CREATE INDEX event_published_order ON public.event(start_year,id) WHERE status='published';
CREATE INDEX person_directory_order ON public.person(created_at DESC,id) WHERE status='published';
CREATE INDEX claims_subject_page ON public.fact_claim(subject_table,subject_id,id) WHERE status='published';
CREATE INDEX claims_source_page ON public.fact_claim(source_id,id) WHERE status='published';
CREATE INDEX claims_search_trgm ON public.fact_claim USING gin((lower(claim_text||' '||coalesce(note,''))) gin_trgm_ops);

CREATE OR REPLACE FUNCTION public.claim_subject_visible(subject text,target uuid) RETURNS boolean LANGUAGE sql STABLE SECURITY INVOKER SET search_path=public AS $$
 SELECT CASE subject
 WHEN 'person' THEN EXISTS(SELECT 1 FROM person WHERE id=target AND status='published')
 WHEN 'event' THEN EXISTS(SELECT 1 FROM event WHERE id=target AND status='published')
 WHEN 'person_relationship' THEN EXISTS(SELECT 1 FROM person_relationship r JOIN person a ON a.id=r.person_a AND a.status='published' JOIN person b ON b.id=r.person_b AND b.status='published' WHERE r.id=target AND r.status='published')
 WHEN 'person_event' THEN EXISTS(SELECT 1 FROM person_event r JOIN person p ON p.id=r.person_id AND p.status='published' JOIN event e ON e.id=r.event_id AND e.status='published' WHERE r.id=target AND r.status='published')
 WHEN 'event_causality' THEN EXISTS(SELECT 1 FROM event_causality r JOIN event a ON a.id=r.cause_event_id AND a.status='published' JOIN event b ON b.id=r.effect_event_id AND b.status='published' WHERE r.id=target AND r.status='published')
 ELSE false END;
$$;
CREATE FUNCTION public.topic_detail(p_id uuid) RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path=public AS $$ SELECT to_jsonb(t) FROM topic t WHERE id=p_id AND status='published' $$;
CREATE FUNCTION public.content_label(p_table text,r jsonb) RETURNS text LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=public AS $$
DECLARE a text; b text;
BEGIN
 IF p_table IN ('person','event','topic','source','nodes') THEN RETURN coalesce(r->>'name',r->>'title',r->>'id'); END IF;
 IF p_table='fact_claim' THEN RETURN left(r->>'claim_text',120); END IF;
 IF p_table='person_relationship' THEN
 SELECT name INTO a FROM person WHERE id=(r->>'person_a')::uuid; SELECT name INTO b FROM person WHERE id=(r->>'person_b')::uuid;
 RETURN coalesce(a,'人物')||' —'||(r->>'relation_type')||'→ '||coalesce(b,'人物');
 ELSIF p_table='person_event' THEN
 SELECT name INTO a FROM person WHERE id=(r->>'person_id')::uuid; SELECT title INTO b FROM event WHERE id=(r->>'event_id')::uuid;
 RETURN coalesce(a,'人物')||' —'||(r->>'role')||'→ '||coalesce(b,'事件');
 ELSE
 SELECT title INTO a FROM event WHERE id=(r->>'cause_event_id')::uuid; SELECT title INTO b FROM event WHERE id=(r->>'effect_event_id')::uuid;
 RETURN coalesce(a,'事件')||' → '||coalesce(b,'事件');
 END IF;
END;
$$;

CREATE FUNCTION public.content_page(p_table text,p_page integer DEFAULT 0,p_limit integer DEFAULT 20,p_query text DEFAULT '',p_admin boolean DEFAULT false,
 p_ids uuid[] DEFAULT NULL,p_topic text DEFAULT NULL,p_section integer DEFAULT NULL,p_person uuid DEFAULT NULL,p_from integer DEFAULT NULL,p_to integer DEFAULT NULL,
 p_subject text DEFAULT NULL,p_subject_id uuid DEFAULT NULL,p_source uuid DEFAULT NULL,p_claim uuid DEFAULT NULL,p_node uuid DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=public AS $$
DECLARE query text; condition text:='true'; ordering text; projection text; result jsonb; labels jsonb:='{}'; scope uuid[]; section_ids jsonb;
 size integer:=least(50,greatest(1,p_limit)); pattern text; item jsonb; target uuid; title text;
BEGIN
 IF p_table NOT IN ('person','event','nodes','topic','source','fact_claim','person_relationship','person_event','event_causality') OR p_page<0 OR p_page>100000 OR length(p_query)>200
 OR (p_from IS NOT NULL AND p_to IS NOT NULL AND p_from>p_to) OR (p_ids IS NOT NULL AND cardinality(p_ids)>200) OR p_section<0 THEN
 RAISE EXCEPTION 'Invalid content query' USING ERRCODE='22023'; END IF;
 IF p_admin AND current_user NOT IN ('service_role','postgres') AND NOT public.is_admin() THEN RAISE EXCEPTION 'Admin required' USING ERRCODE='42501'; END IF;
 IF NOT p_admin AND p_table='source' AND p_ids IS NULL THEN RAISE EXCEPTION 'Source list requires admin' USING ERRCODE='42501'; END IF;
 IF p_topic IS NOT NULL THEN
 SELECT CASE WHEN p_section IS NULL THEN to_jsonb(public.histree_topic_nodes(sections)) ELSE sections->p_section->'node_ids' END INTO section_ids FROM topic WHERE slug=p_topic AND (p_admin OR status='published');
 IF section_ids IS NULL THEN scope:='{}'; ELSE SELECT coalesce(array_agg(value::uuid),'{}'::uuid[]) INTO scope FROM jsonb_array_elements_text(section_ids); END IF;
 END IF;
 IF p_table='nodes' THEN query:='(SELECT to_jsonb(p)||jsonb_build_object(''type'',''person'') doc,p.id,p.status,p.created_at FROM person p UNION ALL SELECT to_jsonb(e)||jsonb_build_object(''type'',''event'') doc,e.id,e.status,e.created_at FROM event e) r';
 ELSE query:=format('(SELECT t.*,to_jsonb(t) doc%s FROM public.%I t) r',CASE WHEN p_table='source' THEN ',''published''::text status' ELSE '' END,p_table); END IF;
 IF NOT p_admin THEN condition:=condition||' AND r.status=''published'''; END IF;
 IF NOT p_admin AND p_table IN ('person_relationship','person_event','event_causality') THEN condition:=condition||format(' AND public.claim_subject_visible(%L,r.id)',p_table); END IF;
 IF p_ids IS NOT NULL THEN condition:=condition||format(' AND r.id=ANY(%L::uuid[])',p_ids); END IF;
 IF scope IS NOT NULL THEN
 condition:=condition||format(' AND r.id=ANY(%L::uuid[])',scope);
 END IF;
 IF p_node IS NOT NULL AND p_table='topic' THEN condition:=condition||format(' AND public.histree_topic_nodes(r.sections) @> ARRAY[%L::uuid]',p_node); END IF;
 IF p_person IS NOT NULL AND p_table='event' THEN condition:=condition||format(' AND EXISTS(SELECT 1 FROM person_event pe JOIN person p ON p.id=pe.person_id WHERE pe.event_id=r.id AND pe.person_id=%L::uuid AND pe.status=''published'' AND p.status=''published'')',p_person); END IF;
 IF p_table='event' THEN
 IF p_from IS NOT NULL THEN condition:=condition||format(' AND (r.start_year IS NULL OR coalesce(r.end_year,r.start_year)>=%s)',p_from); END IF;
 IF p_to IS NOT NULL THEN condition:=condition||format(' AND (r.start_year IS NULL OR r.start_year<=%s)',p_to); END IF;
 END IF;
 IF p_table='fact_claim' THEN
 IF p_subject IS NOT NULL THEN condition:=condition||format(' AND r.subject_table=%L',p_subject); END IF;
 IF p_subject_id IS NOT NULL THEN condition:=condition||format(' AND r.subject_id=%L::uuid',p_subject_id); END IF;
 IF p_source IS NOT NULL THEN condition:=condition||format(' AND r.source_id=%L::uuid',p_source); END IF;
 IF p_claim IS NOT NULL THEN condition:=condition||format(' AND r.id=%L::uuid',p_claim); END IF;
 IF NOT p_admin THEN condition:=condition||' AND public.claim_subject_visible(r.subject_table,r.subject_id)'; END IF;
 END IF;
 IF p_query<>'' THEN
 pattern:='%'||replace(replace(replace(lower(btrim(p_query)),E'\\',E'\\\\'),'%',E'\\%'),'_',E'\\_')||'%';
 IF p_table='person' THEN condition:=condition||format(' AND public.histree_person_search(r.name,r.aliases,r.era,r.faction,r.tags,r.description) LIKE %L',pattern);
 ELSIF p_table='event' THEN condition:=condition||format(' AND public.histree_event_search(r.title,r.dynasty,r.tags,r.description) LIKE %L',pattern);
 ELSIF p_table='topic' THEN condition:=condition||format(' AND lower(r.title||'' ''||r.description) LIKE %L',pattern);
 ELSE
 condition:=condition||format(' AND lower(public.content_label(%L,r.doc)||'' ''||coalesce(r.doc->>''description'','''')||'' ''||coalesce(r.doc->>''aliases'','''')||'' ''||coalesce(r.doc->>''tags'','''')||'' ''||coalesce(r.doc->>''citation'','''')) LIKE %L',p_table,pattern);
 END IF;
 END IF;
 ordering:=CASE WHEN p_table='event' THEN 'r.start_year NULLS LAST,r.id' WHEN scope IS NOT NULL AND p_section IS NOT NULL THEN format('array_position(%L::uuid[],r.id),r.id',scope) ELSE 'r.created_at DESC,r.id' END;
 projection:='r.doc';
 IF NOT p_admin THEN
 projection:='(r.doc - ''biography'' - ''historical_evaluation'' - ''family'' - ''social_relations'' - ''references'')';
 IF p_table IN ('person','event','nodes','topic') THEN projection:=projection||' || jsonb_build_object(''description'',left(r.doc->>''description'',600))'; END IF;
 IF p_table='topic' THEN projection:='(r.doc - ''sections'') || jsonb_build_object(''description'',left(r.doc->>''description'',600),''section_count'',jsonb_array_length(r.doc->''sections''))'; END IF;
 END IF;
 IF p_table IN ('person','event') THEN projection:=projection||format(' || jsonb_build_object(''type'',%L)',p_table); END IF;
 IF p_table='fact_claim' THEN projection:=projection||' || jsonb_build_object(''source'',(SELECT to_jsonb(s) FROM source s WHERE s.id=r.source_id))'; END IF;
 projection:='('||projection||') || jsonb_build_object(''label'',public.content_label('||quote_literal(p_table)||',r.doc))';
 EXECUTE format('SELECT coalesce(jsonb_agg(item ORDER BY ord),''[]'') FROM (SELECT item,row_number() OVER() ord FROM (SELECT %s item FROM %s WHERE %s ORDER BY %s LIMIT %s OFFSET %s) bounded) page',projection,query,condition,ordering,size+1,p_page*size) INTO result;
 FOR item IN SELECT value FROM jsonb_array_elements(result) LOOP
   FOREACH target IN ARRAY ARRAY[(item->>'person_a')::uuid,(item->>'person_b')::uuid,(item->>'person_id')::uuid,(item->>'event_id')::uuid,(item->>'cause_event_id')::uuid,(item->>'effect_event_id')::uuid,(item->>'source_id')::uuid] LOOP
     IF target IS NULL THEN CONTINUE; END IF;
     SELECT name INTO title FROM person WHERE id=target;
     IF title IS NULL THEN SELECT e.title INTO title FROM event e WHERE id=target; END IF;
     IF title IS NULL THEN SELECT s.title INTO title FROM source s WHERE id=target; END IF;
     IF title IS NOT NULL THEN labels:=labels||jsonb_build_object(target::text,title); END IF;
   END LOOP;
   IF p_table='fact_claim' AND item->>'subject_table' IN ('person','event','person_relationship','person_event','event_causality') THEN
     EXECUTE format('SELECT public.content_label(%L,to_jsonb(t)) FROM public.%I t WHERE id=%L::uuid',item->>'subject_table',item->>'subject_table',item->>'subject_id') INTO title;
     IF title IS NOT NULL THEN labels:=labels||jsonb_build_object(item->>'subject_id',title); END IF;
   END IF;
 END LOOP;
 RETURN jsonb_build_object('items',(SELECT coalesce(jsonb_agg(value ORDER BY ordinality),'[]') FROM jsonb_array_elements(result) WITH ORDINALITY WHERE ordinality<=size),'has_more',jsonb_array_length(result)>size,'labels',labels);
END;
$$;

CREATE FUNCTION public.entry_context(p_id uuid,p_page integer DEFAULT 0,p_limit integer DEFAULT 20) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=public AS $$
DECLARE center_node jsonb; edges jsonb; nodes jsonb; size integer:=least(50,greatest(1,p_limit)); ids uuid[];
BEGIN
 IF p_page<0 OR p_page>100000 THEN RAISE EXCEPTION 'Invalid page' USING ERRCODE='22023'; END IF;
 center_node:=public.entry_detail(p_id); IF center_node IS NULL THEN RETURN NULL; END IF;
 WITH incident AS (
 SELECT r.id,'person_relationship' subject,r.person_a source,r.person_b target,r.relation_type type,r.description FROM person_relationship r JOIN person a ON a.id=r.person_a AND a.status='published' JOIN person b ON b.id=r.person_b AND b.status='published' WHERE r.status='published' AND (r.person_a=p_id OR r.person_b=p_id)
 UNION ALL SELECT r.id,'person_event',r.person_id,r.event_id,r.role,NULL::text FROM person_event r JOIN person p ON p.id=r.person_id AND p.status='published' JOIN event e ON e.id=r.event_id AND e.status='published' WHERE r.status='published' AND (r.person_id=p_id OR r.event_id=p_id)
 UNION ALL SELECT r.id,'event_causality',r.cause_event_id,r.effect_event_id,'causes',r.description FROM event_causality r JOIN event a ON a.id=r.cause_event_id AND a.status='published' JOIN event b ON b.id=r.effect_event_id AND b.status='published' WHERE r.status='published' AND (r.cause_event_id=p_id OR r.effect_event_id=p_id)
 ), page AS (SELECT * FROM incident ORDER BY subject,id LIMIT size+1 OFFSET p_page*size)
 SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'subject_table',subject,'source',source,'target',target,'type',type,'description',description) ORDER BY subject,id),'[]') INTO edges FROM page;
 SELECT array_agg(DISTINCT v) INTO ids FROM jsonb_array_elements(edges) WITH ORDINALITY e(value,ordinality) CROSS JOIN LATERAL unnest(ARRAY[(e.value->>'source')::uuid,(e.value->>'target')::uuid]) v WHERE e.ordinality<=size;
 SELECT coalesce(jsonb_agg(doc),'[]') INTO nodes FROM (
 SELECT to_jsonb(p)-'biography'-'historical_evaluation'-'family'-'social_relations'||jsonb_build_object('type','person') doc FROM person p WHERE id=ANY(ids) AND status='published'
 UNION ALL SELECT to_jsonb(e)||jsonb_build_object('type','event') FROM event e WHERE id=ANY(ids) AND status='published') n;
 RETURN jsonb_build_object('center',center_node,'nodes',nodes,'edges',(SELECT coalesce(jsonb_agg(value ORDER BY ordinality),'[]') FROM jsonb_array_elements(edges) WITH ORDINALITY WHERE ordinality<=size),'has_more',jsonb_array_length(edges)>size);
END;
$$;
REVOKE ALL ON FUNCTION public.content_page(text,integer,integer,text,boolean,uuid[],text,integer,uuid,integer,integer,text,uuid,uuid,uuid,uuid),public.entry_context(uuid,integer,integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.content_page(text,integer,integer,text,boolean,uuid[],text,integer,uuid,integer,integer,text,uuid,uuid,uuid,uuid),public.entry_context(uuid,integer,integer) TO anon,authenticated,service_role;
COMMIT;
