import { Test } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import type { NestExpressApplication } from '@nestjs/platform-express';
import request from 'supertest';
import { GatewayGuard } from '../../common/guards/gateway.guard';
import { MysqlService } from '../mysql/mysql.service';
import { AiAccessService } from './ai-access.service';
import { GuessClueController } from './guess-clue.controller';
import { GuessClueGameService } from './guess-clue-game.service';
import { GuessController } from './guess.controller';
import { GuessService } from './guess.service';

describe('cached clue HTTP requests without AI quota', () => {
  let app: NestExpressApplication, token: string, debit: jest.Mock;
  const state = { clues: ['第一条线索'], total: 6, unlocked: 1 };
  const clues = {
    status: jest.fn(async () => ({ available: true, preparedPeople: 1 })),
    start: jest.fn(async () => state),
    act: jest.fn(async () => state),
    feedback: jest.fn(async () => state),
  };
  const questions = {
    status: () => ({ available: true }),
    start: jest.fn(async () => ({})),
    act: jest.fn(async () => ({})),
    feedback: jest.fn(async () => ({})),
  };
  beforeEach(async () => {
    jest.clearAllMocks();
    debit = jest.fn().mockResolvedValue(true);
    const module = await Test.createTestingModule({
      controllers: [GuessClueController, GuessController],
      providers: [
        GatewayGuard,
        AiAccessService,
        { provide: MysqlService, useValue: { enabled: true, consumeQuota: debit } },
        { provide: ConfigService, useValue: new ConfigService({ HISTREE_GATEWAY_SECRET: 'a'.repeat(64) }) },
        { provide: GuessClueGameService, useValue: clues },
        { provide: GuessService, useValue: questions },
      ],
    }).compile();
    token = (await module.get(AiAccessService).issueSession()).token;
    debit.mockClear();
    app = module.createNestApplication<NestExpressApplication>({ rawBody: true });
    await app.init();
  });
  afterEach(async () => { await app.close(); });
  const post = (path: string) => request(app.getHttpServer())
    .post(path).set('x-histree-anonymous', token);

  it('allows more than 80 clue operations even when AI quota is exhausted and binds the signed actor', async () => {
    debit.mockResolvedValue(false);
    for (let i = 0; i < 30; i++) {
      await post('/api/v1/ask/guess/clues/start').send({ difficulty: 'easy' }).expect(201);
      await post('/api/v1/ask/guess/clues/act').send({ action: 'hint', expectedUnlocked: 1 }).expect(201);
      await post('/api/v1/ask/guess/clues/feedback').send({ rating: 'right' }).expect(201);
    }
    expect(debit).not.toHaveBeenCalled();
    for (const operation of [clues.start, clues.act, clues.feedback]) {
      expect(operation).toHaveBeenCalledTimes(30);
      expect(operation).toHaveBeenCalledWith(
        expect.any(Object), `anon:${token.split('.')[0]}`, expect.any(AbortSignal),
      );
    }
  });

  it('streams cached starts on mixed-case routes without depending on the quota store', async () => {
    debit.mockRejectedValue(new Error('quota store unavailable'));
    const response = await post('/API/V1/ASK/GUESS/CLUES/START/')
      .set('Accept', 'application/x-ndjson').send({ difficulty: 'easy' })
      .expect(200).expect('Content-Type', /application\/x-ndjson/);
    expect(JSON.parse(response.text.trim())).toEqual({ type: 'result', state });
    for (const path of ['act', 'feedback'])
      await post(`/API/V1/ASK/GUESS/CLUES/${path.toUpperCase()}/`).send({}).expect(201);
    expect(debit).not.toHaveBeenCalled();
  });

  it.each(['start', 'act', 'feedback'])('keeps identity and origin checks on clue %s', async (path) => {
    const url = `/api/v1/ask/guess/clues/${path}`;
    await request(app.getHttpServer()).post(url).send({}).expect(401);
    await request(app.getHttpServer()).post(url)
      .set('x-histree-anonymous', 'forged').set('x-histree-actor', 'anon:' + 'b'.repeat(64))
      .send({}).expect(401);
    await post(url).set('Origin', 'https://attacker.example').send({}).expect(403);
    expect(clues[path as 'start' | 'act' | 'feedback']).not.toHaveBeenCalled();
    expect(debit).not.toHaveBeenCalled();
  });

  it('keeps request validation before admitting cached operations', async () => {
    const url = '/api/v1/ask/guess/clues/start';
    await post(url).set('Content-Type', 'text/plain').send('fixture').expect(415);
    await post(url).send([]).expect(400);
    await post(url).send({ text: 'a'.repeat(17000) }).expect(413);
    await post(url + '?upstream=evil').send({}).expect(404);
    expect(clues.start).not.toHaveBeenCalled();
    expect(debit).not.toHaveBeenCalled();
  });

  it.each(['start', 'act', 'feedback'])('still blocks question-mode %s when its AI quota is exhausted', async (path) => {
    debit.mockResolvedValue(false);
    await post(`/API/V1/ASK/GUESS/${path.toUpperCase()}/`).send({}).expect(429);
    expect(debit).toHaveBeenCalledWith(`anon:${token.split('.')[0]}`, 'guess');
    expect(questions[path as 'start' | 'act' | 'feedback']).not.toHaveBeenCalled();
  });
});
