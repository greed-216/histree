import { Controller, Post, UseInterceptors, UploadedFile, HttpException, HttpStatus, Headers } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { SupabaseService } from '../supabase/supabase.service';
import { v4 as uuidv4 } from 'uuid';

@Controller('api/v1/upload')
export class UploadController {
  constructor(private readonly supabaseService: SupabaseService) {}

  @Post()
  @UseInterceptors(
    FileInterceptor('file', {
      limits: { fileSize: 5 * 1024 * 1024 },
      fileFilter: (_req, file, cb) => {
        if (!file.mimetype?.startsWith('image/')) {
          cb(new HttpException('Only image uploads are allowed', HttpStatus.BAD_REQUEST), false);
          return;
        }
        cb(null, true);
      },
    }),
  )
  async uploadFile(@UploadedFile() file: Express.Multer.File, @Headers('authorization') authorization?: string) {
    if (!file) {
      throw new HttpException('No file provided', HttpStatus.BAD_REQUEST);
    }

    const adminClient = this.supabaseService.getAdminClient();
    const token = authorization?.startsWith('Bearer ') ? authorization.slice('Bearer '.length) : undefined;
    if (!token) {
      throw new HttpException('Unauthorized', HttpStatus.UNAUTHORIZED);
    }

    const { data: userData, error: userError } = await adminClient.auth.getUser(token);
    if (userError || !userData?.user) {
      throw new HttpException('Unauthorized', HttpStatus.UNAUTHORIZED);
    }

    const { data: roleData } = await adminClient
      .from('user_roles')
      .select('role')
      .eq('user_id', userData.user.id)
      .single();

    if (roleData?.role !== 'admin') {
      throw new HttpException('Forbidden', HttpStatus.FORBIDDEN);
    }

    const fileExt = file.originalname.split('.').pop() || 'png';
    const fileName = `${uuidv4()}.${fileExt}`;

    const { error } = await adminClient.storage
      .from('images')
      .upload(fileName, file.buffer, {
        contentType: file.mimetype,
        upsert: false,
      });

    if (error) {
      if (error.message?.toLowerCase().includes('bucket') && error.message?.toLowerCase().includes('not found')) {
        const { error: createBucketError } = await adminClient.storage.createBucket('images', { public: true });
        if (createBucketError) {
          throw new HttpException(createBucketError.message, HttpStatus.INTERNAL_SERVER_ERROR);
        }

        const { error: retryError } = await adminClient.storage
          .from('images')
          .upload(fileName, file.buffer, {
            contentType: file.mimetype,
            upsert: false,
          });

        if (retryError) {
          throw new HttpException(retryError.message, HttpStatus.INTERNAL_SERVER_ERROR);
        }
      } else {
      throw new HttpException(error.message, HttpStatus.INTERNAL_SERVER_ERROR);
      }
    }

    const { data: publicUrlData } = adminClient.storage.from('images').getPublicUrl(fileName);

    return {
      url: publicUrlData.publicUrl,
    };
  }
}
