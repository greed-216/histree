import { Body, Controller, Delete, Get, Param, Patch, Post, UseGuards } from '@nestjs/common';
import type {
  EventCausalityRelation,
  EventCausalityRelationInput,
  PersonEventRelation,
  PersonEventRelationInput,
  PersonRelationship,
  PersonRelationshipInput,
  RelationshipBundle,
} from '@histree/shared-types';
import { AdminGuard } from '../../common/guards/admin.guard';
import { RelationshipService } from './relationship.service';

@Controller('api/v1/relationships')
export class RelationshipController {
  constructor(private readonly relationshipService: RelationshipService) {}

  @Get()
  async getRelationships(): Promise<RelationshipBundle> {
    return this.relationshipService.getRelationships();
  }

  @Post('person-relationships')
  @UseGuards(AdminGuard)
  async createPersonRelationship(@Body() payload: PersonRelationshipInput): Promise<PersonRelationship> {
    return this.relationshipService.createPersonRelationship(payload);
  }

  @Patch('person-relationships/:id')
  @UseGuards(AdminGuard)
  async updatePersonRelationship(
    @Param('id') id: string,
    @Body() payload: Partial<PersonRelationshipInput>,
  ): Promise<PersonRelationship> {
    return this.relationshipService.updatePersonRelationship(id, payload);
  }

  @Delete('person-relationships/:id')
  @UseGuards(AdminGuard)
  async deletePersonRelationship(@Param('id') id: string): Promise<{ id: string }> {
    return this.relationshipService.deletePersonRelationship(id);
  }

  @Post('person-events')
  @UseGuards(AdminGuard)
  async createPersonEvent(@Body() payload: PersonEventRelationInput): Promise<PersonEventRelation> {
    return this.relationshipService.createPersonEvent(payload);
  }

  @Patch('person-events/:id')
  @UseGuards(AdminGuard)
  async updatePersonEvent(
    @Param('id') id: string,
    @Body() payload: Partial<PersonEventRelationInput>,
  ): Promise<PersonEventRelation> {
    return this.relationshipService.updatePersonEvent(id, payload);
  }

  @Delete('person-events/:id')
  @UseGuards(AdminGuard)
  async deletePersonEvent(@Param('id') id: string): Promise<{ id: string }> {
    return this.relationshipService.deletePersonEvent(id);
  }

  @Post('event-causalities')
  @UseGuards(AdminGuard)
  async createEventCausality(@Body() payload: EventCausalityRelationInput): Promise<EventCausalityRelation> {
    return this.relationshipService.createEventCausality(payload);
  }

  @Patch('event-causalities/:id')
  @UseGuards(AdminGuard)
  async updateEventCausality(
    @Param('id') id: string,
    @Body() payload: Partial<EventCausalityRelationInput>,
  ): Promise<EventCausalityRelation> {
    return this.relationshipService.updateEventCausality(id, payload);
  }

  @Delete('event-causalities/:id')
  @UseGuards(AdminGuard)
  async deleteEventCausality(@Param('id') id: string): Promise<{ id: string }> {
    return this.relationshipService.deleteEventCausality(id);
  }
}
