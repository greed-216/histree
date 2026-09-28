import type { SupabaseService } from '../../modules/supabase/supabase.service';
import { ForbiddenException, UnauthorizedException } from '@nestjs/common';
import type { ExecutionContext } from '@nestjs/common';
import { AdminGuard } from './admin.guard';
const context = (authorization?: string) =>
  ({
    switchToHttp: () => ({
      getRequest: () => ({ headers: { authorization } }),
    }),
  }) as ExecutionContext;
function guard(role = 'admin', valid = true) {
  class Query {
    select() {
      return this;
    }
    eq() {
      return this;
    }
    maybeSingle() {
      return Promise.resolve({ data: { role }, error: null });
    }
  }
  const query = new Query();
  return new AdminGuard({
    getAdminClient: () => ({
      auth: {
        getUser: () =>
          Promise.resolve({
            data: { user: valid ? { id: 'test' } : null },
            error: null,
          }),
      },
      from: () => query,
    }),
  } as unknown as SupabaseService);
}
describe('Editorial admin access', () => {
  it('rejects anonymous callers', async () => {
    await expect(guard().canActivate(context())).rejects.toBeInstanceOf(
      UnauthorizedException,
    );
  });
  it('rejects invalid tokens', async () => {
    await expect(
      guard('admin', false).canActivate(context('Bearer invalid')),
    ).rejects.toBeInstanceOf(UnauthorizedException);
  });
  it('rejects ordinary signed-in users', async () => {
    await expect(
      guard('user').canActivate(context('Bearer token')),
    ).rejects.toBeInstanceOf(ForbiddenException);
  });
  it('accepts verified admins', async () => {
    await expect(guard().canActivate(context('Bearer token'))).resolves.toBe(
      true,
    );
  });
});
