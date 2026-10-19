// Era membership uses published labels, not inferred lifespans or model memory.
// Broad labels expand to their components; partial overlap stays with the agent.
const eras: Record<string, string[]> = {
  春秋: ['春秋'],
  战国: ['战国'],
  春秋战国: ['春秋', '战国'],
  秦: ['秦'],
  西汉: ['西汉'],
  东汉: ['东汉'],
  汉: ['西汉', '东汉'],
  两汉: ['西汉', '东汉'],
  秦汉: ['秦', '西汉', '东汉'],
  三国: ['三国'],
  西晋: ['西晋'],
  东晋: ['东晋'],
  晋: ['西晋', '东晋'],
  两晋: ['西晋', '东晋'],
  魏晋: ['三国', '西晋', '东晋'],
  南北朝: ['南北朝'],
  魏晋南北朝: ['三国', '西晋', '东晋', '南北朝'],
  隋: ['隋'],
  唐: ['唐'],
  隋唐: ['隋', '唐'],
  五代: ['五代十国'],
  五代十国: ['五代十国'],
  宋: ['北宋', '南宋'],
  北宋: ['北宋'],
  南宋: ['南宋'],
  元: ['元'],
  明: ['明'],
  清: ['清'],
  明清: ['明', '清'],
};
function components(label: string): string[] | undefined {
  const key = label.replace(/(?:时期|时代|年代|朝代|朝)$/, '');
  return Object.hasOwn(eras, key) ? eras[key] : undefined;
}

export function judgeEraQuestion(
  question: string,
  publishedEra: string | null | undefined,
): 'yes' | 'no' | undefined {
  const text = question.normalize('NFKC').replace(/[\s，,。.!！?？]/g, '');
  // Match only a whole, single era proposition. Names, offices, birth/death,
  // negation, multiple questions and instructions must use the normal judge.
  const match = text.match(
    /^你(?:(?:是|属于)(?:(?:主要)?(?:生活|活跃|活动)在)?|(?:主要)?(?:生活|活跃|活动)在)(.+?)(?:的)?(?:人物|人)?(?:吗|么|嘛)$/,
  );
  if (!match || !publishedEra) return undefined;
  const requested = components(match[1]);
  const known = components(publishedEra.trim());
  if (!requested || !known) return undefined;
  if (known.every((era) => requested.includes(era))) return 'yes';
  if (known.every((era) => !requested.includes(era))) return 'no';
  return undefined;
}
