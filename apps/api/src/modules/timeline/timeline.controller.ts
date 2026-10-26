import { Controller, Get, Query } from '@nestjs/common';
import { TimelineService } from './timeline.service';
@Controller('api/v1/timeline')
export class TimelineController {
  constructor(private readonly timelineService: TimelineService) {}
  @Get('overview') getOverview(@Query('compact') compact?: string) {
    return this.timelineService.getOverview(compact === '1');
  }
  @Get('highlights') highlights(@Query('year') year: string) {
    return this.timelineService.getHighlights(year);
  }
  @Get() getTimeline(@Query() query: Record<string, string>) {
    return this.timelineService.getTimeline(query);
  }
}
