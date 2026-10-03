BEGIN;
CREATE TABLE public.ai_gateway_quota (
 actor text NOT NULL,
 operation text NOT NULL CHECK (operation IN ('ask','guess','session')),
 bucket timestamptz NOT NULL,
 used integer NOT NULL CHECK (used > 0),
 PRIMARY KEY (actor,operation,bucket)
);
CREATE INDEX ai_gateway_quota_expiry ON public.ai_gateway_quota(bucket);
ALTER TABLE public.ai_gateway_quota ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.ai_gateway_quota FROM PUBLIC,anon,authenticated;

CREATE FUNCTION public.consume_ai_gateway_quota(p_actor text,p_operation text)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE
 current_bucket timestamptz := date_trunc('hour',now());
 actor_cap integer; global_cap integer; accepted boolean;
BEGIN
 IF p_actor IS NULL OR p_actor !~ '^(anon:[a-f0-9]{64}|user:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$' OR p_operation IS NULL OR p_operation NOT IN ('ask','guess','session') THEN
  RAISE EXCEPTION 'Invalid quota scope' USING ERRCODE='22023';
 END IF;
 actor_cap := CASE p_operation WHEN 'ask' THEN 10 WHEN 'guess' THEN 80 ELSE 1 END;
 -- Shared cost ceilings also bound anonymous clients that request fresh identities.
 global_cap := CASE p_operation WHEN 'ask' THEN 200 WHEN 'guess' THEN 1600 ELSE 1000 END;
 BEGIN
  INSERT INTO public.ai_gateway_quota AS q VALUES ('global',p_operation,current_bucket,1)
   ON CONFLICT (actor,operation,bucket) DO UPDATE SET used=q.used+1 WHERE q.used<global_cap RETURNING true INTO accepted;
  IF accepted IS DISTINCT FROM true THEN RETURN false; END IF;
  accepted := NULL;
  INSERT INTO public.ai_gateway_quota AS q VALUES (p_actor,p_operation,current_bucket,1)
   ON CONFLICT (actor,operation,bucket) DO UPDATE SET used=q.used+1 WHERE q.used<actor_cap RETURNING true INTO accepted;
  -- Roll back the global debit too when the caller is already over quota.
  IF accepted IS DISTINCT FROM true THEN RAISE EXCEPTION 'Quota exceeded'; END IF;
 EXCEPTION WHEN SQLSTATE 'P0001' THEN RETURN false;
 END;
 DELETE FROM public.ai_gateway_quota WHERE bucket<current_bucket-interval '2 hours';
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION public.consume_ai_gateway_quota(text,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.consume_ai_gateway_quota(text,text) TO service_role;
COMMIT;
