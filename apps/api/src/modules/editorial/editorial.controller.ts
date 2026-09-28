import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Patch,
  Post,
  UseGuards,
} from '@nestjs/common';
import { AdminGuard } from '../../common/guards/admin.guard';
import { EditorialService } from './editorial.service';

@Controller('api/v1')
export class EditorialController {
  constructor(private readonly service: EditorialService) {}
  @Get('topics') topics() {
    return this.service.topics();
  }
  @Get('topics/:slug') topic(@Param('slug') slug: string) {
    return this.service.topics(slug);
  }
  @Get('evidence/:subject/:id') evidence(
    @Param('subject') subject: string,
    @Param('id') id: string,
  ) {
    return this.service.evidence(subject, id);
  }
  @Get('editorial/:table')
  @UseGuards(AdminGuard)
  list(@Param('table') table: string) {
    return this.service.list(table);
  }
  @Post('editorial/:table')
  @UseGuards(AdminGuard)
  create(@Param('table') table: string, @Body() body: Record<string, unknown>) {
    return this.service.save(table, body);
  }
  @Patch('editorial/:table/:id')
  @UseGuards(AdminGuard)
  update(
    @Param('table') table: string,
    @Param('id') id: string,
    @Body() body: Record<string, unknown>,
  ) {
    return this.service.save(table, body, id);
  }
  @Delete('editorial/:table/:id')
  @UseGuards(AdminGuard)
  remove(@Param('table') table: string, @Param('id') id: string) {
    return this.service.remove(table, id);
  }
}
