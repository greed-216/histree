import { Controller, Get, Query } from '@nestjs/common';
import { TimelineService } from './timeline.service';
@Controller('api/v1/timeline')
export class TimelineController {
  constructor(private readonly timelineService: TimelineService) {}
  @Get() getTimeline(@Query() query: Record<string, string>) {
    return this.timelineService.getTimeline(query);
  }
}
