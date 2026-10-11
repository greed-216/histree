import { Controller, Get, Param, Query } from '@nestjs/common';
import { PersonService } from './person.service';
import type { Person, PageResult } from '@histree/shared-types';

@Controller('api/v1/people')
export class PersonController {
  constructor(private readonly personService: PersonService) {}

  @Get()
  async getPeople(
    @Query() query: Record<string, string>,
  ): Promise<PageResult<Person>> {
    return this.personService.getPeople(query);
  }

}
