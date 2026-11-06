# 蓝孔雀眼斑反射光谱：原始数值与角分辨图谱

采集日期：2026-11-02。

## 1. Kane 等 2019：真正的作者数值表（优先使用）

- 论文：Kane SA, Wang Y, Fang R, Lu Y, Dakin R. *How conspicuous are peacock eyespots and other colorful feathers in the eyes of mammalian predators?* PLOS ONE 14(4), e0210924. [DOI](https://doi.org/10.1371/journal.pone.0210924)。本地：`papers/spectra_Kane_2019_PLOS.pdf`。
- 数据出处：论文 Data Availability 和 p.9 数据链接指向 [Figshare 作者数据归档](https://figshare.com/s/688fb19dad98b6273324)；实际 ZIP file ID 27807240，[可下载 API](https://api.figshare.com/v2/file/download/27807240)。归档总长 1,054,008,566 bytes；这里只用 HTTP Range 提取 ZIP 内相关 XLSX，未整包下载。原始条目名和字节大小见 `spectra_Kane2019_archive_inventory.json`。Figshare 条目声明 CC0。
- 原始数值位置：ZIP `figshare/Fig 2 and 3 data/Indian peacock eyespot reflectance spectra.xlsx`，保存于 `data/spectra_Kane2019_original/`；对应论文 Fig.2D，PDF p.4。`Sheet1` 第 1 行为名称，第 2 行为 `%`，第 3–403 行为 300–700 nm，每 1 nm 一个点，共 401 个波长。
- 5 种眼斑区：PB = purple black；BB = blue black；BG = blue green；BZ = bronze-gold；GB = green barbule（此处作者用该名称指外围绿色区域；与别处将 GB 写作 loose green barbs 的措辞需结合 Fig.2A 理解）。颜色区位置见 Fig.2A，PDF p.4。
- 原表 G–K 列逐点重复 D/E/F/C/B 列，**不是角度、独立样本或误差条**。整理版移除重复列；原表与逐列完整 CSV 保留供核查。
- 可用 CSV：`spectra_Kane2019_eyespot_percent.csv` 为作者百分反射率；`spectra_Kane2019_eyespot_fraction.csv` 为逐项除以 100 后的无量纲 R；`spectra_Kane2019_eyespot_source_all_columns.csv` 保留原表所有列和两行表头。没有再插值、平滑或归一化。

| 区域 | 数值表峰值波长 nm | 峰值反射率 % | 数据类型 |
|---|---:|---:|---|
| PB 紫黑 | 434 | 3.50833 | 作者发布实测处理后数值 |
| BB 蓝黑 | 455 | 5.05017 | 同上 |
| BG 蓝绿 | 496 | 23.92159 | 同上 |
| BZ 铜金 | 589 | 18.28732 | 同上；约 450 nm 另有副峰 |
| GB 外围绿色 | 555 | 8.14092 | 同上 |

这些是逐点最大值，不是作者另行报告的拟合峰心；1 nm 的表格间隔不代表 1 nm 的独立光谱分辨率。

### 样品、仪器、角度与标定的边界

- 物种明确为 *Pavo cristatus*（Indian peafowl）。眼斑羽毛样品数 5，蓝色胸部轮廓羽 3；论文 p.4–5 “Feather samples”。不能从该 XLSX 还原每个样本、误差或每次重装的谱；它是 Fig.2 绘图用处理后曲线，并非探测器计数。
- 光谱仪 Ocean Optics USB2000+；实测采集范围 300–850 nm；积分 100 ms，3 pixel boxcar，5 次平均；分辨率 2.06 nm FWHM。PX-2 脉冲氙灯 200 Hz；白标准为 99% PTFE（Spectralon USRS-99-010-EPV / Thorlabs SM05CP2C），每 15 min 测白标准及暗电流。反射率按 `(样品信号−暗)/(白标准−暗)` 计算，再经 20 nm 波段的 Savitzky–Golay 平滑。详见论文 p.7 “Reflectance spectroscopy”。
- 入射和接收光束聚焦到直径约 2 mm 的同一光斑；每种几何重复卸装 3 次；p.7。同页的 45°照明/0°接收专指色卡和灰阶标准，**不能自动赋给 Fig.2D 羽毛曲线**。
- Fig.2D 的逐曲线照明/接收/方位角在 XLSX 中没有标注，正文也未给该组曲线的完整角度元数据。已下载 `papers/spectra_Kane2019_S2Fig_apparatus.docx` 检查其 Fig.S2A，只有仪器照片，没有可确定每条谱角度的数值。因此将 Fig.2D 数据角度标为 **未明确**，不把它编成角分辨数据。
- p.8 / Fig.4 的正面观察 0±2°、太阳方位 45±3°、仰角 30±3°、光源与相机夹角 52±3°是**室外多光谱照片**的条件；不能无依据套到室内反射光谱。
- 另一原始表 `saucer magnolia leaf blue peacock reflectance spectra.xlsx` 对应 Fig.2E（蓝孔雀胸羽和背景叶），整理为 `spectra_Kane2019_leaf_breast_percent.csv`。胸羽不是眼斑，不要作为眼斑蓝区替代。额外保留同目录作者锥细胞谱和鹦鹉表，以完整保留提取来源，但不将其用于本研究羽毛参数。

## 2. Dakin & Montgomerie 2013：3 色 × 3 入射角，矢量图数字化

- 论文：*Eye for an eyespot: how iridescent plumage ocelli influence peacock mating success*. Behavioral Ecology 24(5):1048–1057. [DOI](https://doi.org/10.1093/beheco/art045)。作者主页提供 [PDF](https://drive.google.com/file/d/1YA0nfFOigsRp0ZuFCU3XjectdWZ6AGDa/view)，本地 `papers/spectra_Dakin_Montgomerie_2013.pdf`；作者页 [Papers](https://www.roslyndakin.com/papers.html)。旧 WordPress PDF 链接现为 404，实际从作者现用链接下载。
- 来源 **Fig.2，印刷 p.1049 = PDF p.2**；每条曲线为 10 只雄鸟各取 1 根羽毛的平均，三个区为 PB、BG、BZ。图例实线=30°，长虚线=45°，点线=60°。
- 输出：`spectra_Dakin2013_Fig2_vector_digitized_percent.csv`；401 行（300–700 nm，1 nm）×9 曲线。**不是原始仪器数据**，而是提取 PDF 已绘制的连续矢量折线并标定坐标；比从截图寻找虚线像素稳定。每条曲线恰好有 400 条线段 / 401 顶点，x 等间距误差 <0.002 PDF point，因而推断其为每 1 nm 一个采样，并将顶点顺序映射到 300…700 nm；端点与图上横轴刻度的排版偏差约 0.6 nm，包含在下述 ±1 nm 估计内。
- y 轴 0/10/20/30/40% 的左侧刻度做线性最小二乘，`y_pdf = 365.8873169 − 1.6314502 × R_percent`。刻度拟合最大残差 0.102 PDF point（约 0.063 个百分点）。将实际读图与排版标定总误差保守记为约 **±0.2 个百分点、±1 nm**；这是数字化误差估计，不是实验不确定度。PDF 的 5 位小数输出不代表测量精度。
- 保存了 `spectra_Dakin2013_Fig2_source_crop.png`、`spectra_Dakin2013_Fig2_digitization_metadata.json` 和重建脚本 `spectra_prepare.py`，可核查线型、颜色、曲线编号与坐标标定。

### 几何定义非常关键

Fig.1 与 p.1049–1050：羽毛正面右侧各色区，观察探头沿羽毛整体平面法线，即观察角 **0°**；光源置于观察方向右侧 **30°、45°、60°**，照明和接收不满足整体羽面上的对称镜面条件。它们是宏观羽毛面上的非镜面几何，不能直接当作二维光子晶体层面法线的 30/45/60°镜面入射谱。羽小枝局部倾角/扭转可使局部满足镜面条件。该数据适合校验整个羽毛片的角度依赖，纳米结构局部谱需要结合朝向分布和探头接受角。

- 仪器：Ocean Optics USB4000-UV-VIS；DH-2000 氘/钨卤素光源；400 μm 光纤加准直透镜，入射和观察工作距离分别 560 mm / 470 mm，样品光斑约 2 mm；p.1050。
- 反射率是相对于与羽毛等厚的叠层 Teflon 胶带白参考，不是积分球的半球总反射率；暗室测量；10 scans，100 ms，12 pixel boxcar，每 15 min 重新白/暗标定；各色区取下重装两次后平均；p.1050。不同论文标定和采样几何不同，绝对幅度不能无条件强制相同。

| 区域 | 光源相对观察方向角度 | 观察角 | 图线峰值 nm | 图线峰值 % |
|---|---:|---:|---:|---:|
| BG | 30° | 0° | 507 | 39.75 |
| BG | 45° | 0° | 499 | 43.35 |
| BG | 60° | 0° | 487 | 33.52 |
| BZ | 30° | 0° | 650 | 22.84 |
| BZ | 45° | 0° | 639 | 30.49 |
| BZ | 60° | 0° | 624 | 36.97 |
| PB | 30° | 0° | 460 | 5.13 |
| PB | 45° | 0° | 453 | 6.80 |
| PB | 60° | 0° | 444 | 8.14 |

## 3. 验证与没有取得的数据

- 已视觉检查 Kane Fig.2 原页、Dakin Fig.2 原图裁切；从 CSV 重绘 `spectra_validation_replot.png` 并视觉对照。峰位置、主副峰、线型与振幅一致。所有主交付 CSV 都是 401 个连续波长，没有缺失值。
- 已核查作者主页、论文和 Dryad 搜索；未找到 Dakin2013 的开放逐样本原始光谱库。搜索到的 Dryad `10.5061/dryad.vt562` 属于另一篇“copulation calls”论文，不能冒充眼斑光谱。
- Loyau2007 的论文确有角分辨测量，但本轮不再额外数字化：Dakin2013 已提供本任务所需的 P. cristatus 三种眼斑区、多角度实测曲线；这不意味着找到了黄色细环的多角度曲线。黄色/褐色更细分区的实测谱由其他光学论文补充，不能由本表重命名生成。
- 这些毫米级光斑反射曲线采样许多羽小枝及其缝隙；用于微距渲染时，曲线幅值包含填充率、排列与倾角、遮挡和接受角效应，不能直接把其峰值当作单个光子晶体表面的本征峰反射率。此为根据测量光斑和局部结构所作的建模判断。
