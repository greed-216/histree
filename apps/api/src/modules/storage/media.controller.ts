import { Controller, Get, Param, Res, StreamableFile } from '@nestjs/common';
import type { Response } from 'express';
import { StorageService } from './storage.service';
import { IMAGE_CACHE_CONTROL, imageType } from './oss-images';

@Controller('api/v1/media')
export class MediaController {
  constructor(private readonly storage: StorageService) {}

  @Get('images/:file')
  async image(
    @Param('file') file: string,
    @Res({ passthrough: true }) response: Response,
  ) {
    const { stream, res } = await this.storage.read(file);
    response.set({
      'Cache-Control': IMAGE_CACHE_CONTROL,
      'X-Content-Type-Options': 'nosniff',
    });
    return new StreamableFile(stream, {
      type: imageType(file),
      disposition: 'inline',
      length:
        Number((res.headers as Record<string, string>)['content-length']) ||
        undefined,
    });
  }
}
