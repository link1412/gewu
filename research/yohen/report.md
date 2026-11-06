# 曜变天目：成因、渲染参数与参照资料

检索日期：2026-11-01。目标物为静嘉堂文库美术馆藏南宋建窑国宝「曜変天目茶碗（稲葉天目）」。

**推荐方向：先建立受证据约束、可切换机制的光谱模型，再用原件的多角度分光数据选模型。现有公开资料不足以把稻叶天目的虹彩唯一归因于某一种纳米结构，更不足以声称已经具备物理意义上的“一比一”参数。** ε-Fe₂O₃ 的存在、薄膜干涉、表面衍射和相分离散射是不同层次的命题，不能互相替代。

可检查的完成标准是：每个输入数值有样本身份、出处和证据等级；原件与古片、现代仿品分开；图像有来源与授权记录；下载量不超过 3 GB；缺失数据不以猜测补成实测。本轮完成了文献核查、参数与媒体清单，并保存了可机读的矿物光学常数。**PDF、照片和视频没有下载到。故 papers/、images/、video/ 目前只有索引，没有伪装成已下载的媒体。视频未播放，关键时间点未核验。**

## 1. 如何读这份报告

- **实测**：作者在明确样本上报告的测量。它仍有仪器、取样位置和不确定度限制。
- **推断/模型**：作者据观察解释机制，或给模拟设定的参数。
- **转引**：未读到最初测量论文，读到作者后续自述或其他论文引述。
- **摘要/公开片段**：未取得全文，不能补写内部页码、误差、图号或完整实验条件。

以下页码原则上为印刷页码。Dejoie 2014 的可读 PDF 镜像多一页 UC 封页：论文 p.2 对应该文件第 3 页。所有论文图像本轮均未完成本地渲染与视觉核对；涉及 OCR 的微米单位另作提示。逐项链接、拟用文件名、授权和下载状态见 [sources.csv](sources.csv)。

## 2. 三只原件与杭州残片：实际知道什么

| 对象 | 已核实的观察或检测 | 能约束什么 | 不能由此推出什么 |
|---|---|---|---|
| 静嘉堂稻叶天目 | 1955 年原件比较的学会官方英文摘要；馆藏与展览资料 | 外观、器形及宏观分布参照 | 未取得原件膜厚、物相分布、椭偏 n/k、校准角谱或 BRDF |
| 藤田天目 | 原物非接触 XRF、光纤反射光谱、数字显微镜 | 有直接光谱峰值和元素比较，见下文 | XRF 不鉴定 ε/α/磁铁矿，也不测纳米周期和膜厚 |
| 大德寺龙光院 | 1953 年原物光学显微观察；所见为官方英文摘要 | 斑内细晶存在，作者提出薄膜解释 | 未测出该碗膜厚；不能把显微亮点直接指认为某一铁氧化物相 |
| 杭州 2009 年古越会馆/方肖鸣藏残盏 | 研究所公布 2023 年专著结论，目录列 Raman、XRD、SEM、角谱等 | 该团队提出斑核银彩、蒸发沉积的膜–微球机制 | 书的数值与方法章节未取得；不能把所有检测统一标为无损，也不能套到三只国宝 |
| 杭州 2017 年述郑斋残器 | 小林仁 2018 年调查文章 | 宏观器形、断面和照片 | 与 2009 年残器不是同一件；2018 年文章谈的是后续研究展望 |

