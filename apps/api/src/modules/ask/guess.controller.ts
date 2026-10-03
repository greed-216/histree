import { GatewayGuard } from '../../common/guards/gateway.guard';
import type { GatewayRequest } from '../../common/guards/gateway.guard';
import { UseGuards } from '@nestjs/common';
import { Body, Controller, Get, Post, Req, Res } from '@nestjs/common';
import type { Response } from 'express';
import { GuessService } from './guess.service';
@UseGuards(GatewayGuard)
@Controller('api/v1/ask/guess')
export class GuessController {
  constructor(private readonly service: GuessService) {}
  @Get('status') status() {
    return this.service.status();
  }
  private async request(
    req: GatewayRequest,
    res: Response,
    operation: (signal: AbortSignal) => Promise<unknown>,
  ) {
    res.set('Cache-Control', 'no-store');
    const controller = new AbortController();
    const close = () => controller.abort();
    res.on('close', close);
    try {
      return await operation(
        AbortSignal.any([controller.signal, AbortSignal.timeout(120000)]),
      );
    } finally {
      res.off('close', close);
    }
  }
  @Post('start') start(
    @Body() body: unknown,
    @Req() req: GatewayRequest,
    @Res({ passthrough: true }) res: Response,
  ) {
    return this.request(req, res, (signal) =>
      this.service.start(body, req.gatewayActor, signal),
    );
  }
  @Post('act') act(
    @Body() body: unknown,
    @Req() req: GatewayRequest,
    @Res({ passthrough: true }) res: Response,
  ) {
    return this.request(req, res, (signal) =>
      this.service.act(body, req.gatewayActor, signal),
    );
  }
}
