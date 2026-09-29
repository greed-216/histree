import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // Render terminates requests at one trusted proxy; local development leaves this off.
  if (process.env.TRUST_PROXY === '1') app.getHttpAdapter().getInstance().set('trust proxy', 1);
  app.enableCors(); // Enable CORS for the frontend demo
  const port = process.env.PORT || 3000;
  await app.listen(port);
}
bootstrap();
