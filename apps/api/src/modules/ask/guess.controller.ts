import {
  Body,
  Controller,
  ForbiddenException,
  Get,
  Post,
  Req,
  Res,
} from '@nestjs/common';
import type { Request, Response } from 'express';
import { GuessService } from './guess.service';
@Controller('api/v1/ask/guess')
export class GuessController {
  constructor(private readonly service: GuessService) {}
  @Get('status') status() {
    return this.service.status();
  }
  private async request(
    req: Request,
    res: Response,
    operation: (signal: AbortSignal) => Promise<unknown>,
  ) {
    const origin = req.headers.origin;
    if (
      origin &&
      ![
        'https://greed-216.github.io',
        'http://localhost:5173',
        'http://127.0.0.1:5174',
      ].includes(origin)
    )
      throw new ForbiddenException('不允许此来源操作游戏');
    res.set('Cache-Control', 'no-store');
    const controller = new AbortController();
    const close = () => controller.abort();
    res.on('close', close);
    try {
      return await operation(
        AbortSignal.any([controller.signal, AbortSignal.timeout(150000)]),
      );
    } finally {
      res.off('close', close);
    }
  }
  @Post('start') start(
    @Body() body: unknown,
    @Req() req: Request,
    @Res({ passthrough: true }) res: Response,
  ) {
    return this.request(req, res, (signal) =>
      this.service.start(body, req.ip || 'unknown', signal),
    );
  }
  @Post('act') act(
    @Body() body: unknown,
    @Req() req: Request,
    @Res({ passthrough: true }) res: Response,
  ) {
    return this.request(req, res, (signal) =>
      this.service.act(body, req.ip || 'unknown', signal),
    );
  }
}
