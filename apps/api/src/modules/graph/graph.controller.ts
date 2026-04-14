import { Controller, Get } from '@nestjs/common';
import { GraphService } from './graph.service';
import type { GraphData } from '@histree/shared-types';

@Controller('api/graph')
export class GraphController {
  constructor(private readonly graphService: GraphService) {}

  @Get('demo')
  async getDemoGraph(): Promise<GraphData> {
    return this.graphService.getDemoGraphData();
  }
}
