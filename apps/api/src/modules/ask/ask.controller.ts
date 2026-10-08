import { GatewayGuard } from '../../common/guards/gateway.guard';
import type { GatewayRequest } from '../../common/guards/gateway.guard';
import { UseGuards } from '@nestjs/common';
import { Body, Controller, Get, Post, Req, Res } from '@nestjs/common';
import type { Response } from 'express';
import { AiAccessService } from './ai-access.service';
import { AskService } from './ask.service';

@UseGuards(GatewayGuard)
@Controller('api/v1/ask')
export class AskController {
  constructor(private readonly service: AskService, private readonly access: AiAccessService) {}
  @Get('status') status() {
    const status = this.service.status();
    return { ...status, available: status.available && this.access.ready() };
  }
  @Post('session') async session(@Res({ passthrough: true }) res: Response) {
    res.set('Cache-Control', 'no-store');
    return this.access.issueSession();
  }
  @Post() async ask(
    @Body() body: unknown,
    @Req() req: GatewayRequest,
    @Res() res: Response,
  ) {
    const ticket = this.service.reserve(body, req.gatewayActor);
    res
      .status(200)
      .set({
        'Content-Type': 'application/x-ndjson; charset=utf-8',
        'Cache-Control': 'no-store',
        'X-Accel-Buffering': 'no',
      });
    res.flushHeaders();
    const abort = new AbortController();
    const close = () => abort.abort();
    res.on('close', close);
    const heartbeat = setInterval(() => {
      if (!res.destroyed) res.write('\n');
    }, 15000);
    try {
      await this.service.run(ticket, abort.signal, (event) => {
        if (!res.destroyed) res.write(`${JSON.stringify(event)}\n`);
      });
    } finally {
      clearInterval(heartbeat);
      res.off('close', close);
      if (!res.destroyed) res.end();
    }
  }
}
