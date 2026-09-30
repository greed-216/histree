BEGIN;
CREATE FUNCTION public.ask_search(p_keywords text[],p_kind text DEFAULT 'all',p_from integer DEFAULT NULL,p_to integer DEFAULT NULL,p_offset integer DEFAULT 0)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=public AS $$
DECLARE result jsonb;
BEGIN
 IF p_kind NOT IN ('all','person','event','topic') OR cardinality(p_keywords) NOT BETWEEN 1 AND 6 OR EXISTS(SELECT 1 FROM unnest(p_keywords) k WHERE length(btrim(k)) NOT BETWEEN 1 AND 40) OR p_offset<0 OR p_offset>10000 OR (p_from IS NOT NULL AND p_to IS NOT NULL AND p_from>p_to) THEN RAISE EXCEPTION 'Invalid ask search' USING ERRCODE='22023'; END IF;
 WITH terms AS(SELECT lower(btrim(k)) term,'%'||replace(replace(replace(lower(btrim(k)),E'\\',E'\\\\'),'%',E'\\%'),'_',E'\\_')||'%' pattern FROM unnest(p_keywords) k),
 entries AS(
 SELECT p.id,'person' kind,p.name label,p.aliases,p.birth_year start_year,p.death_year end_year,p.description,public.histree_person_search(p.name,p.aliases,p.era,p.faction,p.tags,p.description)||' '||lower(coalesce(p.biography,'')) body FROM person p WHERE p.status='published' AND p_kind IN ('all','person')
 UNION ALL SELECT e.id,'event',e.title,NULL::text[],e.start_year,coalesce(e.end_year,e.start_year),e.description,public.histree_event_search(e.title,e.dynasty,e.tags,e.description) FROM event e WHERE e.status='published' AND p_kind IN ('all','event')
 UNION ALL SELECT t.id,'topic',t.title,NULL::text[],NULL::int,NULL::int,t.description,lower(t.title||' '||t.description) FROM topic t WHERE t.status='published' AND p_kind IN ('all','topic')
 ), scored AS(
 SELECT e.id,e.kind,e.label,e.aliases,e.start_year,e.end_year,left(e.description,1600) description,sum(CASE WHEN lower(e.label)=term OR term=ANY(SELECT lower(a) FROM unnest(e.aliases) a) THEN 10 WHEN lower(e.label) LIKE pattern OR EXISTS(SELECT 1 FROM unnest(e.aliases) a WHERE lower(a) LIKE pattern) THEN 5 WHEN e.body LIKE pattern OR EXISTS(SELECT 1 FROM fact_claim c WHERE c.subject_table=e.kind AND c.subject_id=e.id AND c.status='published' AND lower(c.claim_text||' '||coalesce(c.note,'')) LIKE pattern) THEN 1 ELSE 0 END) score
 FROM entries e CROSS JOIN terms WHERE (p_from IS NULL AND p_to IS NULL OR e.start_year IS NOT NULL OR e.end_year IS NOT NULL) AND (p_from IS NULL OR coalesce(e.end_year,e.start_year)>=p_from) AND(p_to IS NULL OR coalesce(e.start_year,e.end_year)<=p_to)
 GROUP BY e.id,e.kind,e.label,e.aliases,e.start_year,e.end_year,e.description
 ), page AS(SELECT * FROM scored WHERE score>0 ORDER BY score DESC,id LIMIT 13 OFFSET p_offset)
 SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'kind',kind,'label',label,'aliases',aliases,'startYear',start_year,'endYear',end_year,'description',description,'score',score) ORDER BY score DESC,id),'[]') INTO result FROM page;
 RETURN jsonb_build_object('items',(SELECT coalesce(jsonb_agg(value ORDER BY ordinality),'[]') FROM jsonb_array_elements(result) WITH ORDINALITY WHERE ordinality<=12),'nextOffset',CASE WHEN jsonb_array_length(result)>12 THEN p_offset+12 ELSE NULL END,'scope','仅搜索已发布条目及其已录入引文；未搜索整部史书。年代筛选排除年代未知条目。');
END;
$$;
REVOKE ALL ON FUNCTION public.ask_search(text[],text,integer,integer,integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ask_search(text[],text,integer,integer,integer) TO anon,authenticated;
COMMIT;
