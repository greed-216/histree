import { Body, Controller, Post, Req, Res } from '@nestjs/common';
import type { Request, Response } from 'express';
import { FeedbackService } from './feedback.service';

@Controller('api/v1/feedback')
export class FeedbackController {
  constructor(private readonly service: FeedbackService) {}
  @Post() submit(@Body() body: unknown, @Req() request: Request, @Res({ passthrough: true }) response: Response) {
    response.set('Cache-Control', 'no-store');
    return this.service.submit(body, request.ip || request.socket.remoteAddress || 'unknown');
  }
}
