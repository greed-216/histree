import { Test } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import type { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { AskController } from './ask.controller';
import { GuessController } from './guess.controller';
import { AskService } from './ask.service';
import { GuessService } from './guess.service';
import { GatewayGuard } from '../../common/guards/gateway.guard';
describe('ECS HTTP gateway boundary', () => {
  let app: INestApplication;
  const secret = 'a'.repeat(64),
    actor = 'anon:' + 'b'.repeat(64);
  const ask = {
    status: () => ({ available: true }),
    reserve: jest.fn(() => ({})),
    run: jest.fn(async (_ticket, _signal, emit) =>
      emit({ type: 'result', answer: 'ok' }),
    ),
  };
  const guess = {
    status: () => ({ available: true }),
    start: jest.fn(async () => ({ remaining: 30 })),
    act: jest.fn(async () => ({ remaining: 29 })),
  };
  beforeAll(async () => {
    const module = await Test.createTestingModule({
      controllers: [AskController, GuessController],
      providers: [
        GatewayGuard,
        {
          provide: ConfigService,
          useValue: new ConfigService({ HISTREE_GATEWAY_SECRET: secret }),
        },
        { provide: AskService, useValue: ask },
        { provide: GuessService, useValue: guess },
      ],
    }).compile();
    app = module.createNestApplication();
    await app.init();
  });
  afterAll(async () => {
    await app.close();
  });
  it('blocks public access to both status and paid operations', async () => {
    for (const path of ['/api/v1/ask/status', '/api/v1/ask/guess/status'])
      await request(app.getHttpServer()).get(path).expect(401);
    for (const path of [
      '/api/v1/ask',
      '/api/v1/ask/guess/start',
      '/api/v1/ask/guess/act',
    ])
      await request(app.getHttpServer())
        .post(path)
        .send({})
        .set('x-histree-actor', actor)
        .expect(401);
    expect(ask.reserve).not.toHaveBeenCalled();
    expect(guess.start).not.toHaveBeenCalled();
  });
  it('passes only a service-authenticated actor to the business services and retains NDJSON', async () => {
    await request(app.getHttpServer())
      .get('/api/v1/ask/status')
      .set('x-histree-gateway-key', secret)
      .expect(200);
    const response = await request(app.getHttpServer())
      .post('/api/v1/ask')
      .set('x-histree-gateway-key', secret)
      .set('x-histree-actor', actor)
      .send({ question: 'hello' })
      .expect(200);
    expect(ask.reserve).toHaveBeenCalledWith({ question: 'hello' }, actor);
    expect(response.headers['content-type']).toContain('application/x-ndjson');
    expect(response.text).toContain('"type":"result"');
    await request(app.getHttpServer())
      .post('/api/v1/ask/guess/start')
      .set('x-histree-gateway-key', secret)
      .set('x-histree-actor', actor)
      .send({ difficulty: 2 })
      .expect(200);
    expect(guess.start.mock.calls[0][1]).toBe(actor);
  });
});
