# 黑漆嵌薄螺钿山水人物盘：实物、工艺、光学与渲染依据

调研日期：2026-11-02。目标是为“转动的黑漆盘特写，细贝片随角度出现虹彩”建立可追溯参照。本报告的 **[实测/观察]** 均指来源作者对指定样品的测量或实物观察，本项目没有接触藏品；**[文献]** 指馆方编目、历史/工艺文献或标准；**[模型]** 指论文采用的假设；**[推断/建议]** 指供本项目验证的解释或实现选择。

推荐以**上海博物馆同名清代圆盘控制器形、构图和色彩分区，以元明器及修复研究控制细部工艺，以珍珠层多层干涉模型控制角度响应**。同名器不是元明器，具体古盘也没有已公开的完整光学参数；不能把现代贝壳数据写成古盘检测结果。[上博同名器](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/P00004947)、[元代盘截面研究](https://collections.asianart.org/wp-content/uploads/sites/5/2024/05/Williams_2008_Conservation_of_Asian_Lacquer.pdf#page=34)、[珍珠层角分辨研究](https://doi.org/10.1073/pnas.2023623118)

交付统计：保留55张图片/图版（含12张长边≥3000 px）、17份PDF文件（含同一论文不同版本、工艺单页与图录）及作者代码/示例谱。已检查全部图片解码、PDF读取和正文/索引本地链接。下文覆盖四项问题；图片在 [`img/`](img/)，逐图的来源、实有像素、视角、处理方式及授权见 [`img/README.md`](img/README.md) 和 [`img/manifest.json`](img/manifest.json)；PDF 与代码包见 [`papers/README.md`](papers/README.md)。未取得图像、未知尺寸和未经测量的参数均明确保留为缺口。

## 1. 实物：先区分同名清器与元明比较物

下表年代、材质、尺寸均为 **[文献：馆方编目]**，不是本次测量；尺寸单位 cm。正面照片常有透视，不能因近正面拍摄便视作正投影；也没有把普通斜视照标作经过控制的“斜光实验”。

| 对象与藏处 | 年代、尺寸、身份 | 已取得的图像与用途 | 出处 |
|---|---|---|---|
| **漆螺钿山水人物图圆盘，上海博物馆** | **清中期，18世纪；径12.6、高1.2**。纻胎、银扣；四件成套，本页为撑伞过桥图，盘底诗句“不辞风雨过溪来” | [`shanghai_landscape_round.jpg`](img/shanghai_landscape_round.jpg)，590×590，仅馆方公开网页图；主要器形/画面参照，不能称高清原片 | [官方记录](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/P00004947) |
| **广寒宫螺钿漆器残片，首都博物馆体系；北京大运河博物馆发布** | 元1271–1368；当前发布记录残片长20、宽12.5；北京后英房元大都遗址出土，馆方称用细小鲍贝薄片 | [`guanghan_fragment_canal.jpg`](img/guanghan_fragment_canal.jpg)，1440×1080，展陈斜视；楼阁、云气、细碎贝片的元代比较物 | [北京大运河博物馆](https://www.canalmuseum.org.cn/detail34/257.html)、[扬州展览注明首都博物馆藏](https://www.grandcanalmuseum.cn/yunboxinwen/365.html) |
| 黑漆螺钿人物图圆盒，上海博物馆 | 元；径11、高3.7 | [`shanghai_yuan_box.jpg`](img/shanghai_yuan_box.jpg)，590×590，斜视；人物、松石、楼阁的元代比较物，**是盒而非盘** | [官方记录](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/P00004945) |
| 黑漆嵌螺钿人物盘，故宫博物院，新00097981 | 明；口径11.4、高1；沈从文捐献 | [`palace_ming_figures.jpg`](img/palace_ming_figures.jpg)，1024×996；人物及大块贝片内阴刻，器形是方盘 | [官方记录](https://www.dpm.org.cn/collection/lacquerware/233185.html) |
| 黑漆嵌螺钿人物纹圆盘，青岛市博物馆 | 清康熙；口径13；木胎，底嵌“千里” | `qingdao_kangxi_01–04.jpg`：正面、**侧面**、盘心**局部**、**背面**四张，各1280×850；圆盘转动时的浅腹轮廓和边饰很有用 | [官方记录及四图](https://qingdaomuseum.cn/collection/detail/242) |
| 元黑漆嵌螺钿梅鹊纹八方盘，纽约大都会艺术博物馆，2011.120.2 / object40256 | 元14世纪；径29.5；官网高度记0.3，照录，未独立核验 | `met_40256_01.jpg` 3001×4000，整体；`_02.jpg` 1000×331，低角度侧视。花鸟主题作为薄贝/黑漆表面对照 | [当前馆藏记录](https://www.metmuseum.org/art/collection/search/40256) |
| 明黑漆嵌螺钿婴戏图盘，Met，2005.265 / object72809 | 明16世纪；高1.9、宽/深14.3 | [`met_72809_01.jpg`](img/met_72809_01.jpg)，3314×4000，近正面；人物轮廓、竹梅兰菊和阴刻 | [官方记录](https://www.metmuseum.org/art/collection/search/72809) |
| 明晚期黑漆嵌螺钿游园赏乐图菱形盘，Met，2015.500.1.58 / object40260 | 16世纪晚期–17世纪；高2.9、宽21.6、长28.6；螺钿及金、银箔 | `met_40260_01–02.jpg`，均4000×3000，前后斜视；楼阁人物、金属与贝片分区 | [官方记录](https://www.metmuseum.org/art/collection/search/40260) |
| 黑漆嵌螺钿“桃源洞”图方盒，Met，2006.181a,b / object73203 | 14世纪晚期–15世纪中叶；高7.6、宽22.9、长34.3 | `met_73203_HD_01–03.jpg`：斜视、正面、侧面，长边3794/3840/3875 px；极细人物、栏杆和题字，**是盒** | [当前馆藏记录](https://www.metmuseum.org/art/collection/search/73203) |
| 黑漆嵌螺钿人物故事图葵口盘，Met，2015.500.1.13 / object40261 | 明16世纪；径27；《西厢记》是旧图片题名的推测，现行馆方只说可能来自流行小说插图 | `extra_met_40261_DP704250_front.jpg`、`...DP704251_back.jpg`，均4000×3002，正/背；圆形葵口、楼阁人物与密集边饰，接近目标 | [官方记录](https://www.metmuseum.org/art/collection/search/40261) |
| 黑漆嵌螺钿人物故事图九方盘，Met，2015.500.1.18 / object40255 | 元14世纪；高5.4、径48.9、足径43.2 | `extra_met_40255_DP704081_front.jpg`、`...DP704082_back.jpg`，均4000×3002，正/背；大盘人物场景的比较物 | [官方记录](https://www.metmuseum.org/art/collection/search/40255) |
| 龍涛螺鈿稜花盆，东京国立博物馆，TH-9 | 元14世纪；径33、高2.3 | [`extra_tnm_TH9_front.jpg`](img/extra_tnm_TH9_front.jpg)，3567×4456；稍斜整体。龙涛题材，供水纹、贝丝和黑地密度参照 | [官方目录](https://emuseum.nich.go.jp/detail?content_base_id=100890&content_part_id=0&content_pict_id=0&langId=ja&webView=)、[IIIF](https://emuseum.nich.go.jp/iiifapi/100890000/manifest.json) |
| 黑漆八宝文螺钿盆，爱知县美术馆，木村定三收藏M1386 | 元14世纪；径20.8、高2.5 | `extra_aichi_M1386_*`：正背侧与局部；**显微×20螺钿、×63金属縒线，带1.0 mm标尺**。普通图为灰阶印刷图，不能作色彩样本 | [目录p.70–71](https://apmoa.museum/assets/pdf/bulletin/2014/apmoabulletin2014kimurap39-93.pdf#page=32)、[科学分析p.100](https://apmoa.museum/assets/pdf/bulletin/2014/apmoabulletin2014kimurap98-117.pdf#page=3) |
| 黑漆楼阁人物图螺钿轴盆，爱知县美术馆，M1028 | 明16–17世纪；宽13.7、深18.7、高2.4 | `extra_aichi_M1028_front.jpeg` 和 `...figure_detail.jpeg`，167×376及272×196；确有楼阁骑马人物局部，但仅低清灰阶 | [目录p.76](https://apmoa.museum/assets/pdf/bulletin/2014/apmoabulletin2014kimurap39-93.pdf#page=38) |
| 黑漆楼阁人物图螺钿四方盆，爱知县美术馆，M1385 | 明16–17世纪；宽/深19.8、高2.3 | `extra_aichi_M1385_oblique.jpeg`，374×222，灰阶斜视整体；仅供构图和器形 | [目录p.75](https://apmoa.museum/assets/pdf/bulletin/2014/apmoabulletin2014kimurap39-93.pdf#page=37) |
| 长方螺钿盘，旧金山亚洲艺术博物馆，B79M7 | 中国元14世纪；40.2×11.3×2.0 | `aam_b79m7_*`：整体、局部、X光、原始/修复层的可见光–UV显微截面；是最直接的**器物层次**证据 | [修复研究p.62–69](https://collections.asianart.org/wp-content/uploads/sites/5/2024/05/Williams_2008_Conservation_of_Asian_Lacquer.pdf#page=32) |

**编目差异与取得限制。** Met“桃源洞”2006年展览旧页记长33 cm、14–15世纪初，当前对象页记34.3 cm、14世纪晚期–15世纪中叶；本报告采用当前对象页。广寒宫残片的20×12.5是当前展示记录，不能与文献中的约37 cm原盘/残件尺度混作同一量。未取得同名上博圆盘的更高清、多角度或显微原片，也未取得这只古盘的受控角分辨反射数据。[Met旧展页](https://www.metmuseum.org/exhibitions/listings/2006/mother-of-pearl/photo-gallery)、[Met当前页](https://www.metmuseum.org/art/collection/search/73203)、[北京大运河记录](https://www.canalmuseum.org.cn/detail34/257.html)、[傅举有p.136](https://img.dpm.org.cn/Uploads/File/pdf/db/b9/89/dbb989254f4ab709d63d9f7cbdea5665.pdf)

另有明确的**明代圆盘**拍卖记录：Christie’s lot5182121，15–16世纪、径19 cm，柳下坐读人物；及lot6194566元末明初方盘，17.8 cm。拍卖归年是拍卖行意见，非本项目鉴定，不能据拍卖记录声称现藏某博物馆；本次原图下载超时，未把它们列成已取得照片。[明圆盘原拍品页](https://www.christies.com/en/lot/lot-5182121)、[元明方盘原拍品页](https://www.christies.com.cn/zh-cn/lot/lot-6194566)

**授权记录原则。** Met开放图像按CC0及API的`isPublicDomain`核对，Commons仅作为馆方图的原尺寸镜像；Commons旧编年不覆盖现行馆方编年。东京图、上博/故宫/青岛图、爱知图录和AAM修复书没有取得开放再利用许可，均逐张标“权利保留/未见开放许可，仅作研究参照”，并非已获机构另行授权。[Met开放政策](https://www.metmuseum.org/about-the-met/policies-and-documents/open-access)、[东京使用条款](https://emuseum.nich.go.jp/about)、[AAM版权页](https://collections.asianart.org/wp-content/uploads/sites/5/2024/05/Williams_2008_Conservation_of_Asian_Lacquer.pdf#page=3)

## 2. 工艺：材料、厚度、切拼与漆层

### 2.1 贝种及“薄”的数值口径

| 证据性质与范围 | 信息 | 对本项目的约束及出处 |
|---|---|---|
| [文献] 中国工艺综述 | 薄螺钿主要用**珍珠贝、夜光螺、鲍鱼贝**；厚螺钿多用河蚌。俗名未必一一对应某个拉丁种 | 不能只凭颜色给目标盘鉴种；广寒宫的“鲍贝”是馆方记载。[傅举有p.136](https://img.dpm.org.cn/Uploads/File/pdf/db/b9/89/dbb989254f4ab709d63d9f7cbdea5665.pdf)、[广寒宫馆方记录](https://www.canalmuseum.org.cn/detail34/257.html) |
| [文献] 同一综述的历史分类 | 厚片0.5–2 mm；薄片<0.5 mm，常**0.1–0.3 mm** | 一般性记载，非元明目标器逐片实测。[傅举有p.136](https://img.dpm.org.cn/Uploads/File/pdf/db/b9/89/dbb989254f4ab709d63d9f7cbdea5665.pdf) |
| [文献] 乔十光现代工序，傅举有转述 | 先去角质/石灰层，取珍珠层，手工磨到**0.3–0.4 mm**后切嵌 | 与上行数值并列保留，不能人为合并成统一历史规范。[傅举有p.143](https://img.dpm.org.cn/Uploads/File/pdf/ce/4c/65/ce4c6508e0747a56ae52fd39b9bde55e.pdf) |
| [文献/现代标准] DB32/T4532—2023《点螺漆器技术规范》§5.1 | 珍珠贝、鲍鱼贝/石决明、夜光螺，亦列河蚌壳唇边“金耳朵”；片厚**3–10丝，明定1丝=0.01 mm，即0.03–0.10 mm** | 起草单位含扬州漆器厂；是现代技术规范，不能称古代普遍厚度。[官方记录](https://std.samr.gov.cn/db/search/stdDBDetailed?id=053A0D902C25C568E06397BE0A0A3538)、[官方全文§5.1](https://dbba.sacinfo.org.cn/portal/download/7d669991c4bc219dca28bdede3f45b833ae99fd8a1fb4c07b66d1fc88b68b6ba) |
| [文献/日本对照] usugai/aogai | <0.1 mm；研磨或煮后剥层；厚片约1 mm | 日本分类与中国综述阈值不同，不可混用。[日本工艺会Gallery Japan](https://www.galleryjapan.com/locale/en_US/technique/urushiwork/30305/) |

**[文献] 平面尺寸与最细线。** 傅举有对后英房元盘的描述是“长宽毫米级”的细小螺片逐片点植；上博同名盘的边饰是贝片裁成极细弧丝拼花，人物衣纹、树石纹理另用阴线浅刻。因此应区分**实体贝丝的宽度**和**贝面阴刻沟宽度**。本次没有查到元明目标器这两者的可靠最小微米数，也没有片长分布统计；“细如发丝”不换算成测量值。[傅举有p.136](https://img.dpm.org.cn/Uploads/File/pdf/db/b9/89/dbb989254f4ab709d63d9f7cbdea5665.pdf)、[上博目标盘](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/P00004947)

### 2.2 怎么切、怎么拼、是否先刻纹

**[文献/现代流程]** 标准列切割工具、镊子、针、黄杨木板和多形开纹刀；先取珍珠层、粗磨并水磨，依壳色和图稿裁成点/线/面，针尖逐片点植，再开纹、补细部，罩漆干后逐级磨抛。标准给初磨260–1500目、罩漆后260–5000目；这些是现代工序数值。人物、树冠和栏杆不应默认各由一整片大壳剪成，许多轮廓是细碎点条拼接，一片内又可阴刻。[DB32/T4532—2023 §4–5.2](https://dbba.sacinfo.org.cn/portal/download/7d669991c4bc219dca28bdede3f45b833ae99fd8a1fb4c07b66d1fc88b68b6ba)、[傅举有p.136](https://img.dpm.org.cn/Uploads/File/pdf/db/b9/89/dbb989254f4ab709d63d9f7cbdea5665.pdf)

**[实物观察→作者工序推定]** 元代B79M7盘的刻线未贯穿贝片，圆头工具留下连续弧痕，沟内多有漆。修复作者据薄片需要稳定支撑，推定粘贝之后刻、最终涂漆之前刻。这是特定实物的证据链，不是所有时代的统一流程。[Williams 2008，印刷p.66–67](https://collections.asianart.org/wp-content/uploads/sites/5/2024/05/Williams_2008_Conservation_of_Asian_Lacquer.pdf#page=34)

### 2.3 漆地、罩漆磨显与剥显

**[实测/观察] B79M7原层**：木胎、平纹布、含灰/黏土的底层，黑色漆层湿粘贝片，再髹漆填平，干后磨至贝片齐平；黑漆上至少一层无颜料透明漆。底层胶黏剂的具体成分没有分析确认。下图为原始层的可见光/UV截面；原PDF倍率写作占位符`00x`，无可用标尺，不能从这张图换算漆厚或贝厚。[Williams p.62–69、图4.32](https://collections.asianart.org/wp-content/uploads/sites/5/2024/05/Williams_2008_Conservation_of_Asian_Lacquer.pdf#page=35)

![B79M7原始漆层截面，图4.32，非目标圆盘；版权AAM](img/aam_b79m7_original_cross_section_fig4_32.jpeg)

**[实物观察→作者推定] 不能把“罩漆再磨显”推广到每件古器。** 爱知M1386螺钿未见研磨痕，有局部残漆与微小高度差，作者推定用刃/篦剥去贝片上的漆，即剥显；相邻金属縒线却有磨痕，作者推定经磨显。同一器上也可能有不同处理机制。此处没有测得台阶高度或微表面粗糙度。[爱知科学分析p.100–101](https://apmoa.museum/assets/pdf/bulletin/2014/apmoabulletin2014kimurap98-117.pdf#page=3)

**[实测/修复观察]** B79M7松片背面有空气时发白，重新贴牢暗底后更绿/粉；粘接空隙、底色、后修罩漆会改变外观。应避免把藏品上全部色差都归于贝片厚度。[Williams p.68](https://collections.asianart.org/wp-content/uploads/sites/5/2024/05/Williams_2008_Conservation_of_Asian_Lacquer.pdf#page=35)

### 2.4 衬色、背衬金银箔与分层

- **[文献] 中国确有衬色螺钿**：在较透明的贝下施色；故宫公开论文单页有明确记载，但本次未获得篇首页，作者/完整篇名未核实，应降低书目完整性评价。[故宫公开原页p.7](https://img.dpm.org.cn/Uploads/pdf/1546/T00007_00.pdf)
- **[文献] 金银与贝片并嵌**：上博目标盘明确有裁成丝条、菱形的金片，Met40260媒材明确有金银箔；这只能证明同器并用，**不证明金银箔一定在贝片背后**。[上博](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/P00004947)、[Met](https://www.metmuseum.org/art/collection/search/40260)
- **[文献/具体对照] 背贴金箔确有实物记载**：浦添市美术馆18–19世纪琉球黑漆牡丹唐草螺钿卓、黑漆楼阁人物螺钿八角食笼的部分花贝背面贴金箔。日本工艺会亦列薄贝背施金、银等的`urazaishiki`。这证明可行机制，不能据此断定元明目标盘均有背箔。[浦添馆方](https://www.city.urasoe.lg.jp/kokyoshisetsu/art/609e776a3d59ae2434bfe14b/)、[日本工艺会](https://www.galleryjapan.com/locale/en_US/technique/urushiwork/30305/)
- **[证据边界]** 没有查得目标盘以多层人工叠贝构成画面的证据。要分开三个尺度：器物的布/灰/漆层、贝背的胶/色/箔、贝内部天然文石–有机层；后者即使贝片只有几十微米，仍可能含许多纳米周期。[B79M7截面](https://collections.asianart.org/wp-content/uploads/sites/5/2024/05/Williams_2008_Conservation_of_Asian_Lacquer.pdf#page=35)、[珍珠层结构研究](https://doi.org/10.1073/pnas.2023623118)


## 3. 光学：结构参数、角谱与磨薄效应

### 3.1 可直接引用的结构数值

| 样品与出处 | 数值与测量性质 | 位置、适用边界 |
|---|---|---|
| 新西兰虹鲍 **Haliotis iris**，Song, Soh & Bai (2003) | **实测：**文石层 **450–550 nm**；有机基质层 **21–31 nm**。样品去除角质／棱柱层，清洗、风干，SEM/TEM观察。 | §2 Experimental method；§3.1，Fig.1a,b。来源原文 [DOI](https://doi.org/10.1016/S0142-9612(03)00215-1)；出版社有完整相关段落，全文PDF未获取。[出版社](https://www.sciencedirect.com/science/article/pii/S0142961203002151) |
| 红鲍 **H. rufescens**，Salman et al. (2021) | **实测：**一处断面文石层厚度近似高斯分布，均值约 **420 nm**、标准差约 **50 nm**。**文献概述：**平面晶板直径约 **5–10 µm**，并非裁切后嵌片的尺寸。 | 下载预印本PDF pp.20–21 / SI §4 Fig.S4；正文p.2的5–10µm为转引范围。[论文](https://doi.org/10.1073/pnas.2023623118)；[下载预印本，包含SI](papers/hit_2021_preprint.pdf) |
| 杂色鲍（期刊中文摘要写明），唐利妹、张刚生 (2015) | **实测：**边缘生长端文石层 **499±35 nm**；成熟中心区 **371±36 nm**；SEM＋光纤反射谱。边缘综合色为蓝＋黄，中心为红＋蓝。 | 只获取到原刊摘要；不可补写其未核对的峰位、入射角或制样厚度。[原刊摘要](https://jogg.cug.edu.cn/cn/article/id/5515d970-5f17-4f0c-b811-8e487545ebc6) |
| 虹鲍 **H. iris**，Hizukuri et al. (2025) | **实测：**蓝区文石 **245±38 nm**；绿区 **293±27 nm**；FIB-TEM间层 **11±3 nm**，EDS显示其中存在有机膜。 | Fig.5d,e（各100次SEM板厚测量）；Fig.6a,d及Experimental。与2003样品的21–31nm不同，应保留样品差异。[论文PDF](papers/nacre_nanogaps_2025.pdf)；[DOI](https://doi.org/10.1038/s41598-025-21872-z) |
| 鹦鹉螺 **Nautilus pompilius**，同上 | **实测：**文石板厚 **276±70 nm**。 | Fig.5g，菲律宾样品；仅适合作同类珍珠层比较。[DOI](https://doi.org/10.1038/s41598-025-21872-z) |
| 一颗近无色大溪地珍珠，Fan et al. (2021) | **实测：**珍珠层总厚约 **0.5 mm**，SEM周期约 **330 nm**；**反演：**扣去**假设**的25nm有机层，得到文石约 **305 nm**，与颜色图反演300–325nm一致。 | Fig.4、Results；本论文明确说SEM不能分辨有机层实际厚度，25nm不是该样品测量结果。[论文](https://doi.org/10.1038/s41598-021-99327-4)；[PDF](papers/nacre_structural_color_2021.pdf) |

**层数口径要写清。** Salman 的SI用超过3300层的实测断面模型测试探测深度；正式论文估计H. rufescens的光学取样深度约350层、H. iris约150层。这是光谱拟合的有效深度，不是所有贝片的固定层数。另其公开代码 `layers=201` 逐项交替文石／有机，实际为101文石＋100有机单层；不能把“200 layers”擅自写成200对周期。[论文Methods与SI§3](https://doi.org/10.1073/pnas.2023623118)；[作者代码](https://github.com/katsgroup/PNAS_Nacre/blob/main/HTC_spectral_fit_ppol_example_PNAS.m)

### 3.2 折射率、角度与实测光谱

- **文献参数，非古盘实测：**Salman 引用文石在589nm的三主折射率 **1.681、1.686、1.530**，模拟取各向同性 **1.63**、有机层 **1.43**、有机厚度 **25nm**；忽略色散、吸收。其文石层搜索区间150–600nm、无序度σ=5–70nm都是拟合网格，不应当作实测分布。[Methods](https://doi.org/10.1073/pnas.2023623118)
- **实测测量几何：**Salman 的HIT采400–1000nm、204波段；H. rufescens现场点使用 **14° p偏振、30° p/s偏振**，相机接收角约±9°。SI Fig.S1有两种鲍壳由近正入射转向掠射时红黄转绿蓝紫的照片；正文/代码给出测量谱与TMM拟合。其拟合把谱峰归一到1，**不能把归一化谱当绝对反射率BRDF**。[Methods；SI§1](https://doi.org/10.1073/pnas.2023623118)；[角度照片裁图](img/optics_HIT_2021_S1_angle_photos.png)
- **独立角分辨实测：**Finnemore et al. (2012)对天然 **Haliotis tuberculata** 与人工7双层材料作 **15–75°**、3mm²光斑的镜向反射测量。Fig.4a,b直接给“波长×镜向角”热图，第二、第三级反射带随角向短波移动；人工薄膜以±15nm无序模拟更接近实测。人工样品是CaCO₃/PVP（含方解石），不可称天然文石的精确参数验证。[论文](https://doi.org/10.1038/ncomms1970)，Fig.4及Methods；[谱图](img/optics_Finnemore_2012_F4_angle_spectra.png)；[正式PDF](papers/artificial_nacre_2012_published.pdf)
- **具体实测峰位：**Ozaki et al. (2021)的三颗Akoya珍珠橙／粉绿／绿样本，其第二级**实测**反射带中心约 **560、620、700nm**。用**假设** `n文石=1.68, n有机=1.5, d有机=10nm` 反演为 **324、360、408nm** 文石层；这不是SEM直接读数。其Fig.3/4中的0°、20°、40°、60°曲线是**计算角谱**，不要误称角分辨实测。[论文pp.3–5 Fig.2、3](https://doi.org/10.1038/s41598-021-94737-w)；[实测谱图](img/optics_Ozaki_2021_F2_measured_spectra.png)

**简单理论作检查，不作唯一着色器。** 对平行双层、给定干涉级次m，近似峰位为 `m λ = 2[n_a d_a cosθ_a + n_o d_o cosθ_o]`，内角由Snell定律求；增大入射角会缩短同一干涉级次峰波长。多个级次同时落在可见区时，综合色并不遵循单一“厚→红、薄→蓝”的色相轴。[Fan2021 Eq.1](https://doi.org/10.1038/s41598-021-99327-4)

作者仓库示例实测数据已保存为 [MAT](sources/optics_code/test_reflectances_iq.mat) 和无改值转换的 [CSV](sources/optics_code/test_reflectances_iq.csv)：204×2，波长397.32–1003.58nm；脚本称它为Specim IQ示例反射谱。**仓库没有为此示例标明贝种／位置／入射角／校准口径，不能把它当特定古器物或具名样本的绝对反射谱。** [数据原件](https://github.com/katsgroup/PNAS_Nacre/blob/main/test_reflectances_iq.mat)；[读取脚本](https://github.com/katsgroup/PNAS_Nacre/blob/main/HTC_spectral_fit_ppol_example_PNAS.m)

### 3.3 “磨薄以后颜色怎么变”应分成三个问题

1. **总片厚减小，保留的文石单层厚度未变：推断。** 减少的是重复周期数N，未必改变主要Bragg峰位；会改变反射强度、谱带宽、透射量与衬底贡献。把工艺嵌片厚0.05mm直接作为“干涉薄膜厚50,000nm”输入单层虹彩节点，在物理含义上不成立。依据为TMM对逐层厚度及边界条件的定义，而非针对古盘打磨的实验。[Byrnes2016](https://arxiv.org/abs/1603.02720)；[HIT的层数测试](https://doi.org/10.1073/pnas.2023623118)
2. **磨到不同生长深度，露出的周期本来不同：文献实测与推断分开。** Hizukuri2025正文p.6记载Ammolite磨后由红变绿（SI Fig.S13），解释为随深度层周期不均匀。**这是化石菊石，不是软螺钿减薄实验。** 对现代贝壳的类比只可写为推断；磨薄不会把所有埋藏晶板机械地均匀压薄。[DOI](https://doi.org/10.1038/s41598-025-21872-z)
3. **磨光改变表面阶梯／划痕，可能改变衍射：实测的特殊样本。** Liu, Shigley & Hurwit1999报告法属波利尼西亚 **Pinctada margaritifera**，抛光前虹彩很弱、抛光后增强；SEM表面沟距约 **3.38µm（296线/mm）**，另一面约 **11.5µm（87线/mm）**，激光实验有离散衍射级次。它支持“表面衍射可以很重要”，不能推翻不同物种/制样的多层干涉证据，亦不能概括为所有抛光贝片必然同样变化。[原文DOI](https://doi.org/10.1364/OE.4.000177)，pp.178–180；[作者论文全文转载入口](https://www.researchgate.net/publication/24361894_Iridescence_color_of_a_shell_of_the_mollusk_Pinctada_Margaritifera_caused_by_diffraction)（未获取有效PDF）

**缺口：**本次未找到针对元明薄螺钿嵌片、控制总厚度连续磨薄同时记录角分辨反射谱的公开实验。可证伪方案是现代同种贝料同一位置留楔形厚度，逐点记录总厚、SEM周期/层数、粗糙度和角谱；固定背衬重复黑漆／白底／金属箔对照。这里是建议实验，不是本次已做工作。

## 4. 现成模型、代码与本镜头的选择

| 模型／实现 | 已核实内容 | 用于圆盘的适配与限制 |
|---|---|---|
| **Salman et al. 2021 HIT，TMM＋Monte Carlo** | 作者 [MATLAB仓库](https://github.com/katsgroup/PNAS_Nacre) 含两偏振TMM、随机层厚与实测拟合；已下少量源码至 `sources/optics_code/`。 | **首选物理依据。** 能保留晶板平均厚度、无序、层数和角度意义；应自己输出未归一化 `R(λ,θ)` 供渲染，不能把原拟合谱当现成BSDF。仓库未见LICENSE，不把公开可读等同于已授商业再分发权。 |
| **Byrnes《Multilayer optical calculations》＋Python tmm** | 作者 [代码](https://github.com/sbyrnes321/tmm) 明确MIT；支持相干/非相干多层、斜入射、吸收、s/p偏振及颜色计算。[论文](https://arxiv.org/abs/1603.02720) | 适合重建文石／有机随机堆栈、加入有限片厚和吸收衬底，预计算角度×层厚×无序度的谱LUT；它是平面光学求解器，仍需微表面BSDF和可见性／采样。 |
| **Ozaki et al.《Structural colors of pearls》2021** | TMM＋Kubelka–Munk散射；GLSL渲染与实拍对比（Fig.5），已下论文；未找到论文附带开放源代码。[DOI](https://doi.org/10.1038/s41598-021-94737-w) | 对珍珠白体、内透射与互补色有价值；黑漆背衬薄片没有白色珠核，不应照搬其核心散射halo。[对比图](img/optics_Ozaki_2021_F5_render_vs_real.png) |
| **Belcour & Barla SIGGRAPH 2017** | [作者页](https://belcour.github.io/blog/research/publication/2017/05/01/brdf-thin-film.html)提供论文、BRDFExplorer GLSL与旧Mitsuba C++；已下 `papers/belcour_2017.pdf`、`belcour_2017_code.zip`。反射Airy项分析积分减少RGB谱混叠。 | 是**单薄膜夹层**微表面虹彩，不是天然珍珠层随机多层模型；可作快速艺术近似、清漆／薄层研究。随附readme限定反射、说明Mitsuba白点问题；包内未见独立许可证。 |
| **KHR_materials_iridescence** | [Khronos正式扩展](https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_materials_iridescence)含GLSL近似和参数定义，基于Belcour/Barla。 | 现成实时路径，但只处理两界面薄膜；“螺钿总片厚”不能直接当该薄膜厚度。 |
| **Kang 2025，UE5 Substrate韩国螺钿** | 原论文元数据/摘要：四种螺钿材质，专家定性评价与运行性能，DOI **10.9728/dcs.2025.26.6.1699**。[期刊索引](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003217168) | 直接相关制作案例，但未获取全文／代码，不能引用节点数、光学数值或声称通过角谱测量验证。 |

**推荐方向（推断）：**用每块嵌片的固定“晶板平均厚度＋无序＋局部层法线”驱动随机多层TMM谱LUT，配透明介质表面高光和黑漆吸收衬底。若制作为RGB实时引擎，先按实际灯光谱与CIE响应离线积分再存LUT，别仅在RGB三个波长求解；Belcour2017讨论了离散RGB取样造成的谱混叠。[Belcour2017](https://doi.org/10.1145/3072959.3073620)；[Byrnes2016](https://arxiv.org/abs/1603.02720)

**旋转镜头关键推断：**纯绕平盘法线自转，若入射／观看几何不变、照明在各对应位置均匀、层平行盘面且各向同性，则每个材料点的局部入射角不因自转改变，整盘不应统一循环色相。希望转盘出现真实变彩，应让各嵌片局部层法线有贝料来源造成的倾斜／波动，或让盘倾转、照明形成非轴对称空间变化；有表面光栅的片还能因切线方向随旋转而改变衍射。微表面反射需按光源与视线的半向量对应局部微面，不能仅用相机对盘法线夹角查色。此结论是各向同性平面层模型的对称性推导，不是古盘旋转实测。[TMM斜入射定义](https://arxiv.org/abs/1603.02720)；[微表面薄膜理论](https://doi.org/10.1145/3072959.3073620)

完成判据建议（未实施）：同一片角谱随倾角峰位合理移动；不同切片的色块在物体坐标固定；改变灯位可改变彩色反射；仅绕法线转动的均匀平层对照不产生虚假的全局hue动画；不同N但相同周期的对照不能被误当成单层厚度扫描。

## 5. 对这个特写镜头的具体选择与证据边界

三个实质不同的方案是：固定RGB贴图只能保留静态构图；单膜虹彩BSDF已有成熟实时实现，但层厚含义不对应天然珍珠层；**随机多层TMM预计算谱查找表，再结合表面反射与每片局部层法线**，能直接关联本报告中的显微参数与角谱，是当前最值得采用的方向。前两条是工程适用性判断，后一条的物理机制依据HIT与Byrnes；没有声称本项目已实现、运行或校准渲染器。[HIT论文及代码](https://github.com/katsgroup/PNAS_Nacre)、[tmm](https://github.com/sbyrnes321/tmm)、[单膜微表面实现](https://belcour.github.io/blog/research/publication/2017/05/01/brdf-thin-film.html)

**[推断/初始参数候选]** 可以从红鲍候选开始：文石平均420 nm、σ50 nm（指定断面实测），有机25 nm、n文石1.63、n有机1.43（论文模型假设），约100对周期作起点（代码规模），再对照论文实测谱。100对总厚约44.5 µm是这些假设的算术结果，不是古盘片厚。片与片的参数及法线应固定在物体坐标，避免噪声随相机游走；对实际黑漆/胶/箔边界条件须重新求谱，不能照搬空气中贝壳的归一化数据。[HIT实测、Methods及代码](https://doi.org/10.1073/pnas.2023623118)、[逐层边界条件](https://arxiv.org/abs/1603.02720)

**[推断/建模建议]** 画面应有三套独立材质区域：吸收性黑漆、分片的珍珠层、并嵌金/银。阴刻线是贝面细节，点螺拼缝是贝片边界，不能共用一张“所有细线都发彩”的遮罩。局部残漆、微小台阶与旧修复可作为参照选项，但其高度、粗糙度、清漆折射率没有本次目标器实测，应留成待校准参数。[上博材质与阴刻描述](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/P00004947)、[AAM刻沟观察](https://collections.asianart.org/wp-content/uploads/sites/5/2024/05/Williams_2008_Conservation_of_Asian_Lacquer.pdf#page=34)、[爱知表面观察](https://apmoa.museum/assets/pdf/bulletin/2014/apmoabulletin2014kimurap98-117.pdf#page=3)

尚不能交付为“已知实测”的项目：同名上博盘贝种和片厚、最细实体贝丝/阴刻沟宽、罩漆厚与折射率、贝背箔分布、原器绝对BRDF，以及其旋转色移曲线。本次取得的是多件比较物、现代生物样品和可验证模型；最终报告没有用这些替代目标器检测。

## 6. 文件、取得状态与后续可用线索

- 图片优先看 [`img/README.md`](img/README.md)；每个保留文件都有独立来源与授权状态，附实有像素和SHA-256。正文的代表图并未涵盖全部图像。真正显微、普通局部、X光、论文谱图、计算图分别标注；PDF裁图或解码校正都记录处理方式。
- 论文/标准/图录见 [`papers/README.md`](papers/README.md)。HIT本地版是**含SI的预印本**；正式正文另经期刊页面核对。傅举有文件只有两张已取得的单页，缺页未冒充全文。Finnemore同时取得作者稿与正式版，图谱以正式版为准。
- 有价值但没有取得原图的线索包括：旧金山亚洲艺术博物馆BL77M3明代山水长方盘（官网列多图，但下载端受限）、京都国立博物馆H甲247明代楼阁人物四方盆（数据库无图）、大阪市立美术馆田万收藏同类明盘（展单有题名、无可用尺寸/高清图），以及港大美术博物馆HKU.L.1966.0299清代薄螺钿人物圆盘（1662–1795、径13、高1.5，页面下载403）。[旧金山条目](https://searchcollection.asianart.org/objects/14690/rectangular-tray-with-landscape-design)、[京都条目](https://knmdb.kyohaku.go.jp/30425.html)、[大阪官方展单](https://www.osaka-art-museum.jp/wordpress/wp-content/uploads/2015/04/02c6b663d85764aae4b669045ebb0823.pdf)、[港大条目](https://ebooks.lib.hku.hk/items/show/85)
- 补充对象如爱知M1505明清香合（带标尺×10裂隙/脱片图）、浦添琉球盘/桌/食笼（有背箔文字证据）和Smithsonian修复照片，分别在逐图清单中标注对象、年代尺寸或链接，没有混成元明中国圆盘。[爱知科学报告](https://apmoa.museum/assets/pdf/bulletin/2014/apmoabulletin2014kimurap98-117.pdf)、[浦添馆藏](https://www.city.urasoe.lg.jp/kokyoshisetsu/art/609e776a3d59ae2434bfe14b/)、[Smithsonian对象](https://asia.si.edu/explore-art-culture/collections/search/edanmdm%3Afsg_S1987.369/)


