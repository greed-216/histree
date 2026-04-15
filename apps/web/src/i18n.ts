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
      loginAdmin: '管理员登录',
      logout: '退出登录',
      loginRequired: '请输入管理员账号登录',
      adminStatus: '已登录 (Admin)',
      Explore: '探索',
      People: '人物',
      Events: '事件',
      'People Directory': '历史人物大全',
      'Events Directory': '历史事件大全',
      'Recommended Exploration': '推荐探索',
      'Random Explore': '随机漫游',
      'Interactive Graph': '交互式图谱',
      'Person Details': '人物详情',
      'Event Details': '事件详情',
      'Unknown Year': '年份未知',
      'No description available.': '暂无描述信息。',
      'Description': '详细描述',
      'Related Nodes': '相关节点',
      'more nodes in graph': '个更多节点在图中',
      'Node not found': '未找到该节点数据',
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
      loginAdmin: 'Admin Login',
      logout: 'Logout',
      loginRequired: 'Please login with your admin account',
      adminStatus: 'Logged in (Admin)',
      Explore: 'Explore',
      People: 'People',
      Events: 'Events',
      'People Directory': 'People Directory',
      'Events Directory': 'Events Directory',
      'Recommended Exploration': 'Recommended Exploration',
      'Random Explore': 'Random Explore',
      'Interactive Graph': 'Interactive Graph',
      'Person Details': 'Person Details',
      'Event Details': 'Event Details',
      'Unknown Year': 'Unknown Year',
      'No description available.': 'No description available.',
      'Description': 'Description',
      'Related Nodes': 'Related Nodes',
      'more nodes in graph': 'more nodes in graph',
      'Node not found': 'Node not found',
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
