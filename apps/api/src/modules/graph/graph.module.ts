import { ExploreController } from './explore.controller';
import { Module } from '@nestjs/common';
import { GraphController } from './graph.controller';
import { GraphService } from './graph.service';

@Module({
  controllers: [GraphController, ExploreController],
  providers: [GraphService],
})
export class GraphModule {}
