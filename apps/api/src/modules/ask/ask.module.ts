import { GatewayGuard } from '../../common/guards/gateway.guard';
import { AiAccessService } from './ai-access.service';
import { Module } from '@nestjs/common';
import { SupabaseModule } from '../supabase/supabase.module';
import { AskController } from './ask.controller';
import { AskService } from './ask.service';
import { GuessController } from './guess.controller';
import { GuessService } from './guess.service';
import { GuessAgentService } from './guess-agent.service';
@Module({
  imports: [SupabaseModule],
  controllers: [AskController, GuessController],
  providers: [AiAccessService, GatewayGuard, AskService, GuessService, GuessAgentService],
})
export class AskModule {}
