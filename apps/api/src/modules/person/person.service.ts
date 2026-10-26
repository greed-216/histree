import type { PageResult, Person } from '@histree/shared-types';
import { Injectable } from '@nestjs/common';
import { MysqlService } from '../mysql/mysql.service';
import { PersonDirectory } from './person-directory';

@Injectable()
export class PersonService {
  constructor(private mysqlService: MysqlService) {}

  facets() {
    return new PersonDirectory(this.mysqlService).facets();
  }
  async getPeople(
    query: Record<string, string> = {},
  ): Promise<PageResult<Person>> {
    return new PersonDirectory(this.mysqlService).list(query);
  }
}
