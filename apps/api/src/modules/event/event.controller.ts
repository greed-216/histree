import { Controller, Get, Param } from '@nestjs/common';
import { EventService } from './event.service';
import type { EventDetail } from '@histree/shared-types';

@Controller('api/v1/event')
export class EventController {
  constructor(private readonly eventService: EventService) {}

  @Get(':id')
  async getEventDetail(@Param('id') id: string): Promise<EventDetail> {
    return this.eventService.getEventDetail(id);
  }
}
