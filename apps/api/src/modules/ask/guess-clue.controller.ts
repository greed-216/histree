import {
  Body,
  Controller,
  Get,
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
    return this.request(res, (signal) =>
      this.service.start(body, req.gatewayActor, signal),
    );
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