早期原件文献为小山富士夫、山崎一雄〈曜変天目の研究〉，《古文化財の科学》6（1953），19–28，及山崎一雄 1955 年续篇，同刊 10，1–3。**只读到学会官方英文摘要，未取得论文全文**：[1953 所在汇编](https://jsccp.or.jp/pre/data/journal/journal_1-25.pdf)、[1955 所在汇编](https://jsccp.or.jp/data/journal/journal_en_6-10.pdf)。1953 的龙光院斑点见原文 Fig.3，细晶的化学性质当时不能确定。水上和则 2013，p.201、图2 引用的约 **0.1 μm = 100 nm**，是在**假定 n=1.5** 下估算蓝紫干涉色的膜厚，**不是原件测厚结果，更不是厚度分布**。[水上原文](https://senshu-u.repo.nii.ac.jp/record/7478/files/3062_0043_15.pdf)

### 藤田：最接近直接可用的原件光学约束

阿部善也等〈藤田美術館所蔵の国宝「曜変天目茶碗」の理化学的研究―釉薬の光彩の発色に関して―〉，《文化財科学》**87**（2023），31–44。[正式书目](https://ndlsearch.ndl.go.jp/books/R000000004-I033061278)。**期刊全文未取得**；部分二次记录误写为卷 84，应采用正式书目的 87。

同作者大会原始摘要 pp.118–119 已读在线索引：[第40届大会摘要 PDF](https://www.jssscp.org/files/abstract/40_poster_obs.pdf)。p.118 §2 为现场无损方法；p.119 §3 报告光彩区反射峰 **420–500 nm**。XRF 主元素为 Al、Si、K、Ca、Fe，微量 Ti、Mn、Ga、Sr、Zr；光彩和黑地未见组成差别；Ag、Sn、W、Bi 未检出。摘要没有定量 wt%、检出限、完整光谱、峰值绝对反射率及角度定义。作者将近表面铁化合物周期结构作为解释，**不是直接电镜测得原件纳米结构**。

福嶋喜章 2022 的作者自述还给藤田原件内面反射峰约 **400–500 nm**（p.44），区间较宽，不应与前者平均成一条谱。测量在早期项目已进行，不能把发表年份当成首次检测年份：[KAKEN 17K02341 结题报告 p.2](https://kaken.nii.ac.jp/file/KAKENHI-PROJECT-17K02341/17K02341seika.pdf)。

### 杭州：关键数据集中在尚未取得的专著

李伟东、方肖鸣，《建窑“曜变天目”研究》，上海科学技术出版社，2023-12，ISBN 9787547863763，181 页。**只读研究机构公告与书目目录，未读专著正文**。团队第一方结论是：2009 年残盏有黑釉银彩点斑，斑核料蒸发–沉积形成膜–微球结构，二者联合作用产生虹彩。[上海硅酸盐所公告](https://www.sic.ac.cn/xwzx/tpxw/202401/t20240122_6962549.html)、[机构著作记录](https://www.sic.cas.cn/sourcedb_sic_cas/zw/zzk/202408/t20240819_7277708.html)

| 要取得的数据 | 目录给出的正文入口；这些页的数据尚未读到 |
|---|---|
| 斑核尺寸 | §2.3，p.32 |
| 元素组成与分布 | §3.2，p.89 |
| 显微 Raman / 常规及微区 XRD | §3.3，p.94 / §3.4，p.99 |
| SEM 与微区组成 | §3.5，p.114 |
| 角分辨反射谱 | §3.6，p.136 |
| 银彩结论 / 膜–微球机制 | §4.1.3，p.159 / §4.2，p.160 |
| 微球面积占比 / 薄膜模拟 | §4.4，p.163 / §4.5，p.168 |

页码依据[公开目录](https://m.dushu.com/book/14039337/)，不能当成已核查实验结果。[CiNii 藏书记录](https://ci.nii.ac.jp/ncid/BD09489776)列东京艺术大学、宫城学院女子大学，可作为取得原书的路径。2018 年故宫文章 p.27 提醒两件杭州残器都不是正式考古发掘品，研究时应保留发现背景限制。[原文 pp.22–27](https://theme.npm.edu.tw/Academic/ChineseArtDownload.ashx?bid=4169&eid=174)

## 3. 成因的竞争解释与证据边界

| 机制 | 支持证据及样本 | 决定性限制 | 对渲染的要求 |
|---|---|---|---|
| 薄膜干涉 | 早期原件外观解释；现代实验品有薄晶层；部分古片角谱可由膜解释 | 稻叶没有实测膜厚/nk；一些出土片的膜可能来自埋藏腐蚀 | 保留相位的多层 Fresnel / 传输矩阵，含吸收、偏振及厚度分布 |
| 二维表面周期起伏衍射 | 长江/福嶋的窑片 TEM、SEM/FFT；海老塚/岡本的 RCWA 模型 | 皱纹未在稻叶直接测得；油滴照片拟合不是原件纳米测量 | 表面二维空间谱、域方向与尺寸，角度/波长耦合；不能只加彩色漫反射 |
| 短程有序纳米结构的相干散射 | Chen 古片；孙建兴现代仿品相分离球 | 形状、尺寸和相关结构不同；不能把现代仿品当南宋工艺证明 | 粒子形状与复 nk、结构因子/相关长度；独立 Rayleigh 或无色 HG 相函数通常不足 |
| 晶体本征吸收/反射与玻璃中铁离子着色 | α/ε/Fe₃O₄ 等相鉴定；现代研究讨论价态、析晶 | “检测到 ε”不等于“已证明虹彩由 ε 纳米散射产生” | 区分晶体和含铁玻璃；同时计算吸收及波动光学效应 |
| 膜–微球复合 | 杭州团队专著的第一方公告 | 未取得书中尺寸、化学分布与角谱；样本不是稻叶 | 需复合模型并避免双重计算同一界面能量 |

这几条路线可以共存，但不能在未测的前提下任意相加。特别是**表面二维衍射、体内相关散射、单层膜的镜面干涉有不同角分布**。现有证据允许提出候选模型，不能唯一识别稻叶的实际模型。

### 3.1 ε-Fe₂O₃：物相鉴定很强，稻叶归因仍缺证据

Dejoie 等，*Learning from the past: Rare ε-Fe₂O₃ in the ancient black-glazed Jian (Tenmoku) wares*, Scientific Reports 4, 4941（2014），[DOI 10.1038/srep04941](https://doi.org/10.1038/srep04941)。**全文文字已读**，[作者机构入口](https://escholarship.org/uc/item/1d28z84g)、[可读 PDF 镜像](https://scispace.com/pdf/learning-from-the-past-rare-e-fe2o3-in-the-ancient-black-3tr0g5tzuw.pdf)。样本为福建省博物馆提供的建窑兔毫/油滴片，**不是三只传世曜变**。

μ-XRD、Laue、Raman 互证所测油滴表面 ε 相、兔毫 α+ε 相（pp.3–5，Fig.4–5）。SEM/TEM 给出形貌，但不能把 TEM 视野里的每个小颗粒仅凭形貌都指认为 ε。该研究没有稻叶的膜厚或 n/k。小粒径和有序晶体可参与光学效应，是机制讨论，而非原件光谱因果实验。

### 3.2 窑片皱纹与油滴 RCWA：模型值不能冒充测量值

福嶋 2022，*Nano-hybrids of clay minerals with water and organic polymers*, Clay Science 26，39–45，[DOI](https://doi.org/10.11362/jcssjclayscience.MS-22-5)，**相关 p.44 原文段落已读在线 PDF 索引，未取得整份文件**。该页 Fig.11–12 给窑片微结构；最初来源是长江惣吉、福嶋喜章〈宋代建盞の光彩の研究〉，《東洋陶磁》41（2011–2012），35–45，**该初始论文全文未取得**。[学会目录](https://toyotoji.com/journal/971/)

海老塚昇、岡本隆之，〈国宝油滴天目茶碗の光彩に関する一考察〉，《光学》52(9)（2023），393–400，**8页全文文字已读**：[原始 PDF](https://myosj.or.jp/wp-content/themes/osj/download/kogaku/52/09/07.pdf)。对象为大阪市立东洋陶磁美术馆**国宝油滴**的照片，辅以前述窑片结构。模型使用周期起伏和金属背反射层；金属铁是**模拟假设**，不代表原件检出金属 Fe。作者仍要求原物分光验证（p.400）。[理研第一方说明](https://www.riken.jp/press/2023/20231011_1/index.html)

### 3.3 有角谱的出土古片：注意腐蚀成膜

Xuanyu Chen 等，*Angle dependence of Jian bowl color and its coloring mechanism*, J. Eur. Ceram. Soc. 42(2)（2022），693–706，[DOI 10.1016/j.jeurceramsoc.2021.10.057](https://doi.org/10.1016/j.jeurceramsoc.2021.10.057)。**只读出版社摘要及公开正文片段，未取得全文**。[出版社](https://www.sciencedirect.com/science/article/abs/pii/S0955221921007913)

3 件建窑窑址陶片见 Fig.1–3。样品1 Fig.5 在入射 **5°** 时没有明显可见峰，在 **20°** 时有 **419 nm** 峰；所见结论报告二维铁氧化物晶体约 **30–40 nm**、厚约 **15 nm**，具体表征方法/内部图号未从片段获得。作者对弱角依赖提出短程有序结构的相干散射解释（Fig.16 为模型）；另一类强角依赖被联系到埋藏腐蚀产生的薄膜。此文说明“古片有虹彩”还不能证明它全是烧成时形成的虹彩；以上数值不能当作稻叶输入。

## 4. 数字账本：哪些可作为候选输入

### 4.1 表面、晶体与层厚

| 样本/来源 | 数值 | 量的含义与证据 | 页/图；可迁移性 |
|---|---|---|---|
| Dejoie 2014 兔毫片 | 约 **500 μm** | 总釉厚，截面观察；不是干涉膜 | p.2 Fig.1c；古片 |
| 同文油滴片 | 分枝 **>5 μm**；小晶约 **20 nm** | SEM 枝晶；TEM 表下晶体 | pp.2–3 Fig.2b–d、Fig.3；不同结构不能混成同一粒径 |
| 同文相鉴定区域 | 兔毫 ε **<100 nm**；油滴晶体 **>1 μm** | 衍射/显微解释；前者由衍射环推断 | pp.3–5 Fig.4–5；非稻叶 |
| 长江/福嶋古片，福嶋 2022 自述 | 层约 **40 nm**；析出体 **0.1–0.2 μm** | TEM/SAED；局部结构，不是膜厚统计 | p.44 Fig.11；初始2011论文未取得 |
| 同一古片体系 | 周期域 **600 nm、800 nm** | SEM/FFT，正文概称700–800nm | p.44 Fig.12；周期不是粒径/膜厚 |
| 同源结构，海老塚2023转引 | 峰谷约 **100 nm** | 窑片起伏高度的转引 | p.394；非原件新测量 |
| 海老塚2023油滴模型 | 周期 **900 nm**；峰谷 **50–100 nm** | 照片位置拟合/模型设定 | pp.398–400 Fig.8、Table2；**不是实测** |
| 同文数值平均 | 釉厚 **4000–28000 nm**，步长 **10 nm**，共 **2401** 点 | 为消去相干条纹作的模拟平均 | p.395；**不是膜厚分布** |
| Shi 2019 现代实验油滴 | 表面晶层 **100–200 nm**；泡壁约 **1290 nm** | 截面 SEM；两者是不同的层 | p.41930 文字、p.41931 Fig.4d / Fig.4c |
| 孙建兴现代仿品，Feng2023 | 磁铁矿 **10–25 μm**；Al掺杂赤铁矿 **1–3 μm**；相分离球约 **130 nm** | 摘要/公开正文片段报告；枝针状、近圆形、球形分别对应 | 全文未取得，内部图号未知；不能移作古物值 |
| 大平修现代专利 | 斑核层约 **5 μm**；晕层约 **0.1 μm**；点涂直径 **1–5 mm** | 实施例1声称确认，但所见正文未交代测厚方法 | HTML实施例1；Ag/Pb现代路线 |

**没有找到稻叶原件表面厚度的空间分布、直方图、标准差、晶粒取向分布，或可核验的斑核/晕圈尺寸数据集。** 这里没有足够依据给出“服从某种分布”的膜厚。现代文献公开片段中有斑点 **20–50 mm** 的异常量级，未能结合全文图尺核准，故不作为输入，也不擅自改写单位。

### 4.2 黑釉组成及折射率

山崎一雄，〈曜変天目と油滴天目〉，《金沢大学考古学紀要》21（1994），169–172，[原始 PDF](https://kanazawa-u.repo.nii.ac.jp/record/6557/files/AN10407034-21-6.pdf)。**只读到原文搜索索引，直接 PDF 返回429；表格须在取得文件后视觉核对。** p.170 表1的建窑窑址片釉，wt%：

| SiO₂ | Al₂O₃ | 总铁按 Fe₂O₃ 计 | TiO₂ | CaO | MgO | MnO | Na₂O | K₂O | P₂O₅ | SO₃ | 原合计 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 59.78 | 20.56 | 6.18 | 0.65 | 6.95 | 2.16 | 0.03 | 0.90 | 3.02 | 痕量 | 0.60 | 100.83 |

保留原合计，未归一化。**总铁的氧化物当量不是晶相质量分数**，也不确定 Fe²⁺/Fe³⁺比例。古片玻璃相历史折射率 **n≈1.538**（同页；1953官方摘要亦载），测量波长未交代；没有 k。早期纤维晶体 n=1.548 的索引存在小数点 OCR 问题，暂不作为输入。稻叶黑釉本体的实测复 nk 未取得；纯透明玻璃 n≈1.5 是简化先验，不能标成黑釉实测。

### 4.3 已保存的 n(λ)、k(λ)

三份 CSV 各有 **380–780 nm、10 nm 间隔、41点**，由 CC0 数据库原始行转写，只把 μm 换成 nm，无插值、无曲线数字化。来源追溯到 M. R. Querry, *Optical constants*, CRDC-CR-85034（1985）。**原报告未取得，原页码、样品与误差未核验；本次核验的是数据库数据行。** [原报告链接](https://apps.dtic.mil/sti/pdfs/ADA158623.pdf)

| 物相/方向 | 400nm：n,k | 550nm：n,k | 700nm：n,k | 数据文件与原始来源 |
|---|---|---|---|---|
| α-Fe₂O₃ ordinary | 2.756, 1.294 | 3.318, 0.498 | 2.972, 0.031 | [本地CSV](data/querry1985_hematite_o_380-780nm.csv)；[原始YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/Fe2O3/nk/Querry-o.yml) |
| α-Fe₂O₃ extraordinary | 2.475, 1.096 | 2.927, 0.460 | 2.675, 0.075 | [本地CSV](data/querry1985_hematite_e_380-780nm.csv)；[原始YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/Fe2O3/nk/Querry-e.yml) |
| Fe₃O₄ | 2.462, 0.062 | 2.343, 0.105 | 2.355, 0.124 | [本地CSV](data/querry1985_magnetite_380-780nm.csv)；[原始YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/master/database/data/main/Fe3O4/nk/Querry.yml) |

这是**块体矿物参照，不是 ε 相、不是混合釉的有效常数、更不是稻叶检测**。赤铁矿有各向异性，o/e不能互换，也不能简单平均后冒充已测的随机晶体层。已另生成 [pbrt 格式的 eta/k 光谱文件](data/pbrt_optics/README.md)，仅作候选材料计算，不能证明原件材料身份。详细转写说明见 [optical_data_README.md](data/optical_data_README.md)。

独立实测线索：Chen–Cahan 1981，JOSA 71，932–934，[DOI](https://doi.org/10.1364/JOSA.71.000932)，**只看摘要**，报告单晶/多晶赤铁矿 **1.6–4.8 eV** 光谱椭偏；未获得谱表。

**ε-Fe₂O₃：本轮未取得可放心导入的可见光复 nk 表。** Jussila 等 [DOI 10.1002/adem.202201262](https://doi.org/10.1002/adem.202201262)，[全文PDF](https://d-nb.info/1273105281/34)，p.6 报告 **240–1700 nm** 椭偏用于现代 ALD 膜厚拟合，但未给所需表；Tanskanen 等 2017，[全文PDF](https://acris.aalto.fi/ws/portalfiles/portal/13557714/Tanskanen_et_al_2017_Simple_ALD_process.pdf)，[DOI](https://doi.org/10.1063/1.4983038)，也未取得可用谱表。不能用 α 相数据改名代替。Al掺杂赤铁矿与多相表层也未取得匹配的实测谱表。

一个应排除的线索：[Physchem 2025,5,33](https://www.mdpi.com/2673-7167/5/3/33)，只读到全文索引段落 §5.1–5.5。其报告 R=0.05–0.37，却用 n=(1+√R)/(1−√R) 得 n=1.05–1.45；代入该式实际约为1.576–4.105，存在内部不一致。其 k 亦需复核量纲，因此未转写为可靠数据。[WO2017126618A1](https://patents.google.com/patent/WO2017126618A1/ja) 表1的 400/450/500nm → 1531/774/427 dm³·mol⁻¹·cm⁻¹ 是粒子分散液摩尔消光系数，**不是实体材料无量纲 k**。

## 5. 现代仿品与实验：分别记录，分别使用

- **孙建兴**：Feng 等，*Phase-separated Tenmoku “Blue” glaze: Microstructure and coloring mechanism*, J. Eur. Ceram. Soc.43（2023），6581–6589，[DOI](https://doi.org/10.1016/j.jeurceramsoc.2023.05.051)。只读摘要和公开片段。作者提出约130nm相分离球的相干散射与铁离子着色协同；不是证明古物有同一结构。公开片段486nm的属性尚不能确认是实测峰还是模型值，故未列为光谱约束。
- **林恭务/林恭助**：未查到“林恭务”对应陶艺家；很可能指林恭助，但不能认定同名。[茨城县陶艺美术馆](https://www.reserch.tougei.museum.ibk.ed.jp/viewer/archive.html?g=194&id=667)使用林恭助。水上2013 p.215将其作品与大平修 Ag/Pb 低温装饰路线联系。[JP2005082438A](https://patents.google.com/patent/JP2005082438A/ja)全文HTML已读，发明人为**大平修**，不能写成林恭助署名专利。实施例的层厚见上表；一般“扩散蒸着形成小于1μm无机膜”是作者推测。该路线不证明三国宝含铅银层。
- **长江惣吉**：大阪市立东洋陶磁美术馆2020《現代の天目―伝統と創造》[数字图录](https://www.moco.or.jp/wp/wp-content/uploads/2020/09/%E7%89%B9%E9%9B%86%E5%B1%95%E3%80%8C%E7%8F%BE%E4%BB%A3%E3%81%AE%E5%A4%A9%E7%9B%AE%E2%80%95%E4%BC%9D%E7%B5%B1%E3%81%A8%E5%89%B5%E9%80%A0%E3%80%8D%E3%83%87%E3%82%B8%E3%82%BF%E3%83%AB%E5%9B%B3%E9%8C%B2.pdf)介绍其2006年作品及萤石相关酸性气体在冷却阶段作用的工艺解释。它是现代复现路线；不等于已测得原件 F/Cl。其古片电镜合作也不等于在三国宝上取截面。
- **Shi 等2019实验油滴**：RSC Advances9，41927–41933，[DOI](https://doi.org/10.1039/C9RA06870H)，[官方PDF](https://pubs.rsc.org/en/content/articlepdf/2019/ra/c9ra06870h)，[本轮已读全文的原PDF镜像](https://pdfs.semanticscholar.org/5568/de904a0af25366573b902d1c52927fc555ac.pdf)。XRD Fig.3b 有赤铁矿和磁铁矿。作者并论散射、衍射、干涉，没有角谱分离其贡献。文中 n赤铁矿2.94–3.22、磁铁矿2.42、玻璃1.5–1.8 是引用/泛用值，无波长/k/椭偏方法；**不能算实测全谱常数**。小于100nm是 Rayleigh 讨论的条件，不是粒径统计。Table2 含16.42%烧失，不能冒充烧后玻璃配比；SEM前以1vol%HF处理30s，解释表面形貌时应注意。
- **Li Xingyun 等2016实验仿品**：Ceramics International42，15269–15273，[DOI](https://doi.org/10.1016/j.ceramint.2016.06.027)，[出版社](https://www.sciencedirect.com/science/article/pii/S0272884216308598)。只读摘要/引言片段；约1280°C氧化烧成、赤铁矿析晶，不是稻叶原件研究；未取得额外可用尺寸或 nk。

## 6. 进入 pbrt-v4 的方式与验证条件

以下是本报告的建模建议，**不是古物测量结论**。

1. **分开斑核、晕、黑地与宏观釉面。** 斑核形状、聚集分布应来自同一视角的原件几何标定图，不能用随机圆点宣称一比一。先保持每个区域的相结构、粗糙度与光学参数可独立更换。
2. **薄膜必须保留相位。** 单膜振幅可写 r=(r₀₁+r₁₂exp(2iβ))/(1+r₀₁r₁₂exp(2iβ))，β=2π ñ d cosθₜ/λ；分别求s/p后平均强度。吸收介质要统一复数符号与衰减分支；采用exp(−iωt)时以 ñ=n+ik、k≥0表示衰减。吸收系数 α=4πk/λ，k不是α。膜厚分布未知时，做敏感性试验应标成假设；空间不相干区域平均的是强度 ∫R(d)p(d)dd，不是先平均复振幅。
3. **衍射候选应有独立 BSDF。** 使用测得或假定的表面PSD、周期域和取向，离线RCWA等计算后制成波长–入射–出射表，保证能量守恒、互易性。数百纳米的结构不应依靠普通几何光线跟踪网格自动产生结构色。体散射路线还需尺寸分布、相含量和结构因子。
4. **不要把 pbrt 的涂层材料直接当干涉膜。** 标准 coateddiffuse/coatedconductor 的 layered 传输以辐亮度与随机游走计算，不保留电磁相位；thindielectric也不是一般色散薄膜干涉求解器。LayeredBxDF 内部以消光归一化设置厚度，不能直接把40nm当无量纲 thickness 填入。应增加波动光学 Fresnel/BSDF 或离线表，再接 pbrt 光谱与光传输。[pbrt 书 §14.3.2](https://pbr-book.org/4ed/Light_Transport_II_Volume_Rendering/Scattering_from_Layered_Materials)、[v4材料输入文档](https://pbrt.org/fileformat-v4)
5. **用相同场景比较候选机制。** 固定器形、光源SPD、光源面积和位置、相机响应/曝光，对斑核、晕、黑地分别比较绝对光谱及角度峰位。单张未知白平衡照片只适合外观检查，不能唯一反演 n、k、d。

建议的可证伪判据：若离镜面角位置与二维结构方向相关，检验衍射模型；若峰位随膜内角度系统移动并可由同一 n/k/d 联合解释，检验膜模型；若弱角依赖且峰位随短程相关长度而变化，检验相关散射。任一模型若只能靠逐张改膜厚/光源才能吻合，应视为证据不足，不能宣称成功复刻。

**继续实现前最值钱的数据**是稻叶原件同一位置的校准多角度反射谱、偏振及对应照片；其次为藤田2023全文、杭州专著 pp.89–172、长江/福嶋2011全文与原始电镜。缺少这些时可做物理合理的候选视觉复现，不能认证原件成因或一比一参数。

## 7. 器形与斑纹几何

| 对象 | 高 / 口径 / 圈足径（cm） | 重量 | 来源及限制 |
|---|---|---|---|
| 稻叶 | **7.2 / 12.2 / 3.8** | **276g** | 故宫2018 p.23表1；三尺寸也见静嘉堂2023展品目录第24项 |
| 藤田 | **6.8 / 12.3 / 3.6** | **250g** | 同表；圈足径与部分网络条目有差别，建模须核对馆藏测量 |
| 龙光院 | **6.4 / 12.2 / 3.8** | 未公开 | 同表；文化厅数据库另记**6.6 / 12.1 / 3.8**，不能平均，待查测量定义 |
| 杭州2009古越会馆 | **6.8 / 12.5 / 4.2** | **208g** | 同表；不是2017残器 |
| 杭州2017述郑斋 | **7.0 / 12.1（估） / 3.8** | **140g** | 同表；残器与复原估计不可作完整器精确约束 |

[故宫文章原文](https://theme.npm.edu.tw/Academic/ChineseArtDownload.ashx?bid=4169&eid=174)、[静嘉堂2023展品表](https://www.seikado.or.jp/file/wp-content/themes/seikado/images/exhibition/230811/exhibition_list230811.pdf)、[龙光院文化厅条目](https://online.bunka.go.jp/db/heritages/detail/125707)。故宫文 p.24 所说约 **1mm 或更薄**是杭州述郑斋断面总釉层的宏观描述，圈足附近有积釉；不能等同于百纳米干涉膜。

未取得稻叶内外完整剖面、口沿壁厚、足底三维数据与全斑点坐标。已找到正面/内面及足底来源，但本轮不能解码图片，因而**没有宣称能够数清斑纹、没有给出虚构斑点数/中心半径/晕宽统计**。达到一比一还需要图像透视校正与轮廓/纹理配准。

## 8. 照片清单：稻叶优先

下面尺寸是文件页元数据，未核实者明确列“未知”。角度只按来源的标题/图注填写，未用图搜自动描述冒充视觉检查。每个实际候选文件的来源、直链、授权和状态均在 [sources.csv](sources.csv)，[images/index.md](images/index.md)提供筛选索引。**表中均为远程候选，尚未下载。**

| 来源与候选图 | 分辨率 | 角度/照明 | 授权与用途 |
|---|---|---|---|
| [静嘉堂馆方馆藏页](https://www.seikado.or.jp/english/english-collection/) collection_img03.png | 未知 | 未视觉核验；光源未知 | 馆方图，未见开放许可；首要外观参照 |
| [三菱2025馆长采访](https://www.mitsubishi.com/ja/profile/csr/mpac/monthly/m_art/2025/03/1.html) img-1-1 / img-1-2 | 未知 | 图文标“见込”内面及全器；是否严格正俯视未知 | 未见单图开放许可；拟用于内面斑点/器形 |
| [日本博官方](https://japanculturalexpo.ntj.jac.go.jp/en/hotspots/1083/) img1.jpg | 未知 | 角度与光未知 | 官方宣传图，未见单图开放许可 |
| [DNP档案X008](https://images.dnpartcom.jp/ia/workDetail?id=SAMB1031X008) | 未公开像素；目录原文件1.4MB | 标题“横”，侧面；光未知 | （公财）静嘉堂／DNPartcom；商业图像许可，未购买 |
| [DNP X105](https://images.dnpartcom.jp/ia/workDetail?id=SAMB1031X105) / [X37](https://images.dnpartcom.jp/ia/workDetail?id=SAMB1031X37) | 未公开像素；目录11.0 /14.3MB | 标题“高台”，圈足；光未知 | 同上；文件大小不是分辨率 |
| DNP [X003](https://images.dnpartcom.jp/ia/workDetail?id=SAMB1031X003)、[X004](https://images.dnpartcom.jp/ia/workDetail?id=SAMB1031X004) | 未知；10.5 /9.1MB | 不同全器档案，具体视角待看 | 同上 |
| DNP [X005](https://images.dnpartcom.jp/ia/workDetail?id=SAMB1031X005)、[X006](https://images.dnpartcom.jp/ia/workDetail?id=SAMB1031X006)、[X007](https://images.dnpartcom.jp/ia/workDetail?id=SAMB1031X007) | 未知；10.5 /10.7 /10.4MB | 标题“部分1/2/3”；位置待视觉核验 | 同上；可查晶斑/晕的局部形状，不能据目录定比例 |
| [Commons 1937旧图版](https://commons.wikimedia.org/wiki/File:Yohen_Tenmoku_Tea_Bowl(Seikado).jpg) | **2195×3941** | 多图版；具体角度待核验，旧印刷照明未知 | Commons标PD-Japan-oldphoto及美国PD；未独立法律核验；用于形态 |
| [Commons 1955图01](https://commons.wikimedia.org/wiki/File:Y%C5%8Dhen_Tenmoku_(Seikad%C5%8D_Bunko_Art_Museum)_01.jpg) | **1652×1049** | 未视觉核验 | 同上；林屋晴三《中国的陶磁》旧版来源 |
| [Commons 1955图02](https://commons.wikimedia.org/wiki/File:Y%C5%8Dhen_Tenmoku_(Seikad%C5%8D_Bunko_Art_Museum)_02.jpg) | **1652×1366** | 未视觉核验 | 同上；不可用于绝对色标定 |
| [Commons 1955全图](https://commons.wikimedia.org/wiki/File:Y%C5%8Dhen_Tenmoku_(Seikad%C5%8D_Bunko_Art_Museum).jpg) | **1388×1429** | 未视觉核验 | 同上；《世界陶磁全集》10 来源 |

DNP 的目录描述补上了圈足/侧面需求，但本轮**没有取得可用于纹理提取的许可原图**。其公开预览与付费原图必须区分；清单只放已定位的预览直链，不假造原图下载地址。

### 另外两碗与杭州

| 对象/来源 | 分辨率与角度 | 授权/问题 |
|---|---|---|
| [藤田 Key-museo 实拍](https://commons.wikimedia.org/wiki/File:Yohentenmoku_2.JPG) | **1375×1422**；角度未核验 | **CC BY-SA 4.0，Key-museo**；EXIF闪光未触发、自动白平衡；不能据此确定光源SPD |
| [藤田1954旧图](https://commons.wikimedia.org/wiki/File:YOUHEN_TENMOKU_bowl_FUJITA.JPG) | **1130×1139** | Commons旧照片PD标记；色彩校准不足 |
| [藤田另一个Commons版本](https://commons.wikimedia.org/wiki/File:Temmoku_tea_bowl_Fujita_Bijutsukan.jpg) | **1413×2464** | 文件历史明确有人工上色/提亮；**排除颜色标定** |
| [文化厅藤田展览图1、2](https://www.bunka.go.jp/prmagazine/rensai/bunkazai/bunkazai_059.html) | 两张像素/视角未核验 | 图注藤田美术馆，未见开放许可 |
| [MIHO龙光院2019官方页](https://www.miho.jp/exhibition/daitokuji-ryokoin/) | 海报与6页折页；像素未知 | MIHO权利保留，未见开放许可；海报不是纯器物照片 |
| [美术手帖龙光院图](https://bijutsutecho.com/magazine/news/exhibition/19335/pictures/2) | 未核验 | 图注明确龙光院；搜索图像会混入藤田，不能仅按缩略图归属 |
| [Internet Museum龙光院报道](https://www.museum.or.jp/report/1167)、[新闻](https://www.museum.or.jp/news/4330) | 各一张已定位直链；像素/视角未知 | Internet Museum权利保留，未见开放许可 |
| [故宫2018文章](https://theme.npm.edu.tw/Academic/ChineseArtDownload.ashx?bid=4169&eid=174) | p.23图1：杭州2009；p.25图3：藤田；p.25图4：龙光院；p.26图5：杭州2017 | 嵌在PDF内，未提取独立文件；杭州两图与藤田为小林仁摄影；龙光院转自2000图录p.250图版93 |

### 可核实的展场照明信息

[KOKUYO THEORiA 静嘉堂展柜报道](https://www.e-theoria.com/museum/047_011.html)描述丸之内展柜：柔和顶面一般光，加照碗内的顶部中心聚光、照外壁的地面聚光、照口沿的两盏顶灯。无SPD、灯具坐标、照度或光源面积数据；只能提供布光关系，不能复建定量照明。[展柜照片](https://www.e-theoria.com/museum/img/047/01_01_photo.jpg)已入清单。

[静嘉堂2019展览页](https://www.seikado.or.jp/exhibition/2019002.html)提到自然光下晨昼夕变化的展示；不能把它当所有馆藏照片的光照。[CCS 2017京都龙光院展照明说明](https://www.ccs-inc.co.jp/museum/results/others/kyoto.pdf)为自然光型LED方案，不等于2019 MIHO展或当前照明，未获得实测SPD。2025静嘉堂足底镜面展示也见[官方展览记录](https://www.nact.jp/artcommons/user/detail/79259)，有助找足底视频。

## 9. 视频：可追踪候选，未虚构时间点

本轮未能播放或下载视频，故所有“关键时间点”均为**待核验**。目前也不能确认哪段真正连续记录了同一斑纹随视角变色；切镜/曝光变化不能作为角度测色证据。[video/index.md](video/index.md)有优先级及去重说明。

| 优先级 | 对象与链接 | 已核实的来源信息 | 需看哪些片段 |
|---|---|---|---|
| 1 | [稻叶2025 Internet Museum](https://www.youtube.com/watch?v=U_Yl9t5BrHg) | 2025-04-04取材，04-06发布；“黒の奇跡・曜変天目の秘密”；含足底展示的报道说明 | 内面连续移动镜头、外壁与镜面圈足；时间点/分辨率未知 |
| 2 | [藤田2015 Internet Museum](https://www.youtube.com/watch?v=8gHSfTcDdkU) | [原报道](https://www.museum.or.jp/report/689)，2015-08-04取材 | 同一斑纹相对高光移动；时间点未知 |
| 3 | [龙光院2019 Internet Museum](https://www.youtube.com/watch?v=3q2sKOBqBlQ) | 2019-03-20取材，04-01上传 | 内面与侧面连续镜头；时间点未知 |
| 去重 | [龙光院2021上传版](https://www.youtube.com/watch?v=dTkFmgZtOZo) | [2019报道页](https://www.museum.or.jp/report/1167)嵌入；可能相同取材 | 先核对是否重复，再择清晰版本 |
| 节目线索 | [TV东京《美の巨人たち》2017官方页](https://www.tv-tokyo.co.jp/plus/lifestyle/entry/2017/014934.html) | 2017-10-21节目；[静嘉堂预告](https://www.seikado.or.jp/info20171010_02.html)明确放大、自然光拍摄 | 未取得可播放节目文件；图文页面不是视频直链 |
| 8K线索 | NHK《国宝 曜変天目茶碗》2019 | [Advanced Imaging Society官方获奖记录](https://advancedimagingsociety.jp/award/award2019.html)；[国立文化财机构2018年报p.192](https://www.nich.go.jp/wp-content/uploads/2020/01/nenpo2018_2-1-4.pdf)记藤田8K拍摄 | 未定位公开可下载8K源，不能承诺有8K素材 |
| 节目线索 | NHK ETV《曜変～陶工・魔性の輝きに挑む～》 | KAKEN原始项目报告记录2016-06-11播出 | 现代复现与原件检测分别核对；无时间点 |
| 补充线索 | [林恭助电视纪录片馆藏](https://www.bpcj.or.jp/program/detail/204859/) | 放送节目中心正式节目记录 | 页面无已核验在线播放 |

另定位[稻叶展览视频 QOMK9UU8L9g](https://www.youtube.com/watch?v=QOMK9UU8L9g)，发布者与画质未充分核验，低优先级。NHK《曜変天目ディスコ》为动画，不作为真实光学参照。未找到可核验杭州残器连续变色视频。

## 10. 交付与仍受阻的部分

已保存：本报告、[sources.csv](sources.csv)、[结构参数CSV](data/mechanism_parameters.csv)、三份41点矿物 n/k CSV、对应pbrt光谱文件和各目录索引。背景核查笔记保留在 notes/，用于追踪未进入主表的疑点。

未完成：实际PDF/照片/视频下载，图像像素与角度的全面视觉核查、视频时间点；稻叶原件缺失的物相/膜厚/全谱数据也不能由这次检索补造。[下载脚本](tools/fetch_sources.py)默认只预览，显式指定 --download 后才下载已列出的静态公开文件；它不购买DNP原图、不处理登录和YouTube。尚未完成在线下载验证。

最先补齐藤田2023全文、杭州专著及稻叶校准角谱，会实质改变模型选择。当前合理的交付结论是“已整理有出处的候选物理模型与参照来源”，而非“已获得稻叶天目的全部真实渲染参数”。

本地交付核查：sources.csv共107条；三份n/k表各41点，六份SPD与CSV逐值一致；报告中的本地链接均存在，下载状态与文件存在情况一致。下载脚本完成了离线签名拦截、大小上限、失败字节记录、防覆盖及清理检查，未完成在线验证。
