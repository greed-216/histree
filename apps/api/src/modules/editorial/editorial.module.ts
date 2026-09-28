import { Module } from '@nestjs/common';
import { EditorialService } from './editorial.service';
import { EditorialController } from './editorial.controller';
@Module({ controllers: [EditorialController], providers: [EditorialService] })
export class EditorialModule {}
