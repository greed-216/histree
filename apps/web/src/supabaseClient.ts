import { createClient } from '@supabase/supabase-js';

export const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
export const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

export const supabase = createClient(supabaseUrl ?? '', supabaseAnonKey ?? '');

// Public pages always use the anonymous RLS view, even when an editor is signed in.
export const publicSupabase = createClient(supabaseUrl ?? '', supabaseAnonKey ?? '', {
  auth: { storageKey: 'histree-public-view', persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
});
