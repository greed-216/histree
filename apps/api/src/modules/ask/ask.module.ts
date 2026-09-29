import { Module } from '@nestjs/common';
import { SupabaseModule } from '../supabase/supabase.module';
import { AskController } from './ask.controller';
import { AskService } from './ask.service';
@Module({ imports: [SupabaseModule], controllers: [AskController], providers: [AskService] })
export class AskModule {}
