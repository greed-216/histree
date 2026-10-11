import { Global, Module } from '@nestjs/common';
import { MysqlService } from './mysql.service';
import { MysqlReadController } from './mysql.controller';
@Global()
@Module({controllers:[MysqlReadController],providers:[MysqlService],exports:[MysqlService]})
export class MysqlModule {}
