import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Patch,
  Post,
  Query,
  UseGuards,
} from '@nestjs/common';
import { AdminGuard } from '../../common/guards/admin.guard';
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

  @Post()
  @UseGuards(AdminGuard)
  async createEvent(@Body() payload: Partial<Event>): Promise<Event> {
    return this.eventService.createEvent(payload);
  }

  @Patch(':id')
  @UseGuards(AdminGuard)
  async updateEvent(
    @Param('id') id: string,
    @Body() payload: Partial<Event>,
  ): Promise<Event> {
    return this.eventService.updateEvent(id, payload);
  }

  @Delete(':id')
  @UseGuards(AdminGuard)
  async deleteEvent(@Param('id') id: string): Promise<{ id: string }> {
    return this.eventService.deleteEvent(id);
  }
}
