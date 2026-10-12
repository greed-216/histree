import { Module } from '@nestjs/common';
import { MysqlModule } from '../mysql/mysql.module';
import { RelationshipController } from './relationship.controller';
import { RelationshipService } from './relationship.service';

@Module({
  imports: [MysqlModule],
  controllers: [RelationshipController],
  providers: [RelationshipService],
})
export class RelationshipModule {}
