BEGIN;
-- Start-year counts describe the published corpus, not historical importance.
CREATE FUNCTION public.timeline_overview()
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
 WITH published AS (SELECT start_year,end_year FROM event WHERE status='published'),
 years AS (SELECT start_year AS year,count(*) AS count FROM published WHERE start_year IS NOT NULL GROUP BY start_year)
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
