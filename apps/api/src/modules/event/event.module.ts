import { Module } from '@nestjs/common';
import { AdminGuard } from '../../common/guards/admin.guard';
import { EventController } from './event.controller';
import { EventService } from './event.service';

@Module({
  controllers: [EventController],
  providers: [EventService, AdminGuard],
})
export class EventModule {}
