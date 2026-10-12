BEGIN;
SET LOCAL search_path = public, extensions;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Immutable wrappers make the search document consistent for inserts and updates.
CREATE FUNCTION public.histree_person_search(name text, aliases text[], era text, faction text, tags text[], description text)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE SET search_path = public AS $$
 SELECT lower(coalesce(name,'') || ' ' || coalesce(array_to_string(aliases,' '),'') || ' ' || coalesce(era,'') || ' ' || coalesce(faction,'') || ' ' || coalesce(array_to_string(tags,' '),'') || ' ' || coalesce(description,''));
$$;
CREATE FUNCTION public.histree_event_search(title text, dynasty text, tags text[], description text)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE SET search_path = public AS $$
 SELECT lower(coalesce(title,'') || ' ' || coalesce(dynasty,'') || ' ' || coalesce(array_to_string(tags,' '),'') || ' ' || coalesce(description,''));
$$;
CREATE INDEX person_search_trgm ON public.person USING gin((public.histree_person_search(name,aliases,era,faction,tags,description)) gin_trgm_ops) WHERE status='published';
CREATE INDEX event_search_trgm ON public.event USING gin((public.histree_event_search(title,dynasty,tags,description)) gin_trgm_ops) WHERE status='published';
CREATE INDEX topic_search_trgm ON public.topic USING gin((lower(title || ' ' || description)) gin_trgm_ops) WHERE status='published';

-- SECURITY INVOKER plus explicit publication checks: never expose editor drafts.
CREATE FUNCTION public.search_entries(p_query text DEFAULT '', p_kind text DEFAULT 'all', p_page integer DEFAULT 0, p_limit integer DEFAULT 20)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = public AS $$
DECLARE q text := lower(btrim(coalesce(p_query,''))); pattern text; results jsonb; size integer := least(50,greatest(1,p_limit));
BEGIN
 IF p_kind NOT IN ('all','person','event','topic','nodes') OR p_page < 0 OR p_page > 100000 OR length(q)>200 THEN
   RAISE EXCEPTION 'Invalid search parameters' USING ERRCODE='22023';
 END IF;
 -- LIKE metacharacters are literal user input, not a query language.
 pattern := '%' || replace(replace(replace(q, E'\\', E'\\\\'), '%', E'\\%'), '_', E'\\_') || '%';
 WITH matches AS (
 SELECT p.id, 'person' AS kind, p.name AS title,
   CASE WHEN lower(p.name)=q THEN 0 WHEN q=ANY(SELECT lower(a) FROM unnest(p.aliases) a) THEN 1 WHEN lower(p.name) LIKE pattern THEN 2 ELSE 3 END AS rank,
   jsonb_build_object('id',p.id,'type','person','name',p.name,'era',p.era,'description',left(p.description,300),'image_url',p.image_url) AS item
 FROM person p WHERE p.status='published' AND p_kind IN ('all','person','nodes') AND (q='' OR public.histree_person_search(p.name,p.aliases,p.era,p.faction,p.tags,p.description) LIKE pattern)
 UNION ALL
 SELECT e.id, 'event', e.title, CASE WHEN lower(e.title)=q THEN 0 WHEN lower(e.title) LIKE pattern THEN 2 ELSE 3 END,
   jsonb_build_object('id',e.id,'type','event','title',e.title,'start_year',e.start_year,'end_year',e.end_year,'description',left(e.description,300),'image_url',e.image_url)
 FROM event e WHERE e.status='published' AND p_kind IN ('all','event','nodes') AND (q='' OR public.histree_event_search(e.title,e.dynasty,e.tags,e.description) LIKE pattern)
 UNION ALL
 SELECT t.id, 'topic', t.title, CASE WHEN lower(t.title)=q THEN 0 WHEN lower(t.title) LIKE pattern THEN 2 ELSE 3 END,
   jsonb_build_object('id',t.id,'type','topic','title',t.title,'slug',t.slug,'description',left(t.description,300))
 FROM topic t WHERE t.status='published' AND p_kind IN ('all','topic') AND (q='' OR lower(t.title || ' ' || t.description) LIKE pattern)
 ), page AS (SELECT * FROM matches ORDER BY rank,title,kind,id LIMIT size+1 OFFSET p_page*size)
 SELECT coalesce(jsonb_agg(item ORDER BY rank,title,kind,id),'[]') INTO results FROM page;
 RETURN jsonb_build_object('items', (SELECT coalesce(jsonb_agg(value ORDER BY ordinality),'[]') FROM jsonb_array_elements(results) WITH ORDINALITY WHERE ordinality<=size), 'has_more', jsonb_array_length(results)>size);
END;
$$;

CREATE FUNCTION public.graph_slice(p_id uuid, p_mode text DEFAULT 'people', p_depth integer DEFAULT 1, p_from integer DEFAULT NULL, p_to integer DEFAULT NULL)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = public AS $$
DECLARE visited uuid[] := ARRAY[p_id]; frontier uuid[] := ARRAY[p_id]; next_frontier uuid[];
 nodes jsonb; center_node jsonb; edges jsonb := '[]'; candidates jsonb; edge jsonb; endpoint uuid;
 edge_ids text[] := '{}'; identity text; cut boolean := false; node_cap CONSTANT integer := 120; edge_cap CONSTANT integer := 300;
