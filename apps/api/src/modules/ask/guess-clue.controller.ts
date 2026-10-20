import {
  Body,
  Controller,
  Get,
  HttpException,
  Post,
  Req,
  Res,
  UseGuards,
} from '@nestjs/common';
import type { Response } from 'express';
import {
  GatewayGuard,
  type GatewayRequest,
} from '../../common/guards/gateway.guard';
import { AiAccessService } from './ai-access.service';
import { GuessClueGameService } from './guess-clue-game.service';

@UseGuards(GatewayGuard)
@Controller('api/v1/ask/guess/clues')
export class GuessClueController {
  constructor(
    private readonly service: GuessClueGameService,
    private readonly access: AiAccessService,
  ) {}
  @Get('status') async status() {
    const s = await this.service.status(AbortSignal.timeout(10000));
    return { ...s, available: s.available && this.access.ready() };
  }
  private async request(
    res: Response,
    operation: (signal: AbortSignal) => Promise<unknown>,
  ) {
    res.set('Cache-Control', 'no-store');
    const controller = new AbortController();
    const close = () => controller.abort();
    res.on('close', close);
    try {
      return await operation(
        AbortSignal.any([controller.signal, AbortSignal.timeout(125000)]),
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
    if (req.headers.accept?.includes('application/x-ndjson'))
      return this.streamStart(body, req.gatewayActor, res);
    return this.request(res, (signal) =>
      this.service.start(body, req.gatewayActor, signal),
    );
  }
  private async streamStart(body: unknown, actor: string, res: Response) {
    res
      .status(200)
      .set({
        'Content-Type': 'application/x-ndjson; charset=utf-8',
        'Cache-Control': 'no-store',
        'X-Accel-Buffering': 'no',
      });
    res.flushHeaders();
    const controller = new AbortController();
    const close = () => controller.abort();
    res.on('close', close);
    const send = (value: unknown) => {
      if (!res.destroyed && !res.writableEnded)
        res.write(JSON.stringify(value) + '\n');
    };
    const heartbeat = setInterval(() => send({ type: 'heartbeat' }), 10000);
    heartbeat.unref();
    try {
      const state = await this.service.start(
        body,
        actor,
        AbortSignal.any([controller.signal, AbortSignal.timeout(120000)]),
        (message) => send({ type: 'status', message }),
      );
      send({ type: 'result', state });
    } catch (error) {
      if (!controller.signal.aborted)
        send({
          type: 'error',
          status: error instanceof HttpException ? error.getStatus() : 503,
          message:
            error instanceof HttpException
              ? error.message
              : '本次准备尚未完成，已取得的线索会保留，请稍后重试。',
        });
    } finally {
      clearInterval(heartbeat);
      res.off('close', close);
      res.end();
    }
  }
  @Post('feedback') feedback(
    @Body() body: unknown,
    @Req() req: GatewayRequest,
    @Res({ passthrough: true }) res: Response,
  ) {
    return this.request(res, (signal) =>
      this.service.feedback(body, req.gatewayActor, signal),
    );
  }
  @Post('act') act(
    @Body() body: unknown,
    @Req() req: GatewayRequest,
    @Res({ passthrough: true }) res: Response,
  ) {
    return this.request(res, (signal) =>
      this.service.act(body, req.gatewayActor, signal),
    );
  }
}
