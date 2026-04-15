import { Controller, Get } from '@nestjs/common';
import { PersonService } from './person.service';
import type { Person } from '@histree/shared-types';

@Controller('api/v1/people')
export class PersonController {
  constructor(private readonly personService: PersonService) {}

  @Get()
  async getPeople(): Promise<Person[]> {
    return this.personService.getPeople();
  }
}
