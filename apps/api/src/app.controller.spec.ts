import { AppController } from './app.controller';
import { MysqlService } from './modules/mysql/mysql.service';
describe('application readiness',()=>{
  it('reports database readiness independently of AI',async()=>{
    const rows=jest.fn().mockResolvedValue([{alive:1}]);const controller=new AppController({rows} as unknown as MysqlService);
    await expect(controller.health()).resolves.toEqual({status:'ok',database:'mysql'});expect(rows).toHaveBeenCalledTimes(1);
    rows.mockRejectedValue(new Error('private credentials in error'));await expect(controller.health()).rejects.toMatchObject({status:503,message:'Database unavailable'});
  });
});
