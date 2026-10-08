import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { NestExpressApplication } from '@nestjs/platform-express';
import { configureWebHosting } from './web-hosting';

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule, { rawBody: true });
  // ECS nginx terminates requests at one trusted proxy.
  if (process.env.TRUST_PROXY === '1') app.getHttpAdapter().getInstance().set('trust proxy', 1);
  app.enableCors(); // Enable CORS for the frontend demo
  if (process.env.HISTREE_WEB_ROOT) configureWebHosting(app, process.env.HISTREE_WEB_ROOT);
  const port = process.env.PORT || 3000;
  await app.listen(port);
}
bootstrap();
