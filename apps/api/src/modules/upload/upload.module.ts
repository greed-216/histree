import { Module } from '@nestjs/common';
import { AdminGuard } from '../../common/guards/admin.guard';
import { UploadController } from './upload.controller';

@Module({
  controllers: [UploadController],
  providers: [AdminGuard],
})
export class UploadModule {}
