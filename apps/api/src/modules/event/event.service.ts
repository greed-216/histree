import { readContentPage, validPage } from '../../common/pagination';
import {
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import type {
  EventDetail,
  Event,
  EntryContext,
  PageResult,
} from '@histree/shared-types';
import { MysqlService } from '../mysql/mysql.service';

@Injectable()
export class EventService {
  constructor(private mysqlService: MysqlService) {}

  async getEvents(
    query: Record<string, string> = {},
  ): Promise<PageResult<Event>> {
    return readContentPage(this.mysqlService.getClient(), 'event', query);
  }

  async getEventDetail(eventId: string, page?: string): Promise<EventDetail> {
    const { data, error } = await this.mysqlService
      .getClient()
      .rpc('entry_context', { p_id: eventId, p_page: validPage(page) });
    if (error) throw error;
    const context = data as EntryContext | null;
    if (!context || context.center.type !== 'event')
      throw new NotFoundException('Event not found');
    const nodes = new Map(context.nodes.map((n) => [n.id, n]));
    return {
      ...context.center,
      related_people: context.edges
        .filter((e) => e.subject_table === 'person_event')
        .flatMap((e) => {
          const person = nodes.get(e.source);
          return person?.type === 'person' ? [{ person, role: e.type }] : [];
        }),
      cause_events: context.edges
        .filter(
          (e) => e.subject_table === 'event_causality' && e.target === eventId,
        )
        .flatMap((e) => {
          const event = nodes.get(e.source);
          return event?.type === 'event' ? [event] : [];
        }),
      effect_events: context.edges
        .filter(
          (e) => e.subject_table === 'event_causality' && e.source === eventId,
        )
        .flatMap((e) => {
          const event = nodes.get(e.target);
          return event?.type === 'event' ? [event] : [];
        }),
      has_more: context.has_more,
    };
  }

}
