import type { ReferenceLink } from '@histree/shared-types';

export const formatDisplayYear = (year?: number | null) => {
  if (year === undefined || year === null) return '时间待补充';
  return year < 0 ? `公元前${Math.abs(year)}年` : `${year}年`;
};

export const formatDisplayRange = (start?: number | null, end?: number | null) => {
  if (start === undefined || start === null) return '时间待补充';
  if (end === undefined || end === null || end === start) {
    return formatDisplayYear(start);
  }
  return `${formatDisplayYear(start)} - ${formatDisplayYear(end)}`;
};

export const referenceTypeLabel = (type: ReferenceLink['reference_type']) => {
  switch (type) {
    case 'encyclopedia':
      return '百科';
    case 'primary':
      return '原始史料';
    case 'reference':
      return '工具书';
    case 'scholarship':
      return '研究论著';
    default:
      return '数字资源';
  }
};

export const primaryReference = (references?: ReferenceLink[]) =>
  references?.find((reference) => reference.reference_type === 'encyclopedia') ?? references?.[0];
