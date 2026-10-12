import { RelationshipService } from './relationship.service';
import { MysqlService } from '../mysql/mysql.service';
describe('public relationship bundle', () => {
  it('reads three bounded public pages and propagates continuation', async () => {
    const rpc = jest.fn(async (_name, args) => ({data:{items:[{id:args.p_table}],has_more:args.p_table==='person_event'},error:null}));
    const service = new RelationshipService({getClient:()=>({rpc})} as unknown as MysqlService);
    const result = await service.getRelationships({page:'2'});
    expect(result.has_more).toBe(true);expect(result.person_events).toEqual([{id:'person_event'}]);
    expect(rpc).toHaveBeenCalledTimes(3);
    for (const call of rpc.mock.calls) expect(call[1]).toMatchObject({p_page:2,p_admin:false});
  });
});
