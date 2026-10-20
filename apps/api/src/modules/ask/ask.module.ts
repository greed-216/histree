import { GuessClueResearch } from './guess-clue-research';
import { GuessCharacterCatalogue } from './guess-character-catalogue';
import { GuessGameLibrary } from './guess-game-library';
import { GuessClueController } from './guess-clue.controller';
import { GuessClueGameService } from './guess-clue-game.service';
import { GuessClueSetsService } from './guess-clue-sets.service';
import { GuessClueStore } from './guess-clue-store';
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
  controllers: [AskController, GuessController, GuessClueController],
  providers: [
    AiAccessService,
    GatewayGuard,
    AskService,
    GuessService,
    GuessAgentService,
    GuessBankService,
    GuessCharacterCatalogue,
    GuessClueStore,
    GuessGameLibrary,
    GuessClueSetsService,
    GuessClueResearch,
    GuessClueGameService,
  ],
})
export class AskModule {}
