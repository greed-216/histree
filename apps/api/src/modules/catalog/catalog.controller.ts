import { Controller, Get, Query, Param } from '@nestjs/common';
import { MysqlService } from '../mysql/mysql.service';
import { CatalogService } from './catalog.service';

@Controller('api/v1')
export class CatalogController {
  constructor(private readonly service: CatalogService, private readonly mysql: MysqlService) {}
  @Get('sources/:id/text') sourceText(@Param('id') id: string) { return this.mysql.sourceText(id); }
  @Get('source-texts/resolve') resolveSourceText(@Query('archive') archive = '') { return this.mysql.resolveSourceText(archive); }
  @Get('topics') topics(@Query() query: Record<string, string>) {
    return this.service.topics(undefined, query);
  }
  @Get('topics/:slug') topic(@Param('slug') slug: string) {
    return this.service.topics(slug);
  }
  @Get('sources/:id') source(
    @Param('id') id: string,
    @Query('page') page?: string,
  ) {
    return this.service.source(id, Number(page ?? 0));
  }
  @Get('evidence/:subject/:id') evidence(
    @Param('subject') subject: string,
    @Param('id') id: string,
    @Query() query: Record<string, string>,
  ) {
    return this.service.evidence(subject, id, query);
  }
}
