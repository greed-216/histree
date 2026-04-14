import { Controller, Get, Query } from '@nestjs/common';
import { TimelineService } from './timeline.service';
import type { Event } from '@histree/shared-types';

@Controller('api/v1/timeline')
export class TimelineController {
  constructor(private readonly timelineService: TimelineService) {}

  @Get()
  async getTimeline(
    @Query('start') start: string,
    @Query('end') end: string,
  ): Promise<Event[]> {
    const startYear = parseInt(start, 10);
    const endYear = parseInt(end, 10);
    return this.timelineService.getTimeline(startYear, endYear);
  }
}
