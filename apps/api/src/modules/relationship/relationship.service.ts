import { Injectable } from '@nestjs/common';
import { readContentPage } from '../../common/pagination';
import type { RelationshipBundle } from '@histree/shared-types';
import { MysqlService } from '../mysql/mysql.service';
@Injectable()
export class RelationshipService {
  constructor(private readonly mysqlService: MysqlService) {}

  async getRelationships(
    query: Record<string, string> = {},
  ): Promise<RelationshipBundle> {
    const client = this.mysqlService.getClient();
    const [p, pe, e] = await Promise.all(
      ['person_relationship', 'person_event', 'event_causality'].map((table) =>
        readContentPage(client, table, query),
      ),
    );
    return {
      person_relationships: p.items,
      person_events: pe.items,
      event_causalities: e.items,
      has_more: p.has_more || pe.has_more || e.has_more,
    };
  }

}
