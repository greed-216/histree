import { Body, Controller, Get, Post, Req, Res, ForbiddenException } from '@nestjs/common';
import type { Request, Response } from 'express';
import { AskService } from './ask.service';

@Controller('api/v1/ask')
export class AskController {
  constructor(private readonly service: AskService) {}
  @Get('status') status() { return this.service.status(); }
  @Post() async ask(@Body() body: unknown, @Req() req: Request, @Res() res: Response) {
    const origin = req.headers.origin;
    if (origin && !['https://greed-216.github.io', 'http://localhost:5173', 'http://127.0.0.1:5174'].includes(origin)) throw new ForbiddenException('不允许此来源提问');
    const ticket = this.service.reserve(body, req.ip || 'unknown');
    res.status(200).set({ 'Content-Type': 'application/x-ndjson; charset=utf-8', 'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no' });
    res.flushHeaders();
    const abort = new AbortController();
    const close = () => abort.abort();
    res.on('close', close);
    const heartbeat = setInterval(() => { if (!res.destroyed) res.write('\n'); }, 15000);
    try {
      await this.service.run(ticket, abort.signal, event => { if (!res.destroyed) res.write(`${JSON.stringify(event)}\n`); });
    } finally {
      clearInterval(heartbeat);
      res.off('close', close);
      if (!res.destroyed) res.end();
    }
  }
}
