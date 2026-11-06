# 钧窑天蓝／月白釉紫斑：45 mm 视野球腹转台的实物与光学依据

调研日期：2026-11-02。交付以可追溯实物、原始论文与可复用计算方法为主；未制作或验证渲染材质。**推荐以 Cleveland 1957.36 宋／金球腹罐作为形状及紫斑主参照，以刘家门 Classic Jun 的纳米结构研究约束蓝釉；蚯蚓纹另按明确可见的器物照片选用。**这避免把明初编号钧的密集纹貌当成所有宋金元日用钧的共同属性。[Cleveland 藏品](https://www.clevelandart.org/art/1957.36)、[Hou 等 2018](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[British Museum 对编号钧的断代](https://www.britishmuseum.org/collection/term/x112232)。

## 0. 阅读方式与最重要的边界

证据标签：**【实测】**论文对注明样本的仪器／图像测量；**【文献】**作者的机理解释、馆方目录或他文转述；**【计算】**成分模型、光学模型或本报告换算；**【观察】**本次看照片的描述；**【建议】**待验证的渲染取舍。照片像素与本地文件检查是本次实读，不是文物材料测量。每个数值均保留适用样本，不能拼成一件“标准钧瓷”。

- **不是只有一种蓝色散射机制。**分相尺度、相含量、铁／钛吸收、釉厚和底层共同影响蓝色、明度与乳浊；紫斑也不能简化成表面紫色油漆。[Hou 2018，讨论及图10](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)。
- **纳米“蠕虫状分相”与毫米“蚯蚓走泥纹”是两种尺度的东西。**前者是玻璃相结构；后者是肉眼可辨的釉内带状纹，不能直接共用一张纹理或同一个形成模型。[Hou 2018，图3–7](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[李媛等 2013，图1–6](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)。
- **样本年代有边界。**下文钧台 JS-29／JS-30 的定量蚯蚓纹数据，原论文沿用“宋官钧”；BM 现将 official／numbered Jun 定为明初约1368–1435。本报告将其列为机制、尺度对照，**不标成已确证宋金元民钧实测**。宋归属的德基瓶另依馆方目录，未独立考古复核。[故宫2013](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)、[BM](https://www.britishmuseum.org/collection/term/x112232)、[德基长颈瓶](https://www.dejiart.com/en/digital_library/junyaotianlanyouzicaizhangjingping/)。
- **没有从 RGB 照片反演光谱、泡径或粗糙度。**本次馆藏照未附受控照明／色卡／局部物理标尺，论文谱与照片也通常不是同一件器物；因此只能形成“文献约束的外观模型”，不能宣称某件器物光学参数已被唯一确定。[照片逐图来源](../../ref/jun/img/index.md)、[Hou 2018 的测量样本和方法](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)。

## 1. 实物、高清照片与局部细节

### 1.1 已下载的核心器物

下表尺寸单位为 cm；断代按保管机构，不把“北宋或金”改写成确定北宋。**每张图的直链、像素、版权、SHA-256、裁切关系见 [img/index.md](../../ref/jun/img/index.md) 及 [manifest.json](../../ref/jun/img/manifest.json)**。同罐盖与罐身、同碗多角度不重复计为独立器物。

| 器物／藏地／编号 | 馆方断代；尺寸 | 本地图像与用途 | 授权、原始出处 |
|---|---|---|---|
| 带盖罐；美国克利夫兰艺术博物馆；1957.36 | 12世纪，北宋或金；高9.5，径12.1 | [6603×5913 TIFF](../../ref/jun/img/cma_1957_36_jar_cover_full.tif)；另3400px JPG、罐身4角度与盖图。**球腹转台首选** | CC0；[整器](https://www.clevelandart.org/art/1957.36)、[罐身](https://www.clevelandart.org/art/1957.36.a)、[API](https://openaccess-api.clevelandart.org/api/artworks/?accession_number=1957.36) |
| 天蓝紫斑碗；纽约大都会；50.145.308／网页52663 | 金，12–13世纪；高9.8，径22.2 | `met_52663_01…06.jpg`，各4000×3002；外壁四向、内底、底足，检查斑边和不同位置的釉色 | Public Domain／CC0；[目录](https://www.metmuseum.org/art/collection/search/52663)、[开放政策](https://www.metmuseum.org/hubs/open-access) |
| 天蓝紫斑碗；大都会；50.145.309／50233 | 金，12–13世纪；高9.8，口22.2，足6 | `met_50233_01…06.jpg`，各4000×3002；长条流动紫斑、多角度 | Public Domain／CC0；[目录](https://www.metmuseum.org/art/collection/search/50233)、[API](https://collectionapi.metmuseum.org/public/collection/v1/objects/50233) |
| 天蓝釉紫红斑碗；北京故宫；新00082245 | 金；高8.5，口14，足4.4 | `dpm_227947_60128…60130.jpg`，1024×683，侧／俯／底。是目录参照，非高清微距 | ©故宫，版权保留；[目录](https://www.dpm.org.cn/collection/ceramic/227947.html)、[使用规定](https://www.dpm.org.cn/bottom/privacy/236341.html) |
| 天蓝釉紫红斑钵；北京故宫；网页227986 | 元；高16.5，口16.8，足8.8 | `dpm_227986_60156…60158.jpg`，1024×683／874／805。深弧球腹、淡紫红斑 | ©故宫，版权保留；[目录](https://www.dpm.org.cn/collection/ceramic/227986.html)、[使用规定](https://www.dpm.org.cn/bottom/privacy/236341.html) |
| 天青釉紫彩长颈瓶；南京德基艺术博物馆 | 馆方定北宋；高29.3，口4.7，腹14，足6.5 | [4136²整器图](../../ref/jun/img/deji_longneck_vase.jpg)。**馆方明确说肩部有蚯蚓走泥纹**，可作有纹历史瓶的形貌参照 | ©德基，未见开放许可；[目录](https://www.dejiart.com/en/digital_library/junyaotianlanyouzicaizhangjingping/) |
| 月白釉紫彩鹅颈瓶；德基 | 馆方定北宋；高26，口5.8，腹12.3，足6.8 | [3358²](../../ref/jun/img/deji_gooseneck_vase.jpg)，月白—蓝—紫交混。英文标题sky-blue，与中文原图文件名“月白”不同，保留此差异 | ©德基，未见开放许可；[目录](https://www.dejiart.com/en/digital_library/junyaotianlanyouzicaiejingping/) |
| 月白釉紫彩直口盘；德基 | 馆方定北宋；高5.1，口23.3，足13.5 | [6200²](../../ref/jun/img/deji_straightrim_dish.jpg)，紫斑轮廓与灰蓝过渡；英文／中文色名同样有差异 | ©德基，未见开放许可；[目录](https://www.dejiart.com/en/digital_library/junyaotianlanyouzicaizhikoupan/) |
| Vase；华盛顿 Smithsonian 亚洲艺术国家博物馆／Freer；F1950.8 | 北宋或金，12世纪；高×宽28×12.8 | [1527×2240](../../ref/jun/img/freer_F1950_8_vase.jpg)，厚灰蓝釉紫斑梨腹瓶 | **Usage Conditions Apply，非已确认CC0**；[目录](https://asia-archive.si.edu/object/F1950.8/)、[图像manifest](https://ids.si.edu/ids/manifest/FS-6217_03) |
| 天蓝釉紫斑钵／Bowl；台北故宫；精选04009328 | 金至元；高16.4，口16.9，足8.1 | [2821×2127官方图](../../ref/jun/img/npm_04009328_17011551.png)。球腹、灰蓝细斑、紫红斑；第二视角未下载完整 | 精选页标版权保留，未将其他Open Data图区许可自动套用；[目录](https://theme.npm.edu.tw/selection/Article.aspx?lang=2&sNo=04009328) |

另保存大都会元代蓝釉碗26.292.27（网页52651）两图，2000×1500彩照与2000×1284旧黑白照，尺寸高10.2、径24.1。它只作蓝釉／器形对照，不列为已明确紫斑的主参照。[馆方目录](https://www.metmuseum.org/art/collection/search/52651)。

### 1.2 哪些图真的能支持微距

**【观察】**Cleveland 原始TIFF可看到紫斑边缘呈细碎、羽化、交错过渡，而非整齐矢量边；斑内与蓝底都有细小亮暗结构。下面三个是**原图未缩放裁切**，没有补纹理；它们不是重新拍摄的显微照，像素细点不能直接鉴定为气泡、棕眼或石英。[原器及高清图出处](https://www.clevelandart.org/art/1957.36)、[裁切框记录](../../ref/jun/img/core-manifest.json)。

| 局部文件 | 像素、原图坐标(x0,y0,x1,y1) | 参照意义 |
|---|---|---|
| [紫斑边缘](../../ref/jun/img/detail_cma1957_36_purple_edge.png) | 1300²；1950,2400,3250,3700 | 斑边交混、亮点、细纹与粗细层级 |
| [紫斑内条带](../../ref/jun/img/detail_cma1957_36_purple_streaks.png) | 1300²；3250,2300,4550,3600 | 紫斑内部不均匀性、流动走向 |
| [蓝釉局部](../../ref/jun/img/detail_cma1957_36_blue_texture.png) | 1300×850；2500,3450,3800,4300 | 蓝地细颗粒外观和照片可辨的表面起伏 |

**【计算】**原图罐身最大投影直径粗估约3500px，对应馆方12.1cm直径，因此1300px裁切的投影视宽约45mm；这是选图尺度估计，曲率、透视、局部法线未校准，**不能据此发表精确孔径或纹宽测量**。[器物尺寸](https://www.clevelandart.org/art/1957.36)、[原图与裁切](../../ref/jun/img/core-manifest.json)。

真正的显微／截面图已另存：

| 图像组 | 内容、尺度、限制 | 原始出处 |
|---|---|---|
| `dpm2013_fig3_*surface_20x.jpeg` | 蚯蚓纹表面OM×20；蓝纹周边乳浊物、紫红纹波状边缘 | [李媛2013，图3，印刷p230](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |
| `dpm2013_fig4_*section_50x.jpeg` | OM×50截面，釉层与内部气泡；纹区深度不同 | [同文图4，p230](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |
| `dpm2013_fig6_*BSE.jpeg` | 针状晶体与残余石英，SEM-BSE×3000／×300 | [同文图6，p232](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |
| [Hou图5](../../ref/jun/img/hou2018-fig5-classic-sem-distributions.jpeg) | **Classic Jun**蓝／乳浊微区、500nm标尺SEM和粒径直方图 | [Hou2018，图5](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |
| [Hou图7](../../ref/jun/img/hou2018-fig7-tem.jpeg)、[图9](../../ref/jun/img/hou2018-fig9-copper-nanoparticles.jpeg) | 两玻璃相TEM，及红／紫区铜纳米粒子 | [Hou2018，图7、9](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |

故宫2013内嵌原图仅约229×171至281×258px；另存带图注的3倍页区PNG便于阅读，但栅格化不增加原始细节。**尚未获得同一件宋金元器物、带标尺且受控照明的高清棕眼／开口泡微距组。**目前可用的是博物馆高清裁切、论文表面显微和截面证据，不把它们伪装成一套同器数据。[显微图清单](worm-model-notes.md)、[照片清单](../../ref/jun/img/index.md)。

### 1.3 已定位而未获得图像的实物

- 台北故宫故瓷006543：金元12–13世纪天青紫斑圆盘，高2.9、口18.8、足12.2。该目录低阶图标CC0、中阶图标CC BY 4.0；本地TLS失败，**未下载**，不能与已下载的04009328钵混淆。[官方目录及逐图授权](https://digitalarchive.npm.gov.tw/Collection/Detail/1268?dep=U)。
- BM PDF.93：金，1115–1234，紫斑盘，高2.8、口18.5、底11.1；HTTP403未得图。BM PDF.45小杯另提供“转动时泡状高光移动”的馆方观察，不等于真实内部气泡在移动。[PDF.93](https://www.britishmuseum.org/collection/object/A_PDF-93)、[PDF.45](https://www.britishmuseum.org/collection/object/A_PDF-45)。
- Museum Wales NMW A(L)1358：12世纪球腹紫斑罐，高12.7、径12.6；官网说明无可提供图像。[目录](https://museum.wales/collections/online/object/fe57b247-ecf0-3dde-bef3-f29a1457c0c2?field0=with_images&page=9&value0=on&view=grid)。Durham DUROM.1969.89元代月白紫斑双系罐已定位，但无本次可核对的尺寸／高清照片。[官方展厅指南](https://www.dur.ac.uk/things-to-do/media/things-to-do/oriental-museum/visit/access/downloadable-gallery-guides-/MacDonald-Gallery-of-China---Large-Print-Guide.pdf)。

## 2. 釉的结构与光学数值

主要原始研究为[Hou等2018（JECS38:4290–4302）](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[Yuan等2022（JECS42:3015–3022）](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016)、[Wang等2024（陶瓷学报45(2):281–289）](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005)。以下保留样本、定义和测法；论文及图像均已下载。

### 2.1 天蓝、月白与釉深度：先把“分相”与“气泡”分开

**实测/文献解释。** Hou 的古样有两类玻璃纳米结构：富钙（同时富 Mg、Fe、Ti、P）球形滴处于富硅（富 Na、K）连续基质中；另一类为虫形及互连纳米结构，组成界面更弥散。经典钧样更偏球滴，官钧样更偏互连；作者将前者解释为成核长大、后者解释为 spinodal decomposition。这里的“虫形纳米结构”不是肉眼可见的蚯蚓走泥纹。[Hou 2018, Results/Discussion, Figs. 3–7](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)

**实测/机制。** 液滴与基质的折射率差引起散射，Fe²⁺ 的宽红外吸收带（约 1100 nm，向可见红端延伸）带来蓝底色；局部富钙区液滴更多、更大、Fe 更氧化，呈白黄乳浊云，贫钙区更透明、更深蓝。应保留“吸收 + 散射 + 空间异质”，不能只用 λ⁻⁴ 蓝散射解释全部颜色。[Hou 2018, Fig. 10](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)；[Yuan 2022, Introduction/Discussion](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016)

| 量 | 数值、测法与适用对象 | 证据类型/出处 |
|---|---|---|
| 富硅基质组成（wt% 氧化物） | JS4：Na₂O 1.4, MgO 0.9, Al₂O₃ 9.3, SiO₂ 74.4, P₂O₅ 0.2, K₂O 3.9, CaO 8.9, TiO₂ 0.2, FeO 0.8 | **实测（半定量 TEM-EDS）**；[Hou Table I](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |
| 富钙液滴组成（wt%） | 同样 JS4：Na₂O 0.2, MgO 3.7, Al₂O₃ 8.2, SiO₂ 59.7, P₂O₅ 1.1, K₂O 1.0, CaO 23.1, TiO₂ 0.5, FeO 2.4；Na/K 的测量有约 30% 波动，作者明确限制 | **实测（半定量）**；[Hou Table I / Results](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |
| 基质/液滴折射率 | **1.503 / 1.545**；Δn=**0.042**（本报告相减）；由化学组成套 Priven–Mazurin 2003 模型得出，无实测色散 n(λ)/k(λ) | **模型**，不是折射仪测值；[Hou Table I](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |
| 富钙纳米相体积分数 | 随总 CaO 增高，最高约 **25 ± 2%**；ImageJ 对每色区至少两幅 FIB-SEM 图作面积分数，按立体学面积=体积分数；Fig. 6D 的连线仅引导视线；原文未定义±2为SD、SE或置信区间 | **图像定量实测估计**；[Hou methods/Results/Fig. 6D](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |
| 液滴尺寸分布 | Figs. 3、5 提供数目直方图，横轴直径 D，图内范围约 **0–200 nm**；没有数值表、D10/D50/D90 或标准分布拟合。不同位置分布不同，不能称“单一均匀粒径” | **实测图**，推荐直接参照所存 Fig. 5；[Hou Figs. 3/5](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |
| 适合渲染的简化起点 | 同一研究组后来概述：富钙乳白区 **120 nm / 25 vol%**，贫钙蓝区 **70 nm / <20 vol%**；这是对 Hou/Yuan 古钧数据的文献归纳，不是 2024 长沙新实测，也非所有液滴的上下限 | **文献转引**；[Yuan 2024 §4 钧釉比较](https://doi.org/10.1111/jace.20025) |
| 独立宋代标本 | 古天蓝样的分相结构约 **96 nm**（STEM-HAADF），含互连和离散滴。由组成算 n 基相=**1.522**、微相=**1.569**。作者假设 φ=90% 算 n_eff=1.564；**90% 是假设，不能与 Hou 实测 25% 混作证据** | **实测尺寸 + 模型折射率**；[Shi 2018 Figs. 3–4, Eqs. 1–4](https://doi.org/10.1016/j.jeurceramsoc.2017.10.036) |
| 元代另一体系 | 燕家梁 YJL-1 组液滴 **50–150 nm**，多数 <100 nm；主要组被作者归源河北定窑而非河南，分相形态不同 | **实测**；[Shi 2025 Fig. 12 / Microstructural analyses](https://doi.org/10.1038/s40494-025-01711-0) |
| 釉厚 | 经典刘家门样 **>1 mm**；官钧钧台样 **0.6–0.8 mm**；官钧制药厂样约 **0.3 mm**；底部橄榄棕反应玻璃层刘家门/钧台 **50–100 µm**，制药厂 **100–150 µm** | **断面实测**；[Hou Results/Fig. 1](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)。官钧组年代有争议，不宜把后三值无条件标为宋金元 |
| 元代釉厚补证 | 燕家梁最厚 YJ10 为 **1.38 mm**；该文转引元代刘家沟/赵家瓦民窑釉 **0.5–2 mm**，后者为**文献转引** | [Shi 2025 Table 9/正文](https://doi.org/10.1038/s40494-025-01711-0) |

**实测/模型反例。** Shi 2018 看到了短程有序，却按 d=96 nm、n_eff=1.564 算出反射特征约 **300 nm**，明确判定该古钧样没有可见光 amorphous photonic crystal 结构色；其 **106–260 nm** 是在折射率 1.5–1.8 及可见波长 380–780 nm 假设下的推算条件，不是该古样实测粒径区间。该文现代含铁矿渣复烧的 **414 / 437 / 496 nm** 反射峰也不是宋钧反射峰。[Shi 2018 §3.2–3.3/Eqs. 2–4/Fig. 5](https://doi.org/10.1016/j.jeurceramsoc.2017.10.036)

### 2.2 紫红斑：铜量不等于金属铜胶体量

| 量 | 古样结果 | 类型/出处 |
|---|---|---|
| 铜颗粒直径 | 古经典/官钧两组红区约 **30–70 nm**，紫区约 **10–30 nm**；FIB-SEM 所见多在富钙液滴中 | **实测**；[Hou Results/Fig. 9](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |
| 粒子空间位置补充 | Yuan 的 JS24 红面图像中少量铜粒在液滴与基质界面，约 **20 nm**；与“所有铜均以胶体存在”相反，多数溶解铜是离子态 | **实测/作者解释**；[Yuan 2022 Fig. 1, §2.2/Results](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016) |
| 总铜含量 | JS24 蓝面富铜处也 **<0.1 wt% CuO**；红面约 **0.2 wt% CuO**，伴 **0.3 wt% SnO₂、0.2 wt% PbO**（作者据此推测青铜原料）。0.2% CuO 换算元素铜约 **0.160 wt% ≈1600 ppm**，仅为化学计量换算，不能当金属 Cu⁰ 颗粒浓度 | **实测总量 + 本报告换算**；[Yuan 2022 Results](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016) |
| 铜价态 | Cu K-edge XAS/EXAFS 显示主体为溶解的 **Cu⁺ 和 Cu²⁺**；Cu⁺/(Cu⁺+Cu²⁺) 富钙区约 **0.6–0.7**、贫钙区约 **0.8–0.9**。单个拟合数和误差见 Table 3（如 BR1 0.7(1)，BP1 0.89(6)，RR1 0.65(8)，RP2 0.84(7)） | **实测谱拟合估计**；[Yuan 2022 Table 3](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016) |
| 金属 Cu⁰ 份额 | 作者因颗粒少、小、表面积大而无法从 XAS 准确量化金属铜贡献；**未得到古钧金属颗粒体积分数或数密度** | **明确证据缺口**；[Yuan 2022 §2.2/Results](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016) |
| 铜消光特征 | 红紫区 **550–600 nm** 的表面等离激元共振（SPR）特征；2022 JS24 红面约 **560 nm**。Cu⁰ 纳米颗粒的红色作用叠到乳白区为红，叠到透明蓝区为紫 | **实测反射谷 + 作者机制解释**；[Hou Fig. 10A](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[Yuan Fig. 5](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016) |
| Fe 价态微区差别 | JS24 蓝面富钙区 **17–20% Fe²⁺**，贫钙区 **57–70% Fe²⁺**；红面对应为 **8–11%**、**24–47%**，支持铜还原伴铁氧化。注意论文 Discussion 一处把富/贫标签颠倒，Results又将红富钙值写作10–12%；本报告优先Table 2逐点值（RR1=11(3)%、RR2=8(3)%） | **实测谱拟合**；[Yuan 2022 Table 2 / Results](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016) |

**推测（渲染实现）。** 把“蓝底的散射/吸收”和“局部 Cu SPR 吸收”分成两个场，紫斑边缘逐渐改变铜颗粒有效含量及浅/深蓝云量；不要只给表面覆盖一块紫色漆。需用照片约束红斑的毫米级布局，10–70 nm 粒子只进入有效光学系数，不应成为 4.5 cm 画幅里的可见噪点。这是从上述尺度和层内成色机制推得的实现建议，并非论文现成渲染结论。[机制依据 Hou 2018](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)

### 2.3 气泡：有金元实测的体积与数目分布

**实测对象。** Wang 2024 两片 DKJ-1/2 来自河北正定开元寺南广场遗址 I 区 H128 灰坑第一层，作者依据地层定为金元。Micro-CT 体素/文中空间分辨率分别 **1.980 / 9.263 µm**，边界气泡被移除后做统计；不是纳米液滴，也不是表面棕眼的孔径测量。[Wang 2024 Samples / §3.1.1](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005)

| 指标 | DKJ-1 | DKJ-2 | 证据 |
|---|---:|---:|---|
| 釉样总体积 mm³ | 0.868 | 148.42 | **实测 CT**，Table 1 |
| 气孔总体积 mm³ | 0.165 | 17.27 | **实测 CT**，Table 1 |
| 开闭孔合计孔隙率 | **19.00 vol%** | **11.64 vol%** | **实测 CT**，Table 1 |
| 气泡数（正文） | 571 | 10156 | §3.1.1 |
| 样本内气泡数密度 | **约 658 mm⁻³** | **约 68.4 mm⁻³** | **本报告推算**＝正文孔数/表中总体积；分辨率差使两者不能直接比较为配方差 |
| 平均 Feret 直径 <50 µm | 466 个 / 81.61% | 6650 个 / 65.48% | **实测 CT 分箱**，Table 4 |
| 50–100 µm | 82 个 / 14.36% | 2498 个 / 24.52% | 同上 |
| 100–200 µm | 19 个 / 3.33% | 790 个 / 7.78% | 同上 |
| >200 µm | 4 个 / 0.70% | 221 个 / 2.18% | 同上 |

以上每行均出自 [Wang 2024 Tables 1、4 / §3.1.1](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005)，非推荐通用配方；平均Feret直径不是等体积球直径，不能把该分箱直接当作球形泡的直径分布。**原始来源有内部不一致：**正文“90% larger than 100 µm”与 Table 4 相反（表显示多数小于 100 µm）；DKJ-2 表内分箱数合计 **10159**，与正文 **10156** 相差 3；部分计数与百分比也非完全相符。因此保留表的逐项原值，密度只报约数并明确推算。不能默默将笔误的“90% >100 µm”写入渲染规格。

**实测位置关系。** 大于 **100 µm** 的大泡主要在釉中层，小于 **100 µm** 的较小泡偏釉表层；泡孔率沿深度的曲线见 Fig. 8；正文称最大约 **300 µm**。元代燕家梁 YJL-1 的另一组标本以 **200 µm** 为表/中层阈值；应把它当跨样差异，不抹平成唯一常数。[Wang 2024 Abstract/Fig. 8](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005)；[Shi 2025 Fig. 10a](https://doi.org/10.1038/s40494-025-01711-0)

**机制与限制。** Hou 认为微米级气泡不能解释其蓝釉的选择性纳米散射，主导乳光的是分相玻璃；Wang 讨论了气泡/玻璃大折射率差对不透明度的贡献，但也明确 CT 分辨率不足以单独验证乳浊机制。可把气泡作为次级散射、可见体内缺陷、表面破口来源；不得用气泡模型替代分相光学。[Hou Discussion](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)；[Wang §3.2.1](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005)

### 2.4 石英、微晶与“未知”的确切边界

**实测。** Reedy 对 15 片钧样作 30 µm 薄片岩相：低质量釉可见未熔石英核并有方石英边缘；Fig. 4 的标尺 **60 µm**，可作实际形状/尺度参照（图已存 `img/reedy2016-fig4-quartz-cristobalite.jpeg`）。Fig. 5、6 显示钙长石羽状晶/团块，长时烧成和慢冷被作者用于解释。这个 60 µm 是图中标尺，**不是平均石英直径**。[Reedy 2016 §2.2/Figs. 4–6](https://www.udel.edu/content/dam/udelImages/bidenschool/chad/ReedyGreatWares.pdf)

**实测但未定量。** Hou 通过线扫 Si 峰识别未熔石英，未给出其粒径分布、体积分数或数密度；Shi 2025 Figs. 11/13 有石英及旁生晶图，但同样未给釉中石英数密度。这轮可访问正文未找到可直接用于经典宋金河南钧釉的石英粒径分布或颗粒/mm³。应留作未知，不用现代配方的研磨粒径或胎体石英粒径冒充。[Hou Results/Fig. 1](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)；[Shi 2025 Figs. 11/13](https://doi.org/10.1038/s40494-025-01711-0)

### 2.5 光谱证据清单：哪些测了，哪些没有

- **实测反射**：Hou Fig. 10A，Shimadzu UV–Vis 2700 + ISR 3100 积分球，光斑 **3 × 1 mm**、光谱分辨率 **1 nm**，D65，BaSO₄ 白标准；直接测釉面漫反射，包含衬底和层厚效应。亮蓝在 **400–600 nm** 反射较高；深蓝曲线偏 **400 nm**；红紫有 **550–600 nm** 的 Cu 特征。图已存 `img/hou2018-fig10-optical-spectra.png`。论文图提供 R(λ) 曲线，未检到公开机器可读 CSV。[Hou methods/Fig. 10](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)
- **实测反射**：Yuan Fig. 5 为 JS24 红蓝面 UV–Vis 对比，铜 SPR 约 **560 nm**。该文引用 Fe²⁺ **1100 nm** 宽带的通用硅酸盐证据，不能把 1100 nm 自动说成该片已测透射峰。[Yuan methods/Fig. 5](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016)
- **模型散射**：Hou Fig. 10D 的不同滴径散射系数是固定体积分数的 **Mie 理论计算**（球多极展开至三阶），不是直接测得 μ_s(λ)；Fig. 10C 的铁/钛玻璃吸收与 30/60 nm Cu⁰ 消光是解释用曲线，不是该古片独立测出的所有组分光学常数。[Hou methods/Fig. 10 caption](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)
- **测量派生颜色**：经典钧 JS4F 的 CIE L*a*b*=**40.9, −3.6, −5.0**；经典浅蓝 JS5R **67.8, −8.0, −2.4**；红 JS2F **38.0, +4.5, 0.0**；官钧紫 JS27F **43.6, +8.6, −6.0**。这些是具体测区而非通用天蓝色值，不应直接当渲染器的线性 RGB。[Hou Table III](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)
- **本轮证据缺口**：没有找到经典宋金元古钧釉的独立体积散射系数 μ_s(λ)、吸收系数 μ_a(λ)、相函数 g(λ) 或 BSDF/BTDF 完整实测；未找到分离后的古釉片透射 T(λ) 数据。现有漫反射不能唯一反演这四者与层厚。渲染拟合可用既有反射谱和微结构约束，但应标为**模型拟合/推测**，不能声称“实测全套光学参数”。



下图是原论文图10：A才是古样实测漫反射；C、D为解释与计算曲线。图像为PDF原生尺寸，不将屏幕放大当成更高光谱精度。[Hou原文图10](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[逐图权利记录](optics-images.md)。

![Hou2018：古样反射与计算曲线，A实测、D计算](../../ref/jun/img/hou2018-fig10-optical-spectra.png)

## 3. 蚯蚓走泥纹：成因、宽度与走向

### 3.1 核心原始研究与成因的证据强度

李媛、苗建民、孙新民、冯小琦、贾翠，《古代钧台窑钧釉“蚯蚓走泥纹”的成因探析》，《故宫学刊》2013，正文印刷pp227–233，下载PDF共8页。[原始PDF](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)，[本地](../../ref/jun/papers/worm_DPM_2013_ancient_Juntai.pdf)。

**【实测／观察】**纹区呈更玻璃质的深色带；截面、SEM-EDS显示纹与周围在相组成、晶体和Ca／Fe等成分分布上有差异。**【文献解释】**作者支持施釉后干燥／预热时釉层收缩开裂，烧成时较易熔组分流入、填充愈合的过程。这说的是**釉层**，没有证明胎坯本体必须先裂。它也不同于冷却后产生的尖锐开片。[故宫2013，pp229–233](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)。

“保温越久纹越浅”的解释来自两样本差异、晶体及界面观察，是**作者推测**，并非在同一配方上受控改变保温时间的实验。故宫2014研讨会另记现代施釉演示中晾干后已出现不规则裂纹，可作现代工艺旁证；报道中的约980–1000°C素烧窗口不能直接当成古代所有钧窑的必备工艺。[2013论文](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)、[故宫研讨会记录](https://www.dpm.org.cn/journal/247025.html)。

### 3.2 可引用的实测尺度

**全部属于钧台相关样本，原文传统定“宋官钧”，本报告保留断代争议。**不是目标宋金元民钧总体统计。[原论文](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)、[BM年代边界](https://www.britishmuseum.org/collection/term/x112232)。

| 参数 | JS-29蓝釉 | JS-30紫红釉／鼓钉洗口沿 | 证据、位置 |
|---|---:|---:|---|
| 平均纹宽 | 1.0mm | 1.6mm | 【实测】表2，p232；[论文](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |
| 平均釉厚 | 920µm | 850µm | 【实测】同表；[论文](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |
| 纹区域深入釉层的平均深度 | 850µm | 65µm | 【实测】同表，**非表面沟槽高差**；[论文](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |
| 观察区大小／条数／最长纹 | 约50×40mm／8条／约50mm | 约60×30mm／十余条／约30mm | 【实物观察】pp227–228；[论文](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |
| 走向 | 口沿向底足，多近似平行 | 纵横交错，有向下、平行口沿两类 | 【实物观察】同文，不能全部做成垂直重力流；[论文](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |
| 胎体原烧成温度估计 | 1290±20°C | 1310±20°C | 【方法推定】热膨胀再加热法，非窑温记录；[论文](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |
| 纹区／周围CuO当量 | 0.01／0.01wt% | 0.15／0.15wt% | 【元素定量】表1；不等于铜胶体浓度；[论文](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) |

**未报告：纹间距分布、纹宽误差、曲率分布、方向直方图、表面高度图。**不能用样片宽度÷条数冒充实测间距；也不能用850µm釉内色带深度做850µm表面凹槽。[原始全文及表2](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)。

**【计算／建议】**45mm视宽下，1.0–1.6mm纹宽占画宽2.2–3.6%；4096px画幅为约91–146px。这种尺度需要有釉内颜色／散射变化和边缘起伏，不能只做亚像素裂纹。目标若严格选宋金元器，纹的密集程度应以选定器物照片为准；先验证德基瓶肩部形貌，不直接复制有断代争议的钧台洗。[尺度据表2换算](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)、[德基实物](https://www.dejiart.com/en/digital_library/junyaotianlanyouzicaizhangjingping/)。

## 4. 现成光学模型、渲染与代码

**本轮未定位到包含宋金元蓝釉、铜紫斑、气泡、蚯蚓纹并经多角度实物验证的完整开源钧釉材质。**这只是下列论文／代码检索的结果，不是“不存在”的证明。找到的是可组合的光谱模型与通用计算核。[Hou2018](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[Li & Lei2022](https://arxiv.org/abs/2208.08043)、[miepython](https://github.com/scottprahl/miepython)、[Mitsuba3](https://github.com/mitsuba-renderer/mitsuba3)。

| 资源 | 能复用的部分 | 验证范围、限制、代码情况 |
|---|---|---|
| Hou等2018，JECS，DOI10.1016/j.jeurceramsoc.2018.05.010 | 钧釉实物结构、反射谱、Mie散射与铜SPR计算；最贴近目标 | 有古钧样品数据；不是3D转台渲染器，未找到随文开源材质；[论文](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |
| Li & Lei2022，*The computational simulation of the reflection spectra of copper red glaze*，DOI10.1063/5.0095570 | Mie铜／Cu₂O截面，多层前后通量、反射谱、L*a*b* | 对铜红釉实验比较；简化角度、均匀球形粒子与法向入射，不等于钧紫斑或3D角度渲染。未找到随文代码；[arXiv全文](https://arxiv.org/abs/2208.08043)、[本地](../../ref/jun/papers/model_Li_Lei_2022_copper_red_reflection.pdf) |
| Cuvelier等2012，*Copper red glazes: a coating with two families of particles*，Applied Physics A106:915–929，DOI10.1007/s00339-011-6707-3 | 现代铜红TEM/EELS、反／透射实测与四通量辐射传输；小粒吸收、大粒散射 | 实验对象为现代复烧铜红，不是宋金元钧紫斑；10–50nm吸收族与约≥100nm散射族不能直接取代Hou紫斑粒径。未找到公开代码；[作者预印本](https://arxiv.org/abs/1302.2302)、[本地](../../ref/jun/papers/model_Cuvelier_2012_copper_red_four_flux.pdf) |
| Hendy2002，*Light Scattering in Transparent Glass Ceramics*，APL81:1171，DOI10.1063/1.1499989 | 分相晚期的Rayleigh–Debye／结构因子；提醒粒子相关性会改变独立散射估计 | 透明玻璃陶瓷、弱散射且忽略多重散射，不能无条件套到乳浊钧釉；[作者预印本](https://arxiv.org/abs/cond-mat/0207591)、[本地](../../ref/jun/papers/model_Hendy_2002_glass_ceramics.pdf) |
| Shi等2018，非晶光子结构分相釉 | 分相短程有序、结构尺度与颜色，古样及复烧对比 | 材料机理论文，不是完整渲染。不可把所有钧蓝写成可见Bragg光子晶体色；[论文](https://doi.org/10.1016/j.jeurceramsoc.2017.10.036) |
| **miepython**，MIT | Mie效率、g、角度散射，复折射率与粒径分布积分的基础 | 不处理连续互穿相、密集相关性或开口孔；相函数归一化必须核对；[作者仓库](https://github.com/scottprahl/miepython)、[官方角分布说明](https://miepython.readthedocs.io/en/stable/03_angular_scattering.html) |
| **NIST SCATMECH** | `Distributed_Mie_Phase_Function`，含粒径分布与介质／颗粒折射率 | 通用计算核，不是钧釉成片；[官方源码](https://pages.nist.gov/SCATMECH/code/phasefunction.cpp) |
| **Mitsuba3** | 光谱路径追踪、表面与介质分离、有限厚釉层 | 无经验证Jun preset。`sigma_t`为场景长度单位倒数；`tabphase`标准参数是一维角度表，不能直接声称支持任意波长依赖Mie相函数，可能需分波段或自定义插件；[仓库](https://github.com/mitsuba-renderer/mitsuba3)、[介质](https://mitsuba.readthedocs.io/en/latest/src/generated/plugins_media.html)、[相函数](https://mitsuba.readthedocs.io/en/latest/src/generated/plugins_phase.html) |

### 4.1 对45mm转台的推荐路线（尚未实施，均为建议）

| 方案 | 与现有证据的关系 | 取舍 |
|---|---|---|
| 表面RGB＋微法线＋单一清漆 | 可快速拟合一张图的配色，但不直接表达分相体散射、铜吸收、釉内纹 | 适合预览；不是本项目微距、移动高光的首选。[需表达的现象据Hou2018](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) |
| **有限厚度釉层＋光谱吸收／散射＋可见缺陷几何** | 能分别约束界面高光、蓝釉深度、紫斑和局部形貌 | 推荐。先以统计系数表达纳米相；不显式建亿万个液滴。Mie先作基线，密集或互穿相需对比结构因子／有效模型。[Hou2018](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[Hendy2002](https://doi.org/10.1063/1.1499989)、[Mitsuba介质](https://mitsuba.readthedocs.io/en/latest/src/generated/plugins_media.html) |
| 对每个液滴全波电磁计算 | 可研究局部相关性，尺度和算力不适合整件45mm视野的首轮迭代 | 只在独立粒子模型被实测谱否定后，用于代表微区的离线验证。[相关性问题据Hendy](https://doi.org/10.1063/1.1499989) |

**【建议】**分四个尺度建模：①厘米紫斑覆盖与形状；②毫米釉厚／蚯蚓纹／局部乳浊云；③微米可见泡、棕眼与起伏；④纳米分相与铜，用光谱系数表达。紫斑变化应包含铜粒径／含量、蓝底散射和釉厚变化，别把“紫”强制做成完全遮盖底釉的一层。表面开口棕眼与内部封闭泡分别处理，缺少确认的细点只作外观参照。[结构与层次据Hou](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[气泡分层据Wang2024](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005)、[纹截面据故宫2013](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)。

独立球形散射的起点可写成：`N = f / ((π/6)⟨d³⟩)`，`μs(λ)=∫n(d) Csca(d,λ) dd`，`μa(λ)=μa,glass(λ)+∫nCu(d) Cabs,Cu(d,λ) dd`，光学厚度`τ=(μs+μa)t`。这里`f`为体积分数，`n(d)`是单位体积、单位粒径间隔的数分布，不是归一化直方图；所有长度单位必须一致。**【计算框架】**这只是独立散射近似，不把25%致密分相自动当成稀释悬浮液；不把元素CuO wt%直接代为铜粒子f。[Mie模型依据](https://github.com/scottprahl/miepython)、[相关性限制](https://doi.org/10.1063/1.1499989)、[体积分数和铜实物依据](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)。

**【建议／可证伪验证】**先固定样本类别、粒径定义和釉厚，在平片上比较蓝地／紫斑反射谱及可用透射谱；独立Mie与结构因子路线并列比较。若谱形不对，先查吸收、粒径与相关性，不进入无依据的高光微调。再固定照明拍45mm球腹转台，多角度检查高光、斑边、纹深与纹理绑定；若只能匹配一个角度，就不能称材质通过。现有馆藏照缺受控光源与同器标尺微距，因此本轮给出验证方法，**没有宣称这些验证已做过**。[实测谱基准Hou](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[铜红反透射基准Cuvelier](https://arxiv.org/abs/1302.2302)。

## 5. 文件、下载与尚缺数据

已保存并逐页读取验证 **11篇PDF**，完整发表信息、下载版本、直链、权利及SHA-256见 [papers/index.md](../../ref/jun/papers/index.md) 与 [papers/manifest.json](../../ref/jun/papers/manifest.json)。下列源文件包括作者接受稿、期刊开放版和公开作者预印本，未取得的文献不伪装为已读全文。

| 核心来源 | 本地PDF | 最直接用途 |
|---|---|---|
| [Hou等2018，Jun ware glazes: Chemistry, nanostructure and optical properties](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) | [hou-2018-jun-nanostructure.pdf](../../ref/jun/papers/hou-2018-jun-nanostructure.pdf) | 古Classic/official Jun；结构与漫反射。封面年份排版错误依DOI纠正为2018。 |
| [Yuan等2022，Jun ware glaze colours: An X-ray absorption spectroscopy study](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016) | [yuan-2022-jun-xas.pdf](../../ref/jun/papers/yuan-2022-jun-xas.pdf) | 古钧台JS24，铜铁XAS；official Jun年代另核。 |
| [王元旭等2024，显微CT技术在钧釉瓷微观结构中的应用](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005) | [wang-2024-jun-microct.pdf](../../ref/jun/papers/wang-2024-jun-microct.pdf) | 金元正定开元寺两片；正文/表气泡数据矛盾已在报告注明。 |
| [Shi等2018，Amorphous photonic crystals and structural colors in the phase separation glaze](https://doi.org/10.1016/j.jeurceramsoc.2017.10.036) | [shi-2018-amorphous-photonic-glaze.pdf](../../ref/jun/papers/shi-2018-amorphous-photonic-glaze.pdf) | 古样与现代复烧分开；106–260nm是模型条件，不是古样粒径范围。 |
| [Shi等2025，Composition and microstructure of Yuan Dynasty Jun glazed stoneware from Yanjialiang site, Inner Mongolia, China](https://doi.org/10.1038/s40494-025-01711-0) | [shi-2025-yuan-yanjialiang.pdf](../../ref/jun/papers/shi-2025-yuan-yanjialiang.pdf) | 元代燕家梁样；主要组作者归河北定窑来源，不替代河南。 |
| [Yuan等2024，Changsha ware glaze color: Composition, nanostructure, and copper and iron speciation](https://doi.org/10.1111/jace.20025) | [yuan-2024-changsha-comparison.pdf](../../ref/jun/papers/yuan-2024-changsha-comparison.pdf) | 长沙是新实测对象；其中钧釉数据为同组前作归纳转引。 |
| [Reedy2016，Petrographic and Image Analysis of Thin Sections of Classic Wares of Song Dynasty](https://www.udel.edu/content/dam/udelImages/bidenschool/chad/ReedyGreatWares.pdf) | [reedy-2016-petrographic-song-wares.pdf](../../ref/jun/papers/reedy-2016-petrographic-song-wares.pdf) | 15片钧样薄片；石英/方石英/钙长石形貌。 |
| [李媛等2013，古代钧台窑钧釉“蚯蚓走泥纹”的成因探析](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) | [worm_DPM_2013_ancient_Juntai.pdf](../../ref/jun/papers/worm_DPM_2013_ancient_Juntai.pdf) | 正文印刷227–233；原文宋官钧旧称；两样片，不当宋金元民钧统计。 |
| [Li & Lei2022，The computational simulation of the reflection spectra of copper red glaze](https://doi.org/10.1063/5.0095570) | [model_Li_Lei_2022_copper_red_reflection.pdf](../../ref/jun/papers/model_Li_Lei_2022_copper_red_reflection.pdf) | 铜红光谱模型，不是完整钧釉3D渲染。 |
| [Cuvelier等2012，Copper red glazes: a coating with two families of particles](https://doi.org/10.1007/s00339-011-6707-3) | [model_Cuvelier_2012_copper_red_four_flux.pdf](../../ref/jun/papers/model_Cuvelier_2012_copper_red_four_flux.pdf) | 现代铜红试片；反/透射、TEM和四通量模型。 |
| [Hendy2002，Light Scattering in Transparent Glass Ceramics](https://doi.org/10.1063/1.1499989) | [model_Hendy_2002_glass_ceramics.pdf](../../ref/jun/papers/model_Hendy_2002_glass_ceramics.pdf) | 通用分相相关性；非钧窑实物拟合。 |

图像共 **53个文件**：32张官方整器／组成部分照片（含重复视角与同图TIFF/JPG），3张原像素裁切，18张论文图／表或含图注页区；不把文件数量当成独立器物数。[逐图清单](../../ref/jun/img/index.md)。PDF全部可打开，图像全部经解码核对，清单覆盖整个`img/`，不是只有缩略图链接。

故宫部分HTML使用curl获取（Python TLS握手失败）；台北故宫04009328第二图传输不完整，未保留为有效图片；台北圆盘与BM图下载失败原因见§1.3。现代工艺PDF `junci360.com/uploadfile/2013/0817/20130817062057792.pdf` 原站TLS失败，未将其未读内容作为实测证据。[已获取的现代工艺旁证为故宫网页](https://www.dpm.org.cn/journal/247025.html)。


**仍缺且不能用猜测补齐的参数**：目标同一器物的两相三维粒径／空间相关分布、全波长两相复折射率、铜金属纳米粒子的绝对体积分数、未熔石英的可靠尺寸／数密度、表面棕眼径深分布、宋金元目标器蚯蚓纹间距统计、同器多角度BRDF／BTDF与标定反射透射。现有论文和图像能约束其中若干尺度及机制，不能唯一决定整套材质。[Hou结构与光学方法](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010)、[Yuan铜价态](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016)、[气泡CT分辨率限制](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005)、[蚯蚓纹仅两样片](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf)。

[下载脚本](scripts/fetch_reference.py)。版权信息只说明文件来源及原站声明；保存作参照不意味着获得对外再发布许可。
