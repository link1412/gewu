# 康熙景德镇窑豇豆红釉印盒：实物、材料与渲染依据

调研日期：2026-11-02。用途：印盒盖顶穹面的近距离转台镜头。原始器物照片、原像素裁图和科学显微图分别标识；下载文件的逐张来源、授权、分辨率与校验值见 [img/README.md](../../ref/jiangdouhong/img/README.md) 和 [img/manifest.json](../../ref/jiangdouhong/img/manifest.json)。论文目录见 [papers/README.md](../../ref/jiangdouhong/papers/README.md)。

## 1. 推荐方向和证据边界

**推荐：以一只有可靠尺寸的印盒定形，用透明釉表面、内部着色/散射层和白瓷胎的分层材质表现“粉润”，用空间变化控制红色光学厚度与绿苔区。** 优先参照大都会 **66.206.17** 的红—粉—绿连续过渡和克利夫兰 **1942.673** 的独立盒盖视图；这两件可以看作不同外观选项，不应把各自最强的特征机械叠满同一件。几何依据为馆藏尺寸，材料结构依据为馆方工艺解释与铜红光学论文，具体贴图和参数仍是渲染工作假设。[Met 印盒](https://www.metmuseum.org/art/collection/search/42423)、[CMA 印盒](https://www.clevelandart.org/art/1942.673)、[BM 工艺说明，PDF p.134](https://www.britishmuseum.org/sites/default/files/2021-05/large_print_guide_room_95_chinese_ceramics.pdf)、[Cuvelier 等光学模型](https://doi.org/10.1007/s00339-011-6707-3)

完成调研的可检查结果是：器物图像能追溯到藏品与许可；关键材料论断有直接来源和证据类型；数值带样本身份、单位和测量/拟合区别；无法取得的原文及缺失实测明确列出。**没有找到可确认来自康熙豇豆红印盒同一位置的“釉厚—铜粒径—铜浓度—价态比例—绝对反射谱”整套数据。** 下文不会将现代试片、宣德祭红和乾隆窑变的数值拼成一套康熙实测参数。

全文标签：

- **〔实测·某样本〕**：原论文的测量；“仅摘要”意味着未取得正文，不能确认全部实验条件。
- **〔拟合/模拟〕**：模型输入、反演量或计算结果，不是直接物性测量。
- **〔馆藏/文献〕**：馆方编目、工艺解释或历史记载，不等同截面分析。
- **〔观察/推测〕**：本次对照片的观察、渲染建议和因果外推。

## 2. 实物和照片：先看哪些

### 2.1 已下载、最适合制作的器物

以下尺寸是**实物尺寸**；图片的像素尺寸另见图像目录。表内“正面/斜俯视”描述相机方向，**不代表经过标定的斜光摄影**。

| 器物、年代、藏处 | 实物尺寸与馆藏号 | 本地照片和用途 | 出处与许可 |
|---|---|---|---|
| 豇豆红印盒，馆方定年1713–22；纽约大都会 | 高 **3.5 cm**，径 **7.1 cm**；**66.206.17** | [闭盒斜上方，4000×3000](../../ref/jiangdouhong/img/met_box_1.jpg)；[底视，4000×3000](../../ref/jiangdouhong/img/met_box_2.jpg)。盖顶弧面、绿斑带、粉白过渡最清楚 | [馆藏](https://www.metmuseum.org/art/collection/search/42423)；Public Domain / CC0 |
| 印盒，康熙1662–1722；克利夫兰艺术博物馆 | 高 **3.9 cm**，径 **7.4 cm**；**1942.673** | [闭盒5257×3649](../../ref/jiangdouhong/img/cma_1942_673_full.jpg)；[独立盖4266×3678](../../ref/jiangdouhong/img/cma_1942_673_b_full.jpg)；[盒身内侧4266×3705](../../ref/jiangdouhong/img/cma_1942_673_a_full.jpg)。同名 `.tif` 为原始大图，JPEG仅为便利查看而转换 | [整器](https://www.clevelandart.org/art/1942.673)、[盖](https://www.clevelandart.org/art/1942.673.b)、[盒身](https://www.clevelandart.org/art/1942.673.a)；CC0 |
| 暗刻团纹太白尊，17世纪晚期、康熙款及本朝；纽约大都会 | 高 **8.7 cm**，宽 **12.9 cm**；**91.1.407** | [正侧4000×3000](../../ref/jiangdouhong/img/met_waterpot_1.jpg)；[底款4000×2460](../../ref/jiangdouhong/img/met_waterpot_2.jpg)。低饱和灰粉、颈部绿带、浅色内部的对照 | [馆藏](https://www.metmuseum.org/art/collection/search/51221)；Public Domain / CC0 |
| 苹果形水丞，康熙1662–1722；华盛顿美国国家美术馆，Widener Collection | **7.6×9.9 cm**；**1942.9.503** | [斜前3000×2464](../../ref/jiangdouhong/img/nga_apple_front.jpg)；[底视](../../ref/jiangdouhong/img/nga_apple_base.jpg)。大面积淡粉云斑与密集红色微斑 | [馆藏](https://www.nga.gov/artworks/1681-water-pot)；本件网页不提供开放下载许可，保守按许可未确定、仅研究参照记录 |
| 柳叶瓶 / Amphora Vase，康熙1662–1722；美国国家美术馆，Widener Collection | **15.6×5.3 cm**；**1942.9.518** | [正面1465×3000](../../ref/jiangdouhong/img/supp_nga_willow_1942_9_518_front.jpg)；[底视2958×3000](../../ref/jiangdouhong/img/supp_nga_willow_1942_9_518_base.jpg)。柔和粉色、局部淡绿和细长器形 | [馆藏](https://www.nga.gov/artworks/1696-amphora-vase)；许可情况逐张见图像目录 |
| 柳叶瓶，康熙款及本朝；冈田美术馆旧藏，2025年苏富比拍品1076 | 高 **15.5 cm** | [正面1500×2000](../../ref/jiangdouhong/img/supp_sothebys_okada_willow_front.jpg)。白背景大、器物有效像素较少；用于器形和大斑布局 | [一手拍品](https://www.sothebys.com/en/buy/auction/2025/masterpieces-of-asian-art-from-the-okada-museum-of-art-hk1632/a-rare-peachbloom-glazed-willow-leaf-vase-mark-and)；未见开放许可，版权保留；拍卖后现藏处未确认 |
| 菊瓣瓶，馆方定年1678–88；纽约大都会 | 高 **21 cm**；**14.40.374** | [正面A](../../ref/jiangdouhong/img/met_juban14_40_374_1.jpg)、[另一朝向B](../../ref/jiangdouhong/img/met_juban14_40_374_2.jpg)、[底视](../../ref/jiangdouhong/img/met_juban14_40_374_3.jpg)，长边4000。两朝向高光与色斑对照 | [馆藏](https://www.metmuseum.org/art/collection/search/42232)；Public Domain / CC0。馆方英文只题Vase，按可见菊瓣记器形 |
| 莲瓣瓶，康熙1662–1722；克利夫兰 | 高 **21.2 cm**；**1942.668.1** | [2149×3400](../../ref/jiangdouhong/img/cma_1942_668_1_print.jpg)。偏浅、均匀粉红与镜面高光 | [馆藏](https://www.clevelandart.org/art/1942.668.1)；CC0 |
| 细长瓶，康熙；克利夫兰 | 高 **14.6 cm**；**1942.670.1** | [2208×3400](../../ref/jiangdouhong/img/cma_1942_670_1_print.jpg)。较深红及近底淡绿，配后加支座 | [馆藏](https://www.clevelandart.org/art/1942.670.1)；CC0；馆方英文定名Bottle with Peach Bloom Glaze |

两张特别实用的原像素裁图：**[绿苔局部](../../ref/jiangdouhong/img/met_box_crop_green_moss.png)**（1280×380）和 **[红到粉白过渡](../../ref/jiangdouhong/img/met_box_crop_red_to_pink.png)**（1160×410），均裁自 Met 66.206.17，没有放大、增清或调色。它们是局部查看工具，不能称为独立微距拍摄，也不能以像素直接换算绿斑的毫米直径；穹面透视和局部曲率尚未校正。[原图及许可](https://www.metmuseum.org/art/collection/search/42423)

![Met印盒绿苔局部，原像素裁切](../../ref/jiangdouhong/img/met_box_crop_green_moss.png)

**〔照片观察〕** 这张图中的深色核心常有浅绿外围，密度沿盖缘增加；红色区和粉白区之间是破碎、渗化的边界，亮白高光横跨带色区域。把可见颜色斑全做成表面凹凸会混淆色斑与形貌。图像本身不足以证明每一个黑点的化学相，也不足以从高光反演唯一粗糙度。[原图](https://www.metmuseum.org/art/collection/search/42423)

### 2.2 补充实物与没有强行补齐的字段

| 对象 | 已核资料 | 本次状态 / 注意 |
|---|---|---|
| 北京故宫“康熙款豇豆红釉印泥盒” | [官方页](https://intl.dpm.org.cn/Ceramicsis/971.html)，[本地800×600图](../../ref/jiangdouhong/img/dpm_box.png) | 仅网页图，非高清；该页未给尺寸和可核文物号，不套用其他故宫印盒尺寸。未见开放授权，©故宫博物院，仅研究参照 |
| 上海博物馆印盒 | [上博官方说明](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/CI00005206)；大阪东洋陶瓷美术馆展签另记上海藏 **26366**：高 **3.7**、口径 **7.2**、底径 **3.9 cm** | [访客Wmpearl实拍830×716](../../ref/jiangdouhong/img/shanghai_box_wmpearl.jpg)由作者释入公有领域；照片无文物号，不能保证就是26366，故不把两者硬配。[照片及授权](https://commons.wikimedia.org/wiki/File:Cowpea-red_glazed_seal-box,_Jingdezhen_ware,_Kangxi_reign_1662-1722,_Shanghai_Museum.jpg)、[官方展签PDF，第06项](https://www.moco.or.jp/wp/wp-content/uploads/2024/10/Shanghai_Museum_and_MOCOC_Collection_Captions.pdf) |
| Walters印盒 **49.428**，1710–1722 | [馆方](https://art.thewalters.org/object/49.428/)明示CC0；描述盖缘灰绿云斑与苹果绿点 | 网站及下载直链返回403，本次未下载。网页把 **7.2 cm** 标作“H”，与扁盒器形可疑；保留原标签，不擅改为径 |
| Smithsonian NMAA印盒 **F1943.5a-b**，康熙 | 高×宽 **3.6×7.2 cm** | [馆方资料](https://asia.si.edu/explore-art-culture/collections/search/edanmdm%3Afsg_F1943.5a-b/)，图片端403，未列为已下载 |
| 台北故宫豇豆红小盒 **中瓷001432N000000000**，康熙 | 高 **3.7**、口径 **7.1**、底径 **4.0 cm**；一式十件同储木盒 | [馆藏](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/19159?dep=U&mode=full)；馆方提供100万像素CC0、600万像素CC BY4.0；本地连接TLS失败，没有声称拿到这组图 |
| 台北故宫莱菔瓶 **故瓷014126N000000000**，康熙 | 高 **20.2 cm**、口径 **3.0 cm**、腹围 **25.2 cm**；口、肩、底有苹果绿及黑苔点 | [馆藏及许可](https://digitalarchive.npm.gov.tw/Collection/Detail/26186?dep=U)；同上下载受阻；注意腹围不是腹径 |
| Met细长瓶 **14.40.372** | [馆页](https://www.metmuseum.org/art/collection/search/52049)与[本地正面](../../ref/jiangdouhong/img/met_vase_1.jpg)、[底款](../../ref/jiangdouhong/img/met_vase_2.jpg) | 图像清楚，但网页尺寸高8.6/径12.5cm与细长器形冲突；API结构化measurements又为高14.6cm，**均不用于定尺度**。留作色泽图，不能把错误字段传入模型 |

**当前图像限制**：没有找到同一印盒完整360°、严格正投影、带色卡的多灯位/交叉偏振/已标定掠射光图组。现有资料是馆方工作室照、个别独立盖图及访客照；无法据此唯一恢复背面斑纹、真实表面粗糙度和绝对色度。绿苔裁图、分件俯视、两朝向瓶照提供可用的视觉约束；未见的背面需要明确作为艺术补全。

## 3. 釉的工艺：哪些能确定，哪些仍是复原解释

### 3.1 吹釉、底釉、面釉、铜所在位置

**〔馆藏/工艺解释〕** 英国博物馆对康熙菊瓣瓶 **PDF579** 的说明支持：**清釉底层 → 含铜色料 → 清釉罩层 → 还原烧成**。原文对色料施法保留“**possibly blown on**”（可能吹施），且说罩上进一步的清釉层，没有限定总共三层或五层。这里的“三段”是施用材料顺序，不能当成烧后显微截面的固定层数。[BM官方导览PDF，第134页，case64-1](https://www.britishmuseum.org/sites/default/files/2021-05/large_print_guide_room_95_chinese_ceramics.pdf)

**〔历史文献〕** 《陶说》卷一所收《陶冶图说》介绍一般吹釉：竹管一端蒙细纱、蘸釉吹附，次数随器物及釉种变化。它记述的是乾隆八年（1743）一般制瓷工艺，**不是康熙豇豆红印盒的专用配方，也不能把吹数当材料层数**。[《陶说》卷一·说今，“蘸釉吹釉”](https://ctext.org/wiki.pl?chapter=898246&if=gb)；[台北故宫学术季刊对原图说的引录，纸页197](https://www.npm.gov.tw/NewChineseArtDownload.ashx?bid=3823)

**〔文献解释，尚非本器实测〕** 铜—石灰色料被夹在清釉之间、通过局部助熔和施料厚薄形成红绿差异，是Wood体系常见复原路线；本次可直接读到的苏富比一手器物说明采用此说，仍应与BM的“可能”一起保留不确定性。它不足以证明古器用的是金属铜粉而非含铜化合物：**施入原料的化学形态与烧后着色粒子的Cu⁰身份是两件事。** [苏富比柳叶瓶，Catalogue note](https://www.sothebys.com/en/buy/auction/2025/masterpieces-of-asian-art-from-the-okada-museum-of-art-hk1632/a-rare-peachbloom-glazed-willow-leaf-vase-mark-and)

**〔证据缺口〕** 网上“康熙铜红固定五层、铜在第三层”的概括未定位到专门的豇豆红印盒切片、图号和测量表；涵盖祭红、郎红、豇豆红的综述不能完成这一步证明。可以在材质里用“透明上层—带色内部—胎”建模，但报告不能写成目标器已测三层或五层。[相关综述，需与原始证据区分](https://www.ihchina.cn/Article/Index/detail?id=24981)、[BM说明](https://www.britishmuseum.org/sites/default/files/2021-05/large_print_guide_room_95_chinese_ceramics.pdf)

### 3.2 绿苔点：不能只写“局部未还原的铜”

**〔桃花片专门分析·仅官方摘要核实〕** 孙荆、陈显求、阮美玲、赵达峰，《桃花片铜红釉的着色机理》，《硅酸盐学报》**19(6),549–555 (1991)**，分出三种区域：红区为细分散**金属铜，粒子小于2 μm**；可见绿苔点是**局部玻璃基质富Cu²⁺的绿色小环**；红中泛绿区与**含硫化铜微粒**相关。本次未取得正文，**样本年代/出处、实验方法细节和环尺寸尚不能核实**，故这是“桃花片研究报告的结果”，不能升级成指定康熙传世印盒的实测。[期刊官方中英摘要](https://jccsoc.cbpt.cnki.net/portal/journal/portal/client/paper/844eb0efd60bd44ee44fdbb867f813ab)

**〔解释边界〕** “有Cu²⁺”不能单凭成品区分**从未完全还原**与**先还原再氧化**的烧成历史。国博藏品说明采用“部分氧化产生绿色斑点”的概括，适合讲工艺大意；模拟时应保留离子绿环与其他泛绿微结构的区别，不能声称一切绿色都是同一个残留CuO颗粒机制。[国博官方器物说明](https://www.chnmuseum.cn/zp/zpml/201812/t20181218_23854.shtml)、[1991分析摘要](https://jccsoc.cbpt.cnki.net/portal/journal/portal/client/paper/844eb0efd60bd44ee44fdbb867f813ab)

**〔渲染推测〕** 把大尺度灰绿/苹果绿云区、深色细点及外围浅绿晕分开控制，红区保持更细密的深浅变化。可见苔点是宏观局部区域，纳米铜粒子是亚像素的着色/散射成分；两者不能用同一粒子尺度替代。[视觉约束：Met原图](https://www.metmuseum.org/art/collection/search/42423)、[现代粒径实测及模型](https://arxiv.org/abs/1302.2302)

### 3.3 大红袍、娃娃脸、美人醉、苹果绿的成因

**先区分名称和机制：这些是相互重叠的鉴赏名称，没有检索到四个名称分别对应的标准色度、铜价态比例或固定配方。** 故宫把“大红袍”列为上乘品相，把含深浅斑点和绿苔者称“美人醉/美人霁”；上博以浅红娇艳解释“娃娃脸/桃花片”，并将带绿苔者联系“美人醉”；台北故宫把偏绿斑晕称苹果绿或苔点。[故宫釉洗说明](https://www.dpm.org.cn/collection/ceramic/227026.html)、[上博印盒说明](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/CI00005206)、[台北故宫莱菔瓶说明](https://digitalarchive.npm.gov.tw/Collection/Detail/26186?dep=U)

| 外观名 | 文献支持的外观意思 | 可以检验的材料/渲染解释；均不是该色名的独占实测成因 |
|---|---|---|
| 大红袍 | 较均匀、鲜明的红，属鉴赏等级 | 金属铜红的吸收光学厚度、粒径谱及散射比例共同改变红的饱和与明暗；**不能仅归因于“温度更高”或“铜更多”**。[现代铜红实验模型](https://doi.org/10.1007/s00339-011-6707-3) |
| 娃娃脸 / 桃花片 | 较浅、柔和的粉红 | 作为较弱红吸收、白胎回返光和体散射的组合来拟合；是物理方向的推测，尚无同一康熙样本跨色区测量把名称与单一变量绑定。[模型](https://arxiv.org/abs/1302.2302)、[上博命名](https://www.shanghaimuseum.net/mu/frontend/pg/article/id/CI00005206) |
| 美人醉 / 美人霁 | 深浅红、绿苔或斑晕共存 | 宏观不均匀性与局部铜赋存/微结构有关；绿色不能全归到金属铜粒径变化。[故宫命名](https://www.dpm.org.cn/collection/ceramic/227026.html)、[桃花片分析摘要](https://jccsoc.cbpt.cnki.net/portal/journal/portal/client/paper/844eb0efd60bd44ee44fdbb867f813ab) |
| 苹果绿 | 绿斑或较连片的淡绿外观 | 绿苔环的Cu²⁺解释有直接分析文献；更广泛“泛绿”另有含硫化铜微粒解释。**不要把色名自动等同某一种铜氧化物纯相**。[台北故宫](https://digitalarchive.npm.gov.tw/Collection/Detail/26186?dep=U)、[桃花片分析摘要](https://jccsoc.cbpt.cnki.net/portal/journal/portal/client/paper/844eb0efd60bd44ee44fdbb867f813ab) |

**〔现代制作实验，非古法证明〕** John Britt与Lindsey Elsey的试烧记录表明，冷却过程的再还原、粗氧化铜撒施等路线可以改变红绿斑；它说明现代仿制的外观存在多条实现路径，不能由某张照片倒推唯一的康熙烧成曲线。[Britt, *Ceramics Monthly*, October2010,40–45](https://ceramicartsnetwork.org/docs/default-source/uploadedfiles/wp-content/uploads/sites/6/2015/06/ceramics-monthly-oct10-cei1010d.pdf)，[本地六页节选](../../ref/jiangdouhong/papers/britt_2010_experiments_peach_bloom_excerpt_pp40-45.pdf)

## 4. 定量实测、浓度、反射谱和截面

### 4.1 数据使用表：不要跨样本混填

| 数据 | 桃花片/豇豆红直接证据 | 可下载的代理证据 | 可否直接用作本印盒实测 |
|---|---|---|---|
| 铜的存在形态/价态 | 1991摘要：金属铜红、Cu²⁺绿环；没有比例 | 现代B23 EELS；宣德祭红XANES；乾隆窑变TEM衍射 | 否；只能比较机制 |
| 金属铜粒径 | 1991：**<2 μm上界**；非平均粒径 | B23：10–50nm及70–150nm；乾隆窑变：50–100nm | 否；可作纳米着色数量级起点 |
| 铜胶体浓度 | 未核到确切体积分数/数密度 | B23光谱拟合φ=8×10⁻⁴；乾隆拟合φ≈10⁻⁴ | 否；拟合量不能记成直接测量 |
| 总釉厚、发色层、罩层 | 未核到目标器数据 | B23总约300μm/红约150μm；宣德总513–674μm | 否；品种/器物/烧成都不同 |
| 反射谱、CIE色度 | 未核到康熙豇豆红标准实测 | 两篇模型论文的谱图、乾隆色度、宣德反射谱 | 否；照片RGB也不能替代绝对谱 |

本表来源与方法逐项见以下三组原论文；1991仅摘要的边界见§3.2。[Cuvelier2012](https://arxiv.org/abs/1302.2302)、[Li/Lei2022](https://arxiv.org/abs/2208.08043)、[路辰等2016](https://html.rhhz.net/ZGKXYDXXB/20160320.htm)、[孙荆等1991](https://jccsoc.cbpt.cnki.net/portal/journal/portal/client/paper/844eb0efd60bd44ee44fdbb867f813ab)

### 4.2 现代铜红试片B23：粒径与浓度最完整的参照

Cuvelier等，*Copper red glazes: a coating with two families of particles*, **Applied Physics A106,915–929(2012)**；[DOI](https://doi.org/10.1007/s00339-011-6707-3)、[作者版](https://arxiv.org/abs/1302.2302)、[本地PDF](../../ref/jiangdouhong/papers/optics_cuvelier_2012_copper_red_glazes.pdf)。下表页码按16页作者版。

| 参数 | 数值 | 证据类型 / 定位 |
|---|---|---|
| 样本 | 现代B23，1280°C还原烧成 | 制作记录，p.2；非古器 |
| 釉厚 | 总约 **300 μm**；内部红区约 **150 μm**，上下无色 | 截面实测，p.3 Fig.2 |
| 小粒子 | 直径 **10–50nm**；数均约 **25nm**，平均体积等效径约 **30nm** | TEM统计，pp.4–5 Fig.4 |
| 大粒子 | 直径 **70–150nm**，数量少 | TEM，Fig.5 |
| 铜身份 | 所测5个小粒子、2个大粒子EELS均为金属铜；另有一个粒子边缘见氧化物 | 局部实测，p.7；不能等于全部铜都为Cu⁰ |
| 小粒子体积分数 | 约 **12×10⁻⁴** | TEM粗估，非全铜浓度 |
| 总金属铜体积分数φ | **8×10⁻⁴=0.08vol%** | 光谱拟合；大粒子占金属铜体积 **20–30%**，不是粒子数量百分比；pp.12–13 |
| 谱与截面图 | 反射/透射Fig.3，拟合对照Fig.18；[本地截面Fig.2a](../../ref/jiangdouhong/img/optics_cuvelier_2012_fig2_cross_section.jpg) | 原始图，未附机器可读谱 |

**〔本样实验+模型〕** 小粒子主要吸收、大粒子贡献散射，Mie计算配四通量传输能拟合该试片的红色与明度。此处“粉润”是分层光学的线索；没有证明康熙豇豆红也恰为这两族及此比例。[原论文](https://doi.org/10.1007/s00339-011-6707-3)

### 4.3 乾隆窑变残片及2022模型：有色度，模型量要另标

Gen Li、Yong Lei，*The computational simulation of the reflection spectra of copper red glaze*, **AIP Advances12,095319(2022)**；[DOI](https://doi.org/10.1063/5.0095570)、[arXiv作者版](https://arxiv.org/abs/2208.08043)、[本地26页PDF](../../ref/jiangdouhong/papers/optics_li_lei_2022_computational_simulation.pdf)。本次读取2022-08-17预印本；出版社正文返回403，不能声称逐字核对终稿。

| 内容 | 数值及身份 | 定位 |
|---|---|---|
| 新测样本 | 故宫南大库遗址出土**乾隆窑变铜红残片** | §3.3；不是康熙豇豆红 |
| 色度 | 三点平均 **L*=33.0,a*=17.7,b*=7.1**，反射谱在约600nm快速上升 | 实测；PDFp.23，Fig.8c；仪器CS-520，p.24 |
| 金属铜粒子 | **50–100nm**，近球形，TEM衍射识别金属铜 | 实测；Fig.8e–f |
| 截面 | 上透明/中红/下透明；Fig.8b标尺200μm | **没有给该片红层厚度数表**；标尺不等于层厚 |
| 残片拟合 | d=50nm，φ≈**1×10⁻⁴**，胎反射率0.65 | 模型拟合；不是TEM测得单分散50nm |
| 默认模型 | n=**1.52**、红层**200μm**、胎反射率0.7 | 假设输入，p.11；非印盒物性 |
| 参数扫描 | d=20/50/100/200nm；φ=0.00003–0.03 | 模拟；Table1–2 |

[本地Fig.8：残片、截面、反射谱与TEM](../../ref/jiangdouhong/img/optics_li_lei_2022_fig8_cross_section_tem_spectra.jpg)。预印本图注写无粒子釉透过比例s₀=0.8，正文写0.6，**内部矛盾未核定终稿如何修正，不把任何一个当准确实测**。Table3的康熙/雍正/乾隆祭红色度是转引数据，也不是新测豇豆红。[作者版pp.20,22–24](https://arxiv.org/pdf/2208.08043)

### 4.4 宣德祭红：总釉厚、罩层、成分、价态与谱

路辰等，《明宣德官窑祭红瓷器的呈色机制》，**中国科学院大学学报33(3),421–426(2016)**；[HTML全文](https://html.rhhz.net/ZGKXYDXXB/20160320.htm)、[官方PDF](http://journal.ucas.ac.cn/CN/article/downloadArticleFile.do?attachType=PDF&id=12365)、[本地PDF](../../ref/jiangdouhong/papers/materials_Xuande_2016.pdf)。三件均为景德镇御窑厂出土**明宣德祭红**，只能作铜红代理。

| 样本 | 总釉平均厚度μm | 表面透明层μm | XRF的CuO当量wt% | 400–700nm谱的正文约值 |
|---|---:|---:|---:|---|
| XD-1 | **665** | **68** | **0.095** | 红端630–660nm附近约23% |
| XD-2 | **674** | **258** | **0.276** | 暗区约5% |
| XD-4 | **513** | **71** | **0.176** | 红区约17%，黑区约5% |

**〔实测·宣德〕** 厚度/成分见纸页424表2–3；反射谱纸页423图2，X-riteVS450、D65、10°、6mm测区。CuK边XANES（p.425 Fig.4）显示XD-1有Cu⁰/Cu⁺混合特征、XD-2更接近Cu⁺；未给价态百分比。**CuO当量是总元素铜的报告方式，不能读成CuO实相含量或金属铜胶体体积分数。** 正文另有泛称铜1–2%与本表不一致，本报告不采用该泛称。[原文表2–3、Fig.2–4](https://html.rhhz.net/ZGKXYDXXB/20160320.htm)

釉基质成分的代表例：XD-1的XRF氧化物当量为 **SiO₂72.71、Al₂O₃12.40、CaO4.51wt%**，这里只摘主要组分，未列出的氧化物不能当作零；它仍是宣德祭红成分，不能替代康熙豇豆红配方。[原文表3](https://html.rhhz.net/ZGKXYDXXB/20160320.htm)

[截面图3](../../ref/jiangdouhong/img/materials_2016_xuande_fig3_cross_sections.jpg)的标尺为250μm；[反射谱图2](../../ref/jiangdouhong/img/materials_2016_xuande_fig2_spectrum.jpg)可查看曲线，未取得CSV原始数据。与B23的层结构不同，不能由“均为铜红”推得统一釉厚或层数。[原论文](https://html.rhhz.net/ZGKXYDXXB/20160320.htm)

### 4.5 最值得继续获取的直接研究

1. **孙荆等1991桃花片研究全文**：能核实样本身份、截面与绿环分析方法；现在只有官方摘要，不提供未核浓度或厚度。[期刊入口](https://jccsoc.cbpt.cnki.net/portal/journal/portal/client/paper/844eb0efd60bd44ee44fdbb867f813ab)。同作者英文题名 *Coloring mechanism of peach bloom copper red glazes*, *American Ceramic Society Bulletin70(12),1900–1905(1991)* 只作为检索线索，未把它算独立重复实验。
2. **熊樱菲、何文权，《清代红釉（彩）瓷的呈色元素分析》，文物保护与考古科学17(4),23–27(2005)**：MCI书目确认EDXRF研究清代馆藏红釉/彩；原表未得，不转抄综述的豇豆红铜百分比。综述误引为2015，本次按原书目记2005。[SmithsonianMCI原研究书目/摘要](https://mci.si.edu/node/1186234)、[后续分析论文原文参考文献5](https://yznkxjs.xml-journal.net/cn/article/pdf/preview/10.7538/yzk.2011.45.11.1399.pdf)

## 5. 有没有现成的光学模型或渲染代码

| 资源 | 实际提供什么 | 能复用到哪里 / 不能承诺什么 |
|---|---|---|
| Cuvelier等2012 | Mie单粒子光学 + **four-flux四通量**传输；两族铜粒子；测量谱与模型对照 | 有实验验证的铜红体层模型；没有找到附带完整开源脚本或成品转台材质。[论文](https://arxiv.org/abs/1302.2302) |
| Li/Lei2022 | Cu/Cu₂O球粒Mie吸收、前后散射；深度分层、多次散射线性方程；谱与色度 | 方程可复现，正文说明用MATLAB；未找到端到端公开代码。模型支持所选条件下Cu比Cu₂O更符合典型红谱，不等于排除所有釉中Cu₂O。[论文](https://arxiv.org/abs/2208.08043) |
| **miepython** | MIT开源的Mie球粒消光、散射、吸收、角分布等计算 | 可计算μa/μs所需单球量；尚需釉层、胎、表面、粒径分布、绿区和空间纹理。不应称作现成铜红shader。[官方代码](https://github.com/scottprahl/miepython) |

**检索结论的范围**：检查上述论文、公开记录，以及标题+code/GitHub/supplementary和铜红shader关键词后，未发现经验证的**豇豆红完整材质、Blender节点、Mitsuba场景或转台渲染资产**。结论是“找到物理模型，未找到可直接套用的成品”，不是“世界上不存在代码”。

### 面向穹面转台的可实施路线〔推测/工程建议〕

比较两条有实质差异的路线：**照片拟合的分层PBR**容易把镜头效果做好，但参数不能解释为古器微结构；**光谱Mie+体传输**能检验粒径/浓度如何影响颜色，但目前缺目标器反射谱和同位置成分，仍会有多解。当前任务优先前者定外观，后者作为机制/参数敏感性验证，不承诺已经完成微结构复原。[实验模型的适用基础](https://doi.org/10.1007/s00339-011-6707-3)、[光谱模型](https://doi.org/10.1063/5.0095570)

- **定形与宏观色斑**：以Met印盒径71mm/高35mm或CMA径74mm/高39mm选一为基准；盖顶曲率由照片约束，盖高和截面不能从整器高度直接拆分。红粉过渡、绿带、苔点在物体空间固定；不能随光照或相机“游动”。背面未见区域另记艺术补全。[Met](https://www.metmuseum.org/art/collection/search/42423)、[CMA盖图](https://www.clevelandart.org/art/1942.673.b)
- **表层**：连续介电高光层覆盖全部色区；铜粒子埋在釉中，因此宏观表面不是裸铜金属。可从2022模型n=1.52起步，但这是代理选值，粗糙度和罩釉厚度尚无目标器标定。[2022模型](https://arxiv.org/abs/2208.08043)
- **内部**：白胎上方的红吸收/散射区通过光学厚度而非单一base-color表现。光谱实现可按粒径族累加 **μa(λ)=ΣNᵢCabs,ᵢ(λ)**、**μs(λ)=ΣNᵢCsca,ᵢ(λ)**；单分散球族 **Nᵢ=6φᵢ/(πdᵢ³)**，全部用一致长度单位。相函数也从Mie或合适近似取得。RGB实现可把代表谱烘焙成查找表；这是实现建议，并非论文提供的现成材质。[Mie代码](https://github.com/scottprahl/miepython)、[四通量验证](https://arxiv.org/abs/1302.2302)
- **绿区**：用独立空间遮罩表达Cu²⁺相关绿晕和更宽泛绿区；不把绿点强行做成凸起绿色金属球。显微米/纳米标尺与肉眼斑纹尺度分别处理。[桃花片分析](https://jccsoc.cbpt.cnki.net/portal/journal/portal/client/paper/844eb0efd60bd44ee44fdbb867f813ab)、[近照](https://www.metmuseum.org/art/collection/search/42423)

建议用实际镜头验证：一盏长条光检验穹面高光连续性、一组柔光检验粉红层次、侧向小光检验绿点是否被错误做成高浮雕；固定曝光和白平衡观察完整转台。**这些是后续渲染验收办法，本次仅交付调研，尚未制作或验证渲染器中的成品材质。** 若要从“视觉可信”进一步主张“物理复原”，需取得同一康熙标本的校准反射谱、截面、粒径分布、价态和浓度；目前这些缺口真实存在，不能用更多照片消除。
