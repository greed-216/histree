import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

@Injectable()
export class SupabaseService {
  private supabase: SupabaseClient;
  private adminClient: SupabaseClient;
  private readonly logger = new Logger(SupabaseService.name);

  constructor(private configService: ConfigService) {
    const supabaseUrl = this.configService.get<string>('SUPABASE_URL');
    const supabaseKey = this.configService.get<string>('SUPABASE_ANON_KEY');
    const supabaseServiceKey = this.configService.get<string>('SUPABASE_SERVICE_ROLE_KEY');

    if (!supabaseUrl || !supabaseKey) {
      this.logger.warn('Supabase URL or Key is missing. Check your .env file.');
    }

    this.supabase = createClient(
      supabaseUrl || 'http://127.0.0.1:54321',
      supabaseKey || 'dummy_key'
    );

    if (supabaseServiceKey) {
      this.adminClient = createClient(
        supabaseUrl || 'http://127.0.0.1:54321',
        supabaseServiceKey
      );
    } else {
      this.adminClient = this.supabase;
    }
  }

  getClient(): SupabaseClient {
    return this.supabase;
  }

  getAdminClient(): SupabaseClient {
    return this.adminClient;
  }
}
