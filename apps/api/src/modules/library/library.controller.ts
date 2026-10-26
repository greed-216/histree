import { Controller, Get, Param, Query } from '@nestjs/common';
import { LibraryService } from './library.service';

@Controller('api/v1')
export class LibraryController {
  constructor(private readonly service: LibraryService) {}
  @Get('library') books() {
    return this.service.books();
  }
  @Get('library/search') search(
    @Query('q') q = '',
    @Query('book') book?: string,
    @Query('page') page?: string,
  ) {
    return this.service.search(q, book, page);
  }
  @Get('library/:book') book(@Param('book') book: string) {
    return this.service.book(book);
  }
  @Get('library/:book/sections/:section') section(
    @Param('book') book: string,
    @Param('section') section: string,
    @Query() options: { page?: string; paragraph?: string },
  ) {
    return this.service.section(book, section, options);
  }
  @Get('library/:book/sections/:section/links') links(
    @Param('book') book: string,
    @Param('section') section: string,
    @Query('paragraph') paragraph: string,
    @Query('page') page?: string,
  ) {
    return this.service.links(book, section, paragraph, page);
  }
  @Get('sources/:id/location') source(@Param('id') id: string) {
    return this.service.sourceLocation(id);
  }
}
