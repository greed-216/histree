import {
  BadRequestException,
  Injectable,
  Logger,
  NotFoundException,
  ServiceUnavailableException,
} from '@nestjs/common';
import { OssImages, imageKey, ossErrorCode, prepareImage } from './oss-images';

@Injectable()
export class StorageService {
  private store?: OssImages;
  private readonly logger = new Logger(StorageService.name);

  private images() {
    try {
      return (this.store ??= new OssImages());
    } catch {
      throw new ServiceUnavailableException('图片存储尚未配置');
    }
  }

  async upload(buffer: Buffer, contentType?: string) {
    try {
      prepareImage(buffer, contentType);
    } catch (error) {
      throw new BadRequestException((error as Error).message);
    }
    try {
      return await this.images().upload(buffer, contentType);
    } catch (error) {
      return this.unavailable(error);
    }
  }

  async read(file: string) {
    try {
      imageKey(file);
    } catch {
      throw new NotFoundException('图片不存在');
    }
    try {
      return await this.images().read(file);
    } catch (error) {
      if (ossErrorCode(error) === 'NoSuchKey')
        throw new NotFoundException('图片不存在');
      return this.unavailable(error);
    }
  }

  private unavailable(error: unknown): never {
    this.logger.warn(`OSS request failed: ${ossErrorCode(error)}`);
    throw new ServiceUnavailableException('图片存储暂不可用，请稍后重试');
  }
}
