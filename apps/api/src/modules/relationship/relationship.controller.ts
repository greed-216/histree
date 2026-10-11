import { Controller, Get, Query } from '@nestjs/common';
import type { RelationshipBundle } from '@histree/shared-types';
import { RelationshipService } from './relationship.service';
@Controller('api/v1/relationships')
export class RelationshipController {
  constructor(private readonly relationshipService: RelationshipService) {}

  @Get()
  async getRelationships(
    @Query() query: Record<string, string>,
  ): Promise<RelationshipBundle> {
    return this.relationshipService.getRelationships(query);
  }

}
