import { Controller, Get, Param } from '@nestjs/common';
import { GraphService } from './graph.service';
import type { GraphResponse } from '@histree/shared-types';

@Controller('api/v1/graph')
export class GraphController {
  constructor(private readonly graphService: GraphService) {}

  @Get('person/:id')
  async getPersonGraph(@Param('id') id: string): Promise<GraphResponse> {
    return this.graphService.getPersonGraph(id);
  }
}
