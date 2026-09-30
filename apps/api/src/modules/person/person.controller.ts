import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Patch,
  Post,
  Query,
  UseGuards,
} from '@nestjs/common';
import { AdminGuard } from '../../common/guards/admin.guard';
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

  @Post()
  @UseGuards(AdminGuard)
  async createPerson(@Body() payload: Partial<Person>): Promise<Person> {
    return this.personService.createPerson(payload);
  }

  @Patch(':id')
  @UseGuards(AdminGuard)
  async updatePerson(
    @Param('id') id: string,
    @Body() payload: Partial<Person>,
  ): Promise<Person> {
    return this.personService.updatePerson(id, payload);
  }

  @Delete(':id')
  @UseGuards(AdminGuard)
  async deletePerson(@Param('id') id: string): Promise<{ id: string }> {
    return this.personService.deletePerson(id);
  }
}
