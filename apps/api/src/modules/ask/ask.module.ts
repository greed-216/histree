import { GatewayGuard } from '../../common/guards/gateway.guard';
import { AiAccessService } from './ai-access.service';
import { Module } from '@nestjs/common';
import { MysqlModule } from '../mysql/mysql.module';
import { AskController } from './ask.controller';
import { AskService } from './ask.service';
import { GuessController } from './guess.controller';
import { GuessBankService } from './guess-bank';
import { GuessService } from './guess.service';
import { GuessAgentService } from './guess-agent.service';
@Module({
  imports: [MysqlModule],
  controllers: [AskController, GuessController],
  providers: [
    AiAccessService,
    GatewayGuard,
    AskService,
    GuessService,
    GuessAgentService,
    GuessBankService,
  ],
})
export class AskModule {}
