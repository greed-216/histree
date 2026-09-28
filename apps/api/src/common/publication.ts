import { BadRequestException } from '@nestjs/common';
export function publicationStatus(
  value: unknown,
): 'draft' | 'published' | undefined {
  if (value === undefined) return undefined;
  if (value !== 'draft' && value !== 'published')
    throw new BadRequestException('状态必须为草稿或已发布');
  return value;
}
