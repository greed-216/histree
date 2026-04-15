import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { GraphModule } from './modules/graph/graph.module';
import { EventModule } from './modules/event/event.module';
import { TimelineModule } from './modules/timeline/timeline.module';
import { PersonModule } from './modules/person/person.module';
import { SupabaseModule } from './modules/supabase/supabase.module';
import { UploadModule } from './modules/upload/upload.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    SupabaseModule,
    GraphModule,
    EventModule,
    PersonModule,
    TimelineModule,
    UploadModule
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
