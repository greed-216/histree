import { Controller, Get, ServiceUnavailableException } from '@nestjs/common';
import { MysqlService } from './modules/mysql/mysql.service';
@Controller('api/v1')
export class AppController {
  constructor(private readonly database: MysqlService) {}
  @Get('health') async health() {
    try { await this.database.rows('SELECT 1 AS alive', [], AbortSignal.timeout(4000)); }
    catch { throw new ServiceUnavailableException('Database unavailable'); }
    return {status:'ok',database:'mysql'};
  }
}
