import { Controller, Post, UseInterceptors, UploadedFile, HttpException, HttpStatus } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { SupabaseService } from '../supabase/supabase.service';
import { v4 as uuidv4 } from 'uuid';

@Controller('api/v1/upload')
export class UploadController {
  constructor(private readonly supabaseService: SupabaseService) {}

  @Post()
  @UseInterceptors(FileInterceptor('file'))
  async uploadFile(@UploadedFile() file: Express.Multer.File) {
    if (!file) {
      throw new HttpException('No file provided', HttpStatus.BAD_REQUEST);
    }

    const adminClient = this.supabaseService.getAdminClient();
    const fileExt = file.originalname.split('.').pop() || 'png';
    const fileName = `${uuidv4()}.${fileExt}`;

    const { data, error } = await adminClient.storage
      .from('images')
      .upload(fileName, file.buffer, {
        contentType: file.mimetype,
        upsert: false,
      });

    if (error) {
      throw new HttpException(error.message, HttpStatus.INTERNAL_SERVER_ERROR);
    }

    const { data: publicUrlData } = adminClient.storage.from('images').getPublicUrl(fileName);

    return {
      url: publicUrlData.publicUrl,
    };
  }
}
