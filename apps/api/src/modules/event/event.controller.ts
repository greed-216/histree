import { Controller, Get, Param, Query } from '@nestjs/common';
import { EventService } from './event.service';
import type { Event, EventDetail, PageResult } from '@histree/shared-types';

@Controller('api/v1/event')
export class EventController {
  constructor(private readonly eventService: EventService) {}

  @Get()
  async getEvents(
    @Query() query: Record<string, string>,
  ): Promise<PageResult<Event>> {
    return this.eventService.getEvents(query);
  }

  @Get(':id')
  async getEventDetail(
    @Param('id') id: string,
    @Query('page') page?: string,
  ): Promise<EventDetail> {
    return this.eventService.getEventDetail(id, page);
  }

}
