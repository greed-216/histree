import { Controller, Get, Query, Param } from '@nestjs/common';
import { CatalogService } from './catalog.service';

@Controller('api/v1')
export class CatalogController {
  constructor(private readonly service: CatalogService) {}
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
