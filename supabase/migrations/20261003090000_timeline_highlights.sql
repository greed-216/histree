BEGIN;
-- A bounded selection of published titles for instant local hover previews.
-- Prefer recorded impact, then titles describing regime changes; no generated facts.
CREATE OR REPLACE FUNCTION public.timeline_overview()
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
 WITH published AS (SELECT id,title,start_year,end_year,impact_level FROM event WHERE status='published'),
 ranked AS (SELECT *,row_number() OVER (PARTITION BY start_year ORDER BY
 coalesce(impact_level,0) DESC,
 (title ~ '(称帝|建立|灭亡|禅位|即位|政变|建国)') DESC,id) AS rank
 FROM published WHERE start_year IS NOT NULL),
 years AS (SELECT start_year AS year,count(*) AS count,
 coalesce(jsonb_agg(jsonb_build_object('id',id,'title',title) ORDER BY rank) FILTER(WHERE rank<=3),'[]'::jsonb) AS highlights
 FROM ranked GROUP BY start_year)
 SELECT jsonb_build_object(
 'years',(SELECT coalesce(jsonb_agg(to_jsonb(years) ORDER BY year),'[]'::jsonb) FROM years),
 'total',(SELECT count(*) FROM published),
 'undated',(SELECT count(*) FROM published WHERE start_year IS NULL),
 'from',(SELECT min(start_year) FROM published),
 'to',(SELECT max(greatest(start_year,coalesce(end_year,start_year))) FROM published WHERE start_year IS NOT NULL));
$$;
REVOKE ALL ON FUNCTION public.timeline_overview() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.timeline_overview() TO anon,authenticated,service_role;
COMMIT;
