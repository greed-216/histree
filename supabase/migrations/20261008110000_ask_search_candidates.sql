-- Retrieve evidence matches once per keyword using the existing claims_search_trgm index.
-- Preserve publication/RLS boundaries, ranking, literal keywords and pagination.
BEGIN;
-- A narrow read-only lookup avoids RLS's per-row visibility functions preventing
-- the trigram index scan. It returns no evidence text, only published parent IDs.
-- No dynamic SQL, caller-controlled SQL or privileged data client is involved.
CREATE OR REPLACE FUNCTION public.ask_published_claim_hits(p_keywords text[],p_kind text DEFAULT 'all')
RETURNS TABLE(id uuid,kind text,term_id bigint)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $hits$
BEGIN
 IF p_kind NOT IN ('all','person','event','topic') OR p_keywords IS NULL OR cardinality(p_keywords) NOT BETWEEN 1 AND 6
 OR EXISTS(SELECT 1 FROM unnest(p_keywords) k WHERE k IS NULL OR length(btrim(k)) NOT BETWEEN 1 AND 40)
 THEN RAISE EXCEPTION 'Invalid ask search' USING ERRCODE='22023'; END IF;
 RETURN QUERY
 WITH terms AS(SELECT ordinality term_id,'%'||replace(replace(replace(lower(btrim(k)),E'\\',E'\\\\'),'%',E'\\%'),'_',E'\\_')||'%' pattern FROM unnest(p_keywords) WITH ORDINALITY AS keywords(k,ordinality))
 SELECT DISTINCT c.subject_id,c.subject_table,t.term_id
 FROM terms t JOIN public.fact_claim c ON lower(c.claim_text||' '||coalesce(c.note,'')) LIKE t.pattern
 WHERE c.status='published' AND c.subject_table IN ('person','event')
 AND (p_kind='all' OR c.subject_table=p_kind)
 AND CASE c.subject_table
 WHEN 'person' THEN EXISTS(SELECT 1 FROM public.person p WHERE p.id=c.subject_id AND p.status='published')
 WHEN 'event' THEN EXISTS(SELECT 1 FROM public.event e WHERE e.id=c.subject_id AND e.status='published')
 ELSE false END;
END;
$hits$;
REVOKE ALL ON FUNCTION public.ask_published_claim_hits(text[],text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ask_published_claim_hits(text[],text) TO anon,authenticated;
CREATE OR REPLACE FUNCTION public.ask_search(p_keywords text[],p_kind text DEFAULT 'all',p_from integer DEFAULT NULL,p_to integer DEFAULT NULL,p_offset integer DEFAULT 0)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=public AS $$
DECLARE result jsonb;
BEGIN
 IF p_kind NOT IN ('all','person','event','topic') OR cardinality(p_keywords) NOT BETWEEN 1 AND 6 OR EXISTS(SELECT 1 FROM unnest(p_keywords) k WHERE length(btrim(k)) NOT BETWEEN 1 AND 40) OR p_offset<0 OR p_offset>10000 OR (p_from IS NOT NULL AND p_to IS NOT NULL AND p_from>p_to) THEN RAISE EXCEPTION 'Invalid ask search' USING ERRCODE='22023'; END IF;
 WITH terms AS(SELECT term_id,lower(btrim(k)) term,'%'||replace(replace(replace(lower(btrim(k)),E'\\',E'\\\\'),'%',E'\\%'),'_',E'\\_')||'%' pattern FROM unnest(p_keywords) WITH ORDINALITY AS keywords(k,term_id)),
 entries AS MATERIALIZED(
 SELECT p.id,'person' kind,p.name label,p.aliases,p.birth_year start_year,p.death_year end_year,p.description,public.histree_person_search(p.name,p.aliases,p.era,p.faction,p.tags,p.description)||' '||lower(coalesce(p.biography,'')) body FROM person p WHERE p.status='published' AND p_kind IN ('all','person')
 UNION ALL SELECT e.id,'event',e.title,NULL::text[],e.start_year,coalesce(e.end_year,e.start_year),e.description,public.histree_event_search(e.title,e.dynasty,e.tags,e.description) FROM event e WHERE e.status='published' AND p_kind IN ('all','event')
 UNION ALL SELECT t.id,'topic',t.title,NULL::text[],NULL::int,NULL::int,t.description,lower(t.title||' '||t.description) FROM topic t WHERE t.status='published' AND p_kind IN ('all','topic')
 ), claim_hits AS MATERIALIZED(
 SELECT * FROM public.ask_published_claim_hits(p_keywords,p_kind)
 ), hits AS(
 SELECT e.id,e.kind,t.term_id FROM entries e CROSS JOIN terms t
 WHERE lower(e.label) LIKE t.pattern OR EXISTS(SELECT 1 FROM unnest(e.aliases) a WHERE lower(a) LIKE t.pattern) OR e.body LIKE t.pattern
 UNION SELECT id,kind,term_id FROM claim_hits
 ), scored AS(
 SELECT e.id,e.kind,e.label,e.aliases,e.start_year,e.end_year,left(e.description,1600) description,
 sum(CASE WHEN lower(e.label)=t.term OR t.term=ANY(SELECT lower(a) FROM unnest(e.aliases) a) THEN 10
 WHEN lower(e.label) LIKE t.pattern OR EXISTS(SELECT 1 FROM unnest(e.aliases) a WHERE lower(a) LIKE t.pattern) THEN 5 ELSE 1 END) score
 FROM hits h JOIN entries e ON e.id=h.id AND e.kind=h.kind JOIN terms t ON t.term_id=h.term_id
 WHERE (p_from IS NULL AND p_to IS NULL OR e.start_year IS NOT NULL OR e.end_year IS NOT NULL)
 AND (p_from IS NULL OR coalesce(e.end_year,e.start_year)>=p_from) AND(p_to IS NULL OR coalesce(e.start_year,e.end_year)<=p_to)
 GROUP BY e.id,e.kind,e.label,e.aliases,e.start_year,e.end_year,e.description
 ), page AS(SELECT * FROM scored WHERE score>0 ORDER BY score DESC,id LIMIT 13 OFFSET p_offset)
 SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'kind',kind,'label',label,'aliases',aliases,'startYear',start_year,'endYear',end_year,'description',description,'score',score) ORDER BY score DESC,id),'[]') INTO result FROM page;
 RETURN jsonb_build_object('items',(SELECT coalesce(jsonb_agg(value ORDER BY ordinality),'[]') FROM jsonb_array_elements(result) WITH ORDINALITY WHERE ordinality<=12),'nextOffset',CASE WHEN jsonb_array_length(result)>12 THEN p_offset+12 ELSE NULL END,'scope','仅搜索已发布条目及其已录入引文；未搜索整部史书。年代筛选排除年代未知条目。');
END;
$$;
REVOKE ALL ON FUNCTION public.ask_search(text[],text,integer,integer,integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ask_search(text[],text,integer,integer,integer) TO anon,authenticated;
COMMIT;