BEGIN
 IF p_mode NOT IN ('people','events') OR p_depth NOT BETWEEN 1 AND 2 OR (p_from IS NOT NULL AND p_to IS NOT NULL AND p_from>p_to) THEN
   RAISE EXCEPTION 'Invalid graph parameters' USING ERRCODE='22023';
 END IF;
 SELECT item INTO center_node FROM (
 SELECT jsonb_build_object('id',id,'type','person','name',name,'era',era,'description',left(description,600)) item FROM person WHERE id=p_id AND status='published'
 UNION ALL SELECT jsonb_build_object('id',id,'type','event','title',title,'start_year',start_year,'end_year',end_year,'description',left(description,600)) FROM event WHERE id=p_id AND status='published'
 ) n;
 IF center_node IS NULL THEN RETURN NULL; END IF;
 FOR level IN 1..p_depth LOOP
   next_frontier := '{}';
   WITH incident AS (
    SELECT r.id, 'person_relationship' AS subject, r.person_a AS source, r.person_b AS target, r.relation_type AS type, r.description
    FROM person_relationship r JOIN person a ON a.id=r.person_a AND a.status='published' JOIN person b ON b.id=r.person_b AND b.status='published'
    WHERE p_mode='people' AND r.status='published' AND (r.person_a=ANY(frontier) OR r.person_b=ANY(frontier))
    UNION ALL
    SELECT r.id, 'person_event', r.person_id, r.event_id, r.role, NULL::text
    FROM person_event r JOIN person p ON p.id=r.person_id AND p.status='published' JOIN event e ON e.id=r.event_id AND e.status='published'
    WHERE p_mode='events' AND r.status='published' AND (r.person_id=ANY(frontier) OR r.event_id=ANY(frontier))
      AND (p_from IS NULL OR e.start_year IS NULL OR coalesce(e.end_year,e.start_year)>=p_from)
      AND (p_to IS NULL OR e.start_year IS NULL OR e.start_year<=p_to)
   ), bounded AS (SELECT * FROM incident WHERE NOT (subject || ':' || id::text)=ANY(edge_ids) ORDER BY subject,id LIMIT edge_cap+1)
   SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'subject_table',subject,'source',source,'target',target,'type',type,'description',description) ORDER BY subject,id),'[]') INTO candidates FROM bounded;
   IF jsonb_array_length(candidates)>edge_cap THEN cut := true; END IF;
   FOR edge IN SELECT value FROM jsonb_array_elements(candidates) LOOP
     identity := (edge->>'subject_table') || ':' || (edge->>'id');
     IF identity=ANY(edge_ids) THEN CONTINUE; END IF;
     IF jsonb_array_length(edges)>=edge_cap THEN cut := true; CONTINUE; END IF;
     -- Add endpoints atomically; an edge is never returned without both nodes.
     IF cardinality(visited)+(SELECT count(*) FROM (SELECT DISTINCT v FROM unnest(ARRAY[(edge->>'source')::uuid,(edge->>'target')::uuid]) v WHERE NOT v=ANY(visited)) fresh)>node_cap THEN
       cut := true; CONTINUE;
     END IF;
     FOREACH endpoint IN ARRAY ARRAY[(edge->>'source')::uuid,(edge->>'target')::uuid] LOOP
       IF NOT endpoint=ANY(visited) THEN visited:=array_append(visited,endpoint); next_frontier:=array_append(next_frontier,endpoint); END IF;
     END LOOP;
     edges:=edges || jsonb_build_array(edge); edge_ids:=array_append(edge_ids,identity);
   END LOOP;
   frontier:=next_frontier;
   EXIT WHEN cardinality(frontier)=0;
 END LOOP;
 SELECT coalesce(jsonb_agg(item ORDER BY id),'[]') INTO nodes FROM (
 SELECT id,jsonb_build_object('id',id,'type','person','name',name,'era',era,'description',left(description,600)) item FROM person WHERE id=ANY(visited) AND status='published'
 UNION ALL SELECT id,jsonb_build_object('id',id,'type','event','title',title,'start_year',start_year,'end_year',end_year,'description',left(description,600)) FROM event WHERE id=ANY(visited) AND status='published'
 ) n;
 RETURN jsonb_build_object('center',center_node,'nodes',nodes,'edges',edges,'truncated',cut,'node_limit',node_cap,'edge_limit',edge_cap);
END;
$$;
REVOKE ALL ON FUNCTION public.search_entries(text,text,integer,integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.graph_slice(uuid,text,integer,integer,integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.search_entries(text,text,integer,integer), public.graph_slice(uuid,text,integer,integer,integer) TO anon, authenticated;
CREATE FUNCTION public.entry_detail(p_id uuid) RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
 SELECT to_jsonb(p) || jsonb_build_object('type','person') FROM person p WHERE id=p_id AND status='published'
 UNION ALL SELECT to_jsonb(e) || jsonb_build_object('type','event') FROM event e WHERE id=p_id AND status='published';
$$;
REVOKE ALL ON FUNCTION public.entry_detail(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.entry_detail(uuid) TO anon, authenticated;
COMMIT;
