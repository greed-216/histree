import type { PageResult, Person } from '@histree/shared-types';
import { Controller, Get, Query } from '@nestjs/common';
import { PersonService } from './person.service';

@Controller('api/v1/people')
export class PersonController {
  constructor(private readonly personService: PersonService) {}

  @Get('facets') facets() {
    return this.personService.facets();
  }
  @Get()
  async getPeople(
    @Query() query: Record<string, string>,
  ): Promise<PageResult<Person>> {
    return this.personService.getPeople(query);
  }
}
