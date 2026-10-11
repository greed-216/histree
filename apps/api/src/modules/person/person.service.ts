import { readContentPage } from '../../common/pagination';
import {
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import type { Person, PageResult } from '@histree/shared-types';
import { MysqlService } from '../mysql/mysql.service';

@Injectable()
export class PersonService {
  constructor(private mysqlService: MysqlService) {}

  async getPeople(
    query: Record<string, string> = {},
  ): Promise<PageResult<Person>> {
    return readContentPage(this.mysqlService.getClient(), 'person', query);
  }

}
