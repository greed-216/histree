# 首页历史画卷 V2

当前使用内置imagegen生成的一张连续母图 `apps/web/public/timeline-scroll/scroll-continuous-v2.png`，2172×724。SVG只展示其中 x=0、y=194、宽2172、高368的画卷区域，约6:1；网页完整预览6516×1104是展示尺寸，放大不会增加原图细节。母图像素未作修改。

覆盖前770年至1912年，无0年，共2681年。整幅画面由同一条连续河道与山势贯穿；不再将三幅独立生图并列。`history-scroll.json`保存裁切、尺寸、哈希及分期，底图使用与事件相同的时间坐标。

## V2 提示词规格

Use case: compositing. Inputs: 原三幅图作为风格和时代意象参考。Redraw all three together as ONE organically continuous landscape; no montage, no vertical seams, no repeated vignettes at one-third/two-thirds. Continuous river, mountains, roads, consistent perspective, texture, lighting and palette. Preserve blue-green gongbi Chinese handscroll style and ivory silk texture. No text, dates, labels, watermarks or map boundaries.

生图请求为3:1画布中间包含9:1浅长卷，两侧上下为空白纸面。实际工具返回2172×724，画卷区域更高，因此网页裁出约6:1区域以保留山势与河道，而未把画面强行拉伸成9:1。

按宽度比例配置意象：春秋战国20.5%，秦汉16.4%，魏晋南北朝13.5%，隋唐12.2%，五代2.0%，宋11.9%，元3.3%，明10.3%，清10.0%。时代场景逐渐过渡，不设分块边界。最右侧少量蒸汽船、电报线和铁路表现清末变化。

## 交互与验证

首页默认607—1207年、选中907年；浏览、拖动、缩放不改变选年，明确点击才更新选择。数据范围外的直达年份也定位到对应画卷。未录入年份显示暂无记录。年份、史事和数量由页面绘制，不从画面推断事实。

画面是AI文化意象，画内时代比例近似，不代表疆域、准确建筑年代或具体事件。按中原主线粗分时期；元从1279年、清从1644年计算。后续可替换更高清母图，保持年轴及裁切定义即可。

`pnpm test:timeline`验证时间比例、无0年换算、单幅连续资产、裁切范围、图片比例与原件哈希。旧三幅原件保留为V1参考，当前页面不再加载。

---

## V1 生成档案

# 首页历史画卷

## 展示与尺寸

覆盖公元前770年至1912年；没有公元0年，总时间跨度2681年。三张原始PNG在网页中连续展示为约9:1长卷，逻辑画布6514×725。它们并不是一张已经拼接的PNG。

原件保存在 `apps/web/public/timeline-scroll/`：

| 文件 | 原始分辨率 | 时间范围 |
| --- | --- | --- |
| scroll-01.png | 2172×724 | 前770年—124年 |
| scroll-02.png | 2170×725 | 124—1018年 |
| scroll-03.png | 2172×724 | 1018—1912年 |

`apps/web/src/data/history-scroll.json` 保存年界、尺寸、哈希和分期。页面坐标与底图使用同一套排除0年的时间换算；展示宽度按年数计算。缩放时保持图片比例并裁切上下区域。首页仅加载与当前时间窗口相交的图片。

默认首页显示607—1207年，选中已有数据的907年；“画卷全景”浏览全部年代，“看已录史事”回到当前数据范围。拖动、分期按钮和缩放只改变浏览窗口，点击年份才改变选择。年度事件和年份文字由网页绘制，底图不包含数据。

## 分期占比

春秋战国20.5%，秦汉16.4%，魏晋南北朝13.5%，隋唐12.2%，五代2.0%，宋11.9%，元3.3%，明10.3%，清10.0%。按中原主线作大体划分，不能用来说明同时并存政权的疆界；元从1279年、清从1644年计算。

## 生图方式与提示词规格

使用内置 imagegen 生成三张新图，未使用CLI、史图馆图片或其他参考图；原件未做像素编辑。下面保留生成时使用的构图和年代规格，后续可以据此重生成。

共同提示词：

> Use case: historical-scene. Create one full-bleed 3:1 horizontal landscape panel of a continuous Chinese historical handscroll. Refined Chinese blue-green landscape painting, gongbi-style architecture, tiny ordinary people, jade and pine green, pale mineral blue, sandstone and ivory silk-paper. Elevated panoramic view with rivers, fields and towns. Pale mist at both edges and a river crossing both edges roughly 65% down. Keep the upper 25% calm. No text, dates, labels, watermarks or map boundaries. Artistic cultural backdrop, not an authoritative historical map or reconstruction. No giant portraits, major war, fire, gore or fantasy structures. Place scenes in chronological order and allocate their widths by elapsed time rather than equal dynasty sections.

第一幅：前770年—124年。左至右：0—33%春秋（青铜工坊、学者、战车、夯土城镇）；33—61.5%战国；61.5—63.2%秦的窄小过渡；63.2—88.7%西汉；88.7—90.3%过渡；90.3—100%东汉早期。

第二幅：124—1018年。左至右：0—10.7%东汉后期；10.7—51.1%三国、两晋、南北朝；51.1—87.6%隋唐；87.6—93.5%五代；93.5—100%宋初。

第三幅：1018—1912年。左至右：0—29.2%宋；29.2—39.2%元；39.2—70%明；70—100%清。最右3%用少量蒸汽船、电报线、铁路表现清末变化，不使用暴力场面或旗帜。

## 使用边界

画面为AI生成的历史文化意象，画内建筑和服饰不保证精确年代，也不代表疆域或具体事件。三幅边缘仍有可见风格接缝，画内场景比例近似；网页年轴、分期和底图块宽度按时间计算。未录入史事的年份显示暂无记录，不以画面代替史料。

验证：`pnpm test:timeline` 检查分期比例、无0年的坐标、图片相接、图片比例与原件哈希。浏览器另行验证拖动、缩放、明确选年和预览布局。
