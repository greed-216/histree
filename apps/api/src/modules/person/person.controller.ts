import { Body, Controller, Delete, Get, Param, Patch, Post, UseGuards } from '@nestjs/common';
import { AdminGuard } from '../../common/guards/admin.guard';
import { PersonService } from './person.service';
import type { Person } from '@histree/shared-types';

@Controller('api/v1/people')
export class PersonController {
  constructor(private readonly personService: PersonService) {}

  @Get()
  async getPeople(): Promise<Person[]> {
    return this.personService.getPeople();
  }

  @Post()
  @UseGuards(AdminGuard)
  async createPerson(@Body() payload: Partial<Person>): Promise<Person> {
    return this.personService.createPerson(payload);
  }

  @Patch(':id')
  @UseGuards(AdminGuard)
  async updatePerson(@Param('id') id: string, @Body() payload: Partial<Person>): Promise<Person> {
    return this.personService.updatePerson(id, payload);
  }

  @Delete(':id')
  @UseGuards(AdminGuard)
  async deletePerson(@Param('id') id: string): Promise<{ id: string }> {
    return this.personService.deletePerson(id);
  }
}
