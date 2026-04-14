import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  zh: {
    translation: {
      title: 'Histree (历史之树)',
      subtitle: '一个基于图谱驱动的中国历史探索平台。',
      demoTitle: 'Histree MVP 演示',
      person: '人物',
      event: '事件',
      failedToFetch: '获取图谱数据失败，使用降级模拟数据。',
      loading: '加载中...',
      langToggle: 'English',
      // Mock data translations
      'Liu Bei': '刘备',
      'Zhuge Liang': '诸葛亮',
      'Battle of Red Cliffs': '赤壁之战',
      'Founder of Shu Han': '蜀汉开国皇帝',
      'Chancellor of Shu Han': '蜀汉丞相',
      'Decisive battle at the end of the Han dynasty': '汉末决定性战役',
      'Three Kingdoms': '三国',
      'Eastern Han': '东汉',
      'ruler': '主公',
      'participant': '参与者',
      'Liu Bei recruited Zhuge Liang': '刘备三顾茅庐请诸葛亮出山',
      'Zhuge Liang planned the alliance': '诸葛亮促成孙刘联盟',
      'Liu Bei led allied forces': '刘备率领联军'
    }
  },
  en: {
    translation: {
      title: 'Histree',
      subtitle: 'A graph-driven platform for exploring Chinese history.',
      demoTitle: 'Histree MVP Demo',
      person: 'Person',
      event: 'Event',
      failedToFetch: 'Failed to fetch graph data, using mock data fallback.',
      loading: 'Loading...',
      langToggle: '中文',
      // Mock data remains as is
      'Liu Bei': 'Liu Bei',
      'Zhuge Liang': 'Zhuge Liang',
      'Battle of Red Cliffs': 'Battle of Red Cliffs',
      'Founder of Shu Han': 'Founder of Shu Han',
      'Chancellor of Shu Han': 'Chancellor of Shu Han',
      'Decisive battle at the end of the Han dynasty': 'Decisive battle at the end of the Han dynasty',
      'Three Kingdoms': 'Three Kingdoms',
      'Eastern Han': 'Eastern Han',
      'ruler': 'Ruler',
      'participant': 'Participant',
      'Liu Bei recruited Zhuge Liang': 'Liu Bei recruited Zhuge Liang',
      'Zhuge Liang planned the alliance': 'Zhuge Liang planned the alliance',
      'Liu Bei led allied forces': 'Liu Bei led allied forces'
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'zh', // default language
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
