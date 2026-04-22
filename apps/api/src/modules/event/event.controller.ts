import { Body, Controller, Delete, Get, Param, Patch, Post, UseGuards } from '@nestjs/common';
import { AdminGuard } from '../../common/guards/admin.guard';
import { EventService } from './event.service';
import type { Event, EventDetail } from '@histree/shared-types';

@Controller('api/v1/event')
export class EventController {
  constructor(private readonly eventService: EventService) {}

  @Get()
  async getEvents(): Promise<Event[]> {
    return this.eventService.getEvents();
  }

  @Get(':id')
  async getEventDetail(@Param('id') id: string): Promise<EventDetail> {
    return this.eventService.getEventDetail(id);
  }

  @Post()
  @UseGuards(AdminGuard)
  async createEvent(@Body() payload: Partial<Event>): Promise<Event> {
    return this.eventService.createEvent(payload);
  }

  @Patch(':id')
  @UseGuards(AdminGuard)
  async updateEvent(@Param('id') id: string, @Body() payload: Partial<Event>): Promise<Event> {
    return this.eventService.updateEvent(id, payload);
  }

  @Delete(':id')
  @UseGuards(AdminGuard)
  async deleteEvent(@Param('id') id: string): Promise<{ id: string }> {
    return this.eventService.deleteEvent(id);
  }
}
