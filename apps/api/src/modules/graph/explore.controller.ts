import {
  BadRequestException,
  Controller,
  Get,
  NotFoundException,
  Param,
  Query,
} from '@nestjs/common';
import {
  exploreRequest,
  contentRequest,
  pageNumber,
} from '@histree/shared-types';
import { SupabaseService } from '../supabase/supabase.service';

@Controller('api/v1')
export class ExploreController {
  constructor(private readonly supabase: SupabaseService) {}

  @Get('search')
  search(@Query() query: Record<string, string>) {
    return this.read(`/search?${new URLSearchParams(query)}`);
  }

  @Get('graph-slice/:id')
  graph(@Param('id') id: string, @Query() query: Record<string, string>) {
    return this.read(`/graph-slice/${id}?${new URLSearchParams(query)}`);
  }

  @Get('entry/:id')
  entry(@Param('id') id: string) {
    return this.read(`/entry/${id}`);
  }

  @Get('catalog/:table')
  async catalog(
    @Param('table') table: string,
    @Query() query: Record<string, string>,
  ) {
    let args: ReturnType<typeof contentRequest>;
    try {
      args = contentRequest(`/catalog/${table}?${new URLSearchParams(query)}`);
    } catch {
      throw new BadRequestException('查询参数无效');
    }
    const { data, error } = await this.supabase
      .getClient()
      .rpc('content_page', args);
    if (error) throw error;
    return data;
  }

  @Get('entry-context/:id')
  async context(@Param('id') id: string, @Query('page') page?: string) {
    let offset: number;
    try {
      exploreRequest(`/entry/${id}`);
      offset = pageNumber(page);
    } catch {
      throw new BadRequestException('查询参数无效');
    }
    const { data, error } = await this.supabase
      .getClient()
      .rpc('entry_context', { p_id: id, p_page: offset });
    if (error) throw error;
    if (!data) throw new NotFoundException('条目尚未发布或不存在');
    return data;
  }

  private async read(path: string) {
    let request: ReturnType<typeof exploreRequest>;
    try {
      request = exploreRequest(path);
    } catch {
      throw new BadRequestException('查询参数无效');
    }
    if (!request) throw new BadRequestException('查询地址无效');
    const { data, error } = await this.supabase
      .getClient()
      .rpc(request.name, request.args);
    if (error) throw error;
    if (!data) throw new NotFoundException('条目尚未发布或不存在');
    return data;
  }
}
