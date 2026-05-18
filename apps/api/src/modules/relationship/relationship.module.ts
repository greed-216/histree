import { Module } from '@nestjs/common';
import { SupabaseModule } from '../supabase/supabase.module';
import { RelationshipController } from './relationship.controller';
import { RelationshipService } from './relationship.service';

@Module({
  imports: [SupabaseModule],
  controllers: [RelationshipController],
  providers: [RelationshipService],
})
export class RelationshipModule {}
