import { FeedbackModule } from './modules/feedback/feedback.module';
import { LibraryModule } from './modules/library/library.module';
import { CatalogModule } from './modules/catalog/catalog.module';
import { AskModule } from './modules/ask/ask.module';
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { GraphModule } from './modules/graph/graph.module';
import { EventModule } from './modules/event/event.module';
import { TimelineModule } from './modules/timeline/timeline.module';
import { PersonModule } from './modules/person/person.module';
import { MysqlModule } from './modules/mysql/mysql.module';
import { RelationshipModule } from './modules/relationship/relationship.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    MysqlModule,
    GraphModule,
    EventModule,
    PersonModule,
    TimelineModule,
    RelationshipModule,
    CatalogModule,
    FeedbackModule,
    LibraryModule,
    AskModule,
  ],
  controllers: [AppController],
  providers: [],
})
export class AppModule {}
