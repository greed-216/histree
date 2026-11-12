import { Module } from '@nestjs/common';
import { MediaController } from './media.controller';
import { StorageService } from './storage.service';

@Module({
  controllers: [MediaController],
  providers: [StorageService],
  exports: [StorageService],
})
export class StorageModule {}
