import { editorialGuessName } from './guess-identity';
import { createHash } from 'node:crypto';
import { Injectable } from '@nestjs/common';
import { MysqlService } from '../mysql/mysql.service';
import type { GuessPerson } from './guess-catalogue';

export type GuessDifficulty = 'easy' | 'hard';
export type GuessRating = 'easy' | 'right' | 'hard';
export type BankRow = {
  person_id: string;
  difficulty: GuessDifficulty;
  revision: number;
};
export type BankSeed = { person_id: string; difficulty: GuessDifficulty };
export type BankFeedback = {
  person_id: string;
  revision: number;
  actor_hash: string;
  game_hash: string;
  rating: GuessRating;
  turns: number;
  hints: number;
};
export type BankRatingResult = BankRow & {
  rating: GuessRating;
  moved: boolean;
};

// Editorial familiarity anchors are a game setting, never historical evidence.
// Other published, source-backed people begin in the broader hard pool. Feedback
// can move either group; bootstrap must never overwrite a player-adjusted level.
export const legacyGuessTiers: Record<string, number> = Object.fromEntries(
  [
    [
      '李白 杜甫 李世民 曹操 刘邦 项羽 秦始皇 嬴政 武则天 孔子 孟子 诸葛亮 关羽 刘备 孙权 岳飞 朱元璋 李清照 苏轼 白居易',
      1,
    ],
    ['朱温 朱全忠 朱晃 李存勖 柴荣 石勒 苻坚 李克用 刘裕 王安石 赵匡胤', 2],
    ['王僧辩 刘琨 敬翔 李振 葛从周 王彦章', 3],
    ['孙泰 刘交', 4],
  ].flatMap(([names, tier]) =>
    String(names)
      .split(' ')
      .map((name) => [name, Number(tier)]),
  ),
);

const familiarNames = new Set(
  (
    '祖冲之 张良 韩信 萧何 陈平 樊哙 英布 彭越 周勃 周亚夫 窦婴 卫青 霍去病 霍光 张骞 苏武 李广 李陵 刘彻 刘秀 刘恒 刘启 吕雉 王莽 董仲舒 司马迁 班固 班超 班昭 蔡伦 张衡 华佗 张仲景 ' +
    '张飞 赵云 黄忠 马超 张辽 吕布 董卓 袁绍 袁术 陈宫 许褚 典韦 张郃 徐晃 徐庶 荀彧 荀攸 郭嘉 贾诩 曹仁 曹洪 夏侯惇 夏侯渊 于禁 庞统 法正 姜维 邓艾 钟会 鲁肃 吕蒙 陆逊 周瑜 黄盖 孙坚 孙策 太史慈 甘宁 陆抗 曹丕 曹植 蔡琰 王允 司马懿 司马师 司马昭 司马炎 ' +
    '谢安 谢玄 王羲之 王献之 陶渊明 桓温 桓玄 王敦 王导 祖逖 石虎 冉闵 慕容垂 慕容恪 王猛 刘渊 刘聪 贾南风 刘义隆 萧道成 萧衍 陈霸先 高欢 高洋 高长恭 宇文泰 宇文邕 拓跋珪 拓跋焘 拓跋宏 郦道元 ' +
    '杨坚 杨广 杨素 杨玄感 贺若弼 韩擒虎 韦孝宽 窦建德 王世充 李渊 李建成 李元吉 李靖 李勣 李绩 尉迟恭 秦琼 程咬金 魏征 房玄龄 杜如晦 褚遂良 长孙无忌 狄仁杰 姚崇 宋璟 张九龄 高力士 杨玉环 安禄山 史思明 郭子仪 李光弼 李隆基 李亨 李豫 李适 李纯 李忱 李晔 黄巢 ' +
    '王维 孟浩然 岑参 高适 韩愈 柳宗元 刘禹锡 元稹 贾岛 王勃 骆宾王 杨炯 卢照邻 陈子昂 李贺 杜牧 李商隐 温庭筠 韩偓 陆龟蒙 皮日休 张承业 冯道 钱镠 王建 杨行密 高季兴 孟知祥 李煜 李昪 刘知远 郭威 石敬瑭 耶律阿保机 耶律德光 耶律楚材 赵普 寇准 包拯 范仲淹 司马光 欧阳修 辛弃疾 文天祥 陆游'
  ).split(' '),
);

export function initialGuessDifficulty(person: GuessPerson): GuessDifficulty {
  const name = editorialGuessName(person.name);
  const tier = legacyGuessTiers[name];
  return (tier && tier <= 2) || familiarNames.has(name) ? 'easy' : 'hard';
}
export function guessCatalogueRevision(people: GuessPerson[]) {
  return createHash('sha256').update(JSON.stringify(people)).digest('hex');
}

@Injectable()
export class GuessBankService {
  constructor(private readonly db: MysqlService) {}

  async prepare(
    people: GuessPerson[],
    signal: AbortSignal,
  ): Promise<GuessPerson[]> {
    const bank = new Map<string, BankRow>();
    const read = async (ids: string[]) => {
      const rows = (await this.db.rows(
        `SELECT person_id,difficulty,revision FROM guess_bank WHERE person_id IN (${ids.map(() => '?').join(',')})`,
        ids,
        signal,
      )) as BankRow[];
      for (const row of rows) bank.set(row.person_id, row);
    };
    for (let offset = 0; offset < people.length; offset += 1000) {
      const page = people.slice(offset, offset + 1000);
      await read(page.map((p) => p.id));
      const missing = page.filter((p) => !bank.has(p.id));
      if (missing.length) {
        await this.db.seedGuessBank(
          missing.map((p) => ({
            person_id: p.id,
            difficulty: initialGuessDifficulty(p),
          })),
          signal,
        );
        // Another instance may have prepared or reclassified a row meanwhile.
        await read(missing.map((p) => p.id));
      }
    }
    return people.map((p) => {
      const row = bank.get(p.id);
      if (!row) throw new Error('Game bank preparation incomplete');
      return {
        ...p,
        game_difficulty: row.difficulty,
        game_revision: row.revision,
      };
    });
  }

  rate(feedback: BankFeedback, signal: AbortSignal) {
    return this.db.rateGuessPerson(feedback, signal);
  }
}
