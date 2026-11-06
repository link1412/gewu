# 蓝孔雀眼斑微距渲染：结构、光学参数与实测参考

资料核查日期：2026-11-02。目标画幅宽 10–20 mm；对象为 **蓝孔雀 Pavo cristatus 的尾上覆羽（train feather）眼斑**，不是飞行尾羽，也不是颈胸羽。

**推荐基线：Freyer & Stavenga 2020 的六色区有效介质多层膜传递矩阵模型，采用有色散和吸收的材料常数；羽枝、羽小枝及细胞曲面显式控制局部法线。** 它同时覆盖目标物种、眼斑、有限层结构和实测反射谱。二维棒阵列是几何基础；需要检查有效介质误差时，再用同一结构做二维 RCWA/散射矩阵或 FDTD 对照。2019 年同组对颈胸羽的有效介质/FDTD 比较支持这一简化，但不能当作眼斑全部角度的独立验证。[F20 pp.51–53,56–60；F19 §2.6, §3.3]

本资料包已完成：原始 PDF 与真实照片下载、参数分类、作者数值表转换、光谱图数字化、原图叠加/重绘核验。**未找到或未取得的资料列在第 7 节；没有补造数值。** 没有运行目标渲染器或宣称重新复现了论文 TMM。

## 1. 先避免混用物种、色区和证据类型

- **Zi et al. 2003 明确研究绿孔雀 Pavo muticus**，不是 P. cristatus；仍是重要的经典机制与参数参考。[Z03 p.12576 “Materials and Methods”]
- Yoshioka & Kinoshita 2002 的蓝色样本来自体羽，黄色样本来自尾覆羽；并非在一根眼斑上分出的“蓝、黄环”。它的角度曲线不能改名为眼斑蓝环真值。[Y02 p.170 §2]
- Freyer 2020 的 R1–R6 依次为：**黑紫中心、蓝绿、褐、绿黄、紫、黄铜绿外缘**，位置见下图。Kane 2019、Dakin 2013 的 PB/BG/BZ 等是另一种分区方案，不能按名字逐一强行等同。[F20 Fig.1 p.53；K19 Fig.2A p.4；D13 Fig.1 p.1048]
- 下文分为 **实测**（显微/TEM/光谱）、**拟合模型**（为匹配光谱而选的参数）、**本次读图估计**、**转引汇编**。模型数值不代表所有个体的固定尺寸；不同研究也不是同一根羽毛。

![蓝孔雀真实眼斑、羽枝与各色区微照片，含比例尺](photos/Freyer_2020_Fig1_cristatus_train_macro_micro_CC-BY-NC-3.0.jpg)

图源：Freyer & Stavenga 2020 Fig.1，期刊 p.53／本地 PDF 第 6 页；作者实拍，CC BY-NC 3.0。a：20 mm；b：5 mm；c、d：1 mm；e–j：50 µm。拍摄 RGB 未作光谱标定；照片适合形态、疏密、色区位置和局部色变的外观检查。[原论文](https://doi.org/10.1039/D0FD00033G)

## 2. 二维光子结构：参数表

### 2.1 Zi 2003：经典四区，物种为 P. muticus

以下周期和层数来自 SEM 观察，棒轴大致平行皮质表面。蓝/绿/黄近方格，褐色近矩形。单位均为 nm；层数是**黑色素棒层数**，不是传递矩阵中的数值切片数。[Z03 pp.12576–12577、Fig.1]

|色区|表面平行方向中心距|表面法向层周期|观察层数 N|名义棒径 Dm|名义空气孔径 Da|表层角蛋白厚度|
|---|---:|---:|---:|---:|---:|---|
|蓝|≈140|≈140|≈9–12|112，按 0.8a 推导|70，按 0.5a 推导|未给独立数值|
|绿|≈150|≈150|≈9–12|120，同上|75，同上|未给独立数值|
|黄|≈165|≈165|≈6|132，同上|82.5，同上|未给独立数值|
|褐|≈150|≈185|≈4|原文未单列；F20 Table1 转录为 120|原文未单列；F20 转录为 75|未给独立数值|

**棒径/孔径的证据区别：** Z03 p.12577 给用于带结构计算的 `r_rod/a=0.4`、`r_air/a=0.25`，称结构比值取自测量；上表前三行直径是据此计算的**名义模型值**，不是每个色区单独报告的棒径均值和误差。矩形褐色不能把深度 185 nm 无条件代入方格公式。原文还说表面角蛋白中埋着 1–2 层黑色素棒，不能由此直接推算一层纯角蛋白膜厚。[Z03 p.12577；F20 Table1 p.52]

Z03 Fig.4 的有限层计算选 `N=10,10,6,4`（蓝、绿、黄、褐）。其模型采用 **角蛋白 n=1.54、黑色素 n=2.0 的无色散实数**，未提供按波长变化的 k。另有棒长约 0.7 µm、髓芯约 3 µm、细胞凹陷约 20–30 µm；均为该文样本的观察量。[Z03 Fig.1、p.12576；p.12577 Fig.4及正文]

**转录冲突：** F20 Table1 的 Zi 行把黄/褐层数列成 4/6，与 Z03 正文及 Fig.4 的 6/4 相反。这里以 Z03 原文为准；不把该冲突当成另一项测量。

### 2.2 蓝孔雀眼斑：2020 年可直接实现的一整套模型

**本表全部是拟合模型值，不是逐项直接测量。** 位置、记号以 F20 Fig.4a p.55 为准：`a` 为深度方向层周期，`b` 为表面横向中心距，`c` 为外表面到第一棒表面的角蛋白层厚度，`Dm/Da` 为黑色素棒/空气通道直径，`N` 为棒层数。a 的方向不要与其他论文的记号混用。[F20 Table1 p.52，Fig.4]

|区/外观|a|b|Dm|Da|N|c|表面附近的特殊结构|
|---|---:|---:|---:|---:|---:|---:|---|
|R1 黑紫|140|150|100|33|10|100|常规|
|R2 蓝绿|160|170|110|33|9|100|常规|
|R3 褐|190|150|110|50|5|70|本论文 Model 行没有省略首层空气的星号|
|R4 绿黄|195|150|120|55|5|130|常规|
|R5 紫|185|190|100|70|3|140|首个层周期为 240；省略第一空气通道层|
|R6 黄铜绿，模型 1|185|160|120|70|4|130|省略第一空气通道层|
|R6 黄铜绿，模型 2|185|160|100|70|3|150|首个周期为 240；省略第一空气通道层|

单位 nm。R6 的两个模型对应同一区内可见的不同谱型，不是两个新色环。保留空气相和表面两层的特殊构造，对单双峰尤其重要。[F20 Table1注、pp.57–60、Fig.6–8]

机读文件：[Freyer2020_model_parameters.csv](data/Freyer2020_model_parameters.csv)。拟合参数受到既有解剖数据约束，但并非唯一反演解；不可把 c、a、N 从不同论文任意拼接后仍称“文献已验证”。

为检查模型尺度，下表另外列出 **F20 转引的解剖范围**，未冒称本次已逐篇取得和复核 Durrer/Jiang 原文。c 故意不放入此表：F20 中 Durrer 的 c 范围来自 **刚果孔雀 Afropavo congensis**，不能当作蓝孔雀实测值。[F20 Table1 p.52、p.57；完整汇编与原引用索引见下方 CSV]

|区|原来源，按 F20 引用|a 范围 nm|b 范围 nm|棒径 nm|空气通道径 nm|层数|
|---|---|---:|---:|---:|---:|---:|
|R1 黑紫|Durrer 汇编|150–170|140–165|100–110|33|9–11|
|R1 黑紫|Jiang 2018|128–151|116–134|113–126|30–40|9–11|
|R2 蓝绿|Durrer|157–175|150–190|100–120|未给|9–10|
|R2 蓝绿|Jiang 2018|153–178|112–131|106–119|52–63|5–8|
|R3 褐|Durrer|198–223|135–172|100–120|未给|5–7|
|R4 绿黄|Durrer 汇编|190–220|115–190|100–130|55|4–6|
|R5 紫|Durrer|180–228|160–250|110–130|未给|4–7|
|R6 黄铜绿|Durrer|180–240|140–180|110–135|未给|3–6|

[Freyer2020_anatomical_ranges_secondary_compilation.csv](data/Freyer2020_anatomical_ranges_secondary_compilation.csv)。Jiang et al. 的研究是 *Mechanochromic response of the barbules in peacock tail feather*, Optical Materials 75,74–78 (2018)，[DOI](https://doi.org/10.1016/j.optmat.2017.08.024)；公开原始方法摘录确认 P. cristatus，但全文未取得，表中数值仅按 F20 汇编引用。

### 2.3 后来的直接实测表层厚度：Okazaki 2022

**2020 年“Pavo 缺少皮质厚度解剖数据”的限制，不能写成今天仍没有测量。** O22 方法明确是蓝孔雀尾羽；TEM 测外表面到第一层黑色素**表面**的距离，数值见 p.11，对应 Fig.4C/D。层数见 p.10。[O22 pp.5–6,10–11]

|O22 自己的图4分区|c 实测 nm，原文 ±|黑色素层数|另测到的深度，距外表面 nm|
|---|---:|---:|---|
|a 黑色中心|62 ± 6.70|2–3|第二层黑色素表面 202 ± 5.26|
|b 蓝|96 ± 5.66|11–12|第一空腔表面 216 ± 23.3|
|c 浅褐|136 ± 12.8|5–6|第二层黑色素表面 419 ± 16.3|
|d 绿|144 ± 13.2|7–8|第一空腔表面 296 ± 16.0|

原段没有明确解释厚度 ± 是 SD 还是 SE，也没有给相应独立个体数，故不自行命名。Table1 p.11 另有黑色素颗粒“间距 d”，n=5：a/b/c/d 分别为 **135±17.7 / 189±21.4 / 179±32.4 / 202±21.5 nm**。该 d 用于作者的 Bragg 估算，方向和定义不能直接等同 F20 的 a 或 b；n=5 也不自动适用于 c 的样本数。[O22 Table1、p.11]

[Okazaki2022_measured_cortex_depths.csv](data/Okazaki2022_measured_cortex_depths.csv)。蓝区 c≈96 nm 与 F20 拟合 100 nm 相近；浅褐 c≈136 nm 与 F20 褐区 70 nm 差异明显，黑区层数也不同。**保留为独立样本/分区证据，不能求平均掩盖差异。** O22 的光学计算是简化 Fresnel/Bragg 模型，n_m=1.7、n_k=1.6 为设定值，不是新的材料色散测量。[O22 pp.7,11]

### 2.4 Yoshioka 2002 和 Li 2005 的可确认内容

Y02 p.172 实测：蓝体羽棒径约 **130 nm**、层距 **150 nm**、规则层 **8–12**；黄色尾覆羽棒径约 **140 nm**、层距 **190 nm**、规则层 **3–6**。棒可长至数 µm，纵向没有同样的规则周期。棒径估计带有平行表面方向近密堆积假设。p.173 给蓝谱 FWHM≈110 nm、黄谱≈170 nm；不是眼斑各环统一参数。[Y02 Fig.1、§3.1–3.2]

Li et al. 2005，*Structural origin of the brown color of barbules in male peacock tail feathers*，[DOI](https://doi.org/10.1103/PhysRevE.72.010902)。**全文 PDF 本次未取得**，见第7节。原始摘要可确认：褐色主要为结构色；层数、周期、表面两层间距及缺失空气孔重要。F20 Table1 转引其模型为 `a=185 nm`、首周期 `235 nm`、`b=150 nm`、`Dm=120 nm`、`Da=75 nm`、`N=6`、缺失首空气层；这些只定位到 **F20 p.52 的 Li 行**，不伪报 Li 原文页图，也不未经核实指定物种。F20 自己的褐色模型另为 N=5、a=190 nm，不能混为一套。

## 3. 材料复折射率与传递矩阵用法

### 3.1 推荐色散，波长输入 nm

所有色区先共用同一材料函数，颜色差异由结构产生；**没有找到按蓝/绿/黄/褐分别测得的蓝孔雀本征 n,k**。

\[
n_k(\lambda)=1.532+5890/\lambda^2,\qquad k_k\simeq0
\]

\[
n_m(\lambda)=1.648+23700/\lambda^2,\qquad k_m(\lambda)=0.56\exp(-\lambda/270)
\]

- 角蛋白：L11 白鹅无色羽小枝的偏振干涉显微测量、Cauchy 拟合；`A=1.532±0.001`，`B=(5.89±0.21)×10³ nm²`。测量波长 390、451、494、546、588、650、715 nm；**不是直接测蓝孔雀**。可见光 k_k=0 是透明近似。[L11 pp.24064–24065、Fig.2B/3]
- 黑色素：S15 **Parotia lawesii 劳氏六线风鸟枕羽**的完整羽小枝测量结合 TEM 体积分数反推；不是分离孔雀黑色素的直接椭偏结果。`A=1.648±0.003`，`B=(2.37±0.14)×10⁴ nm²`，消光式系数 `0.56±0.01`、`270±5 nm`。[S15 正文 p.4、Fig.3b/c]
- F19、F20 把这些色散用于蓝孔雀并与反射谱比较，因此适合当前的物理起点。若复现 Zi 旧模型，则保留旧 n=2/1.54；不要替换一半材料常数后声称逐点复现旧图。[F19 §2.6；F20 pp.51–53]

|λ nm|角蛋白 n|黑色素 n|黑色素正消光系数 k|
|---:|---:|---:|---:|
|400|1.56881|1.79613|0.12729|
|450|1.56109|1.76504|0.10577|
|500|1.55556|1.74280|0.08789|
|550|1.55147|1.72635|0.07303|
|600|1.54836|1.71383|0.06069|
|650|1.54594|1.70409|0.05043|
|700|1.54402|1.69637|0.04190|

[optical_constants_400_700nm_5nm.csv](data/optical_constants_400_700nm_5nm.csv)：每 5 nm 的**解析拟合函数采样**，不是数字化原始测量点。CSV k 均取正值。F20 写 `ñ=n−ik`；求解器若用相反时间谐波约定，需相应改变虚部符号，确保吸收而非增益。空气 n=1。[F20 p.51]

### 3.2 推荐的物理实现及可检查标准

F20 沿深度切成 **1 nm** 层，每层从圆柱几何求 `f_k+f_m+f_a=1`，再计算

\[
\tilde n_\mathrm{eff}=(f_k n_k^w+f_m\tilde n_m^w+f_a n_a^w)^{1/w}.
\]

作者用 `w_TE=2.5`、`w_TM=−1.5`，是与 FDTD 比较后采用的有效介质权重；不是简单算术平均。TE 电场沿棒轴，TM 电场垂直棒轴。用此 n(z,λ) 做薄膜 TMM，非偏振结果取两偏振平均；有限 N、cap 和空气通道要全部保留。[F20 Eq.1 pp.51–53、Fig.4；F19 §2.6、Fig.4c]

仅算上侧有序堆栈是原论文的反射近似；底侧堆栈和随机内核对反射较小。不要把整根羽小枝上下两侧强制当作同相、厚度完全恒定的 Fabry–Perot 腔；也不要因此宣称透射/吸收已完整验证。[F20 p.56；F19 §3.3]

针对 10–20 mm 近景，建议分两级验收，这是根据证据提出的**渲染验证方案**：

1. 单个局部平面：用 F20 同套结构和色散检查 R2/R4 单峰、R3/R5 双峰、R6 两种谱型及主峰位置；先比较谱形。F20 的幅值经孔径修正，不能以其 y 值作为独立绝对反射率标定。
2. 羽毛片：按照片的疏密、遮挡、细胞倾斜和曲面法线积分，再模拟 D13 的正面观察／30、45、60°侧向照明条件。比较蓝移趋势和不同色区的幅度变化；不能把宏观灯角直接塞进局部镜面 TMM。当这些检查吻合后，再用真实照片检查 1–2 cm 构图中的断续亮纹和色带。

## 4. 实测反射光谱与 CSV

**所有数字化文件都标明“测量曲线的图形提取”，不当作仪器原始计数。** 不同论文的照斑、法线、接收角和白标准不同，跨论文幅值不可强制相等。

|数据文件|对象/曲线|波段与采样|性质与定位|
|---|---|---|---|
|[Kane2019 fraction](data/spectra_Kane2019_eyespot_fraction.csv)、[percent](data/spectra_Kane2019_eyespot_percent.csv)|P. cristatus 眼斑 PB、BB、BG、BZ、GB 五区|300–700 nm，1 nm，401 行|**作者发布数值**；K19 Fig.2D p.4，原始 XLSX 已保存；无额外平滑/插值|
|[Dakin2013 多角度](data/spectra_Dakin2013_Fig2_vector_digitized_percent.csv)|P. cristatus PB/BG/BZ；30/45/60°照明，9 条曲线|300–700 nm，1 nm，401 行|**PDF 矢量数字化实测曲线**；D13 Fig.2 p.1049|
|[Freyer2020 六区探头谱](data/Freyer2020_fig5_probe_measured_5nm.csv)|P. cristatus R1–R6；R6 两条，共7条粗线|305–895 nm，5 nm，长表833行|**JPEG 曲线数字化**；F20 Fig.5 p.57；不提取细 MSP 线|
|[Zi2003 四区](data/Zi2003_fig2A_measured_5nm.csv)|P. muticus 蓝/绿/黄/褐；法向入射 E 沿棒|约425–750 nm，5 nm；各线只在原图有效段采样|**PDF 矢量数字化实测曲线**；Z03 Fig.2A p.12577；不是 Fig.4 模拟谱|
|[Yoshioka2002 角度局部谱段](data/Yoshioka2002_fig2_angular_partial_5nm.csv)|蓝体羽与黄尾覆羽，各8观察角|仅可分辨的局部波段；5 nm，472行|**保守扫描图提取**；Y02 Fig.2 p.172；只作补充，非眼斑、非绝对 R|

### 4.1 优先使用的作者数值：Kane 2019

原始文件位于 [data/spectra_Kane2019_original/](data/spectra_Kane2019_original/)，其中 `Indian peacock eyespot reflectance spectra.xlsx` 来自 [作者 Figshare 数据归档](https://figshare.com/s/688fb19dad98b6273324)。原归档约1.05 GB，本次用 HTTP Range 提取相关 XLSX，**没有声称下载整包**。原表后5列逐点重复前5列的重新排序，不是更多角度或独立样本；整理版删除重复，完整列版仍保留。[K19 Data Availability、Fig.2D；归档清单见 data/spectra_Kane2019_archive_inventory.json]

|色区|数值表逐点最大值 λ nm|峰值 %|
|---|---:|---:|
|PB 紫黑|434|3.50833|
|BB 蓝黑|455|5.05017|
|BG 蓝绿|496|23.92159|
|BZ 铜金|589|18.28732|
|GB 外围绿|555|8.14092|

峰值仅用于复核表格，不是五位有效数字的实验精度。光谱仪分辨率 **2.06 nm FWHM**，作者做过约20 nm窗的 Savitzky–Golay 平滑；积分100 ms、5次平均、3 pixel boxcar，约2 mm照斑，白标准99% PTFE。眼斑样品5根，但发布表不能还原每根的独立误差。[K19 pp.4–5 “Feather samples”、p.7 “Reflectance spectroscopy”]

**角度缺口：** XLSX 和主文没有把 Fig.2D 每条曲线绑定到完整照明/观察/方位角；补图 S2A 只有装置照片。p.8／Fig.4 的太阳方位45°、仰角30°、光源与相机夹角52°属于室外多光谱摄影，不能套作这张反射谱的角度。故 CSV 这组谱不冒充角分辨数据。装置补图文件也已保存到 papers/。[详见光谱证据笔记](data/spectra_notes.md)

### 4.2 真正的蓝孔雀眼斑多角度：Dakin 2013

观察方向固定在宏观羽面法线 **0°**，灯在观察方向右侧30/45/60°；图中实线/长虚线/点线分别对应三种灯角。三色每条曲线是10只雄鸟各1根羽毛的平均。[D13 Fig.1–2，pp.1048–1050]

|色区|30° 灯角：峰位 nm / %|45°：nm / %|60°：nm / %|
|---|---|---|---|
|BG 蓝绿|507 / 39.75|499 / 43.35|487 / 33.52|
|BZ 铜金|650 / 22.84|639 / 30.49|624 / 36.97|
|PB 紫黑|460 / 5.13|453 / 6.80|444 / 8.14|

这里是**宏观羽毛片非镜面测量**；局部倾斜羽小枝仍可满足镜面条件。白参考是叠层 Teflon 胶带，约2 mm光斑、10 scans、100 ms、12 pixel boxcar，每15分钟重新白/暗标定；每色两次卸装取平均。不是积分球总反射率。[D13 p.1050]

直接提取每线401个 PDF 折线顶点，以 y 轴刻度线性标定。保守数字化误差约 **±1 nm、±0.2 个百分点**，不是实验误差。详见 [metadata](data/spectra_Dakin2013_Fig2_digitization_metadata.json)、[原图裁切](data/spectra_Dakin2013_Fig2_source_crop.png)、[CSV 重绘](data/spectra_validation_replot.png)。

### 4.3 Freyer、Zi 和 Yoshioka 的数字化边界

- F20 Fig.5 粗线是约1 mm探头测量，细线是5–10 µm单细胞 MSP。作者因漫反射白板与近镜面羽小枝孔径不匹配，把探头谱**除以约4**；MSP 峰又缩放到探头/模型。CSV 保留论文已修正的纵轴值，**不要再除4**；它更适合谱形检查。[F20 p.51、p.56、Fig.5 p.57]
- F20 的本次提取使用原嵌入1331×710 JPEG，以各面板真实刻度校准，按粗线颜色排除细线。5 nm采样；读图误差保守约 ±3–5 nm、各面板显示满量程的 ±1–2%，不含实验误差。已逐面板检查[叠加图](data/Freyer2020_fig5_digitization_overlay.png)，另存[校准坐标](data/Freyer2020_fig5_digitization_calibration.json)。谱的入射/接收数值角未逐线报告，不标为精确0°镜面谱。
- Z03 Fig.2A 从彩色矢量折线取点，x轴左端425 nm、右端750 nm，y轴0–0.6，保守排版读取误差约 ±1 nm、±0.005 R；绿线从450 nm才有有效数据，不外推。已检查[叠加图](data/Zi2003_fig2A_digitization_overlay.png)。原文 Fig.2B 是甘油浸润、2C 是偏振比较，这两组本次未另转CSV。
- Y02 Fig.2 是固定近法向照明、观察角15、25、35、45、55、65、75、85°；纵轴仅 arbitrary units、无数值刻度。只接受扫描列中8条线都能分开的点，线条合并处留缺。黄色主要保留525–730 nm中可分辨点，蓝色445–545 nm；同面板以15°曲线可采样最高值为1，**不是每条线各归一化**。极大角度的真正峰可能落在未分辨区；[采样最大值表](data/Yoshioka2002_fig2_angular_peaks.csv) 的 `peak_inside_resolved_range=False` 不能当实际峰心。已查看[叠加图](data/Yoshioka2002_fig2_digitization_overlay.png)；该补充谱不用于眼斑绝对反射率拟合。

F19 Fig.2c/d 还给蓝孔雀**颈羽** TE/TM 的0–70°角分辨实测谱，说明局部偏振与蓝移机制；PDF已下载，未将其混为眼斑曲线。O22 Fig.4B 为圆偏振筛选条件下的四色实测谱，PDF已下载，未另数字化。[F19 §3.2；O22 pp.9–10]

## 5. 羽枝、羽小枝、曲率和色环尺度

|所需几何|查到的数值或形状|证据/限制及页图|
|---|---|---|
|羽小枝细胞/节段长|通常20–30 µm|SEM观察；Y02 p.172、Fig.1B；样本非眼斑各环系统采样|
|眼斑深蓝细胞长/羽小枝宽|25.2±3.26 / 34.5±5.33 µm，mean±SD|H24 p.10 Table1、Fig.5；一手SEM本科论文，**非同行评审**|
|眼斑金色细胞长/羽小枝宽|29.4±3.22 / 46.7±2.25 µm，mean±SD|H24 同表；蓝/金取自同一羽枝，表未报独立样本数|
|羽小枝总长、羽枝长|约1 mm；厘米量级|H24 p.11量级描述，非分色区严格统计；不要当精确均值|
|横截面/细胞面|羽小枝为弯曲薄片，横截面新月形；细胞面鞍形|Y02 p.171 Fig.1C、p.172；F20 p.55 Fig.3a，横截面标尺5 µm|
|沿长轴弯曲、扭转|沿长轴弯曲，从根部轻微扭转|Y02 p.172定性观察；未找到可信统一扭角/曲率半径|
|羽小枝内部棒朝向|不应全根严格平行，可能向尖端扇形展开|O18 原摘要；全文未取得，**无可核对的定量扭转角**|
|R1 与其余区朝向|R1远端细胞强烈侧倾，近垂直羽片；R2–R6中/远端较平行羽片|P. cristatus显微实测；F20 Fig.1d–j、pp.59–60。中央黑并非仅由吸收决定|
|眼斑局部疏密、连接|R2密集互相重叠，R3–R6较疏；眼斑有互锁、微钩|F20 Fig.1c/d、p.60；D16 §3.7 p.17、Fig.8F/G p.18|
|羽枝相对羽轴夹角|图中两条局部投影约47°、50°，约±5°|**本次手工读图**，F20 Fig.1b；不是总体三维夹角|
|羽枝间距|F20 Fig.1b显示亚毫米级沿轴节距；未取得统一数值表|只能按同图5mm比例尺逐条布置；羽枝与羽小枝间距不可混用|
|羽枝截面宽/厚、羽小枝横向节距|未找到可靠的目标部位分区统计|不能将纳米晶格常数或细胞长20–30µm当作羽枝间距|
|青铜眼斑整体直径|平均40.5 mm|D16 p.8 §2.5用于视频标定；**不是青铜环的宽度**，该句未给SD/n|

H24 的“Main Stem”行是主轴附近大羽枝的紫色样本，不能把其60.3 µm宽冒充铜色眼斑羽小枝。非同行评审数值在此仅作网格尺寸先验；优先对照有比例尺真显微图。[H24 pp.10–11]

### 色环宽度：一根有标尺羽毛的可复现估计

没有找到蓝孔雀各色环毫米宽的通用测量表。本次按 F20 Fig.1a 的20 mm尺，取**右侧同一水平截线 y=420 px**，换算比例117 px = 20 mm。得到：

|色带|原图 x 范围 px|该水平截线上的投影宽度|
|---|---|---:|
|R2 蓝绿|282–307|约4.3 mm|
|R3 褐/铜|307–331|约4.1 mm|
|R4 绿黄|331–347|约2.7 mm|
|R5 紫|347–359|约2.1 mm|

边界每端约±3px，宽度建议按约 **±1 mm** 处理。这是**本次对一个样本的照片测量**，不是原作者表格，不是总体SD，也不是沿色界法线的环厚度。眼斑上下左右不等宽，R6外界与松散羽枝混合，没有强行给“闭合环宽”。这些尺度说明10–20 mm画幅可跨越几条色带，但应沿实际位置取景。[F20 Fig.1a p.53]

坐标与算术：[geometry_figure_estimates.csv](data/geometry_figure_estimates.csv)、[重算脚本](scripts/measure_geometry_figure.py)。几何完整查证笔记：[geometry_notes.md](data/geometry_notes.md)。

## 6. 已下载真照片与用途

|文件|可核对内容|比例尺/许可|
|---|---|---|
|[完整实验照片组](photos/Freyer_2020_Fig1_cristatus_train_macro_micro_CC-BY-NC-3.0.jpg)|眼斑全貌、边缘与六区真实细胞；目标物种明确|F20 Fig.1；20mm/5mm/1mm/50µm；CC BY-NC 3.0|
|[眼斑原样裁切](photos/Freyer_2020_Fig1a_eyespot_20mm_scale.png)|环形轮廓、羽枝走向；来自同一个体|保留20mm尺；同上|
|[边缘/中心边界显微裁切](photos/Freyer_2020_Fig1cd_barbules_1mm_scales.png)|c为外侧R5附近，d为中心R1/R2；白箭头是原注释|各1mm尺，放大倍数不同；同上|
|[眼斑SEM与互锁](photos/Dakin_2016_Fig8FG_eyespot_SEM_1mm_300um_scales.png)|真实羽小枝连接、微钩；只能校验几何|D16 Fig.8F/G p.18；1mm/300µm；CC BY 4.0|
|[高分辨率实拍眼斑](photos/Mister_rf_2023_Peacock_feather_close-up_CC-BY-SA-4.0.jpg)|3375×2594，外观与构图；非定量颜色校准|Mister rf 2023；无尺；CC BY-SA 4.0；作者说明焦点堆栈与去背景，页面未明确物种|

来源、作者、原下载链接、许可及裁切记录：[photo_sources.csv](data/photo_sources.csv)。实验照片的颜色受灯角、白平衡和成像光路影响；没有将照片RGB当作反射率。F20图片有非商业许可限制，若用于商业发布，应另核权利；D16和Commons图按其各自许可使用。

## 7. 取得范围、阻碍与复核记录

**已取得：** 下表所列11篇不同论文/学位论文PDF、装置补图、带标尺照片、原始数值表、分色区结构CSV、色散CSV和多组反射谱CSV。全部PDF能被解析，已检查相关图页；数字化谱已叠回源图或重绘核对。文件的实际大小、页数和SHA-256见 [artifact_manifest.csv](data/artifact_manifest.csv)。

**仍缺：** Li2005、Jiang2018、Okazaki2018全文PDF，以及Durrer原始解剖专著未取得；Li的APS全文接口返回401或HTML。本报告仅在明确“摘要”或“F20转引”的范围使用它们。没有伪装保存HTML为PDF。可公开取得的F20新模型和目标物种实测谱已覆盖主要建模需求。

**仍不确定：** 各色区独立孔雀材料n,k、全色区局部镜面角扫描、统一羽枝截面与间距、数值化三维扭角和曲率、不同个体的各色环宽统计。已有资料不足以给出这些量的可信固定值；需要针对目标样本做有标尺多视角显微/TEM和测角光谱。现有微距图足以提供可检查的单样本形态依据，但不等于这些统计已测得。



可复现提取：`scripts/digitize_spectra.py`、`scripts/digitize_yoshioka_angles.py`、`data/spectra_prepare.py`、`scripts/measure_geometry_figure.py`。依赖Python、PyMuPDF、NumPy、Pillow；原始XLSX按ZIP/XML读取。提取脚本本身离线。数字化方法详见 [digitization.md](data/digitization.md)。

## 8. 文献索引、PDF与页码映射

下列短标识用于上文每条参数定位；期刊页码优先，电子论文使用正文页码。大学库封面会使PDF页码比正文多1页。

|标识|原始文献与来源|本地PDF、页码映射|
|---|---|---|
|Z03|Zi J et al. 2003. *Coloration strategies in peacock feathers*. PNAS100:12576–12578. [DOI](https://doi.org/10.1073/pnas.2133313100)，[成功下载镜像](https://oww-files-public.sfo3.cdn.digitaloceanspaces.com/3/30/Zi_PeacockColor_PNAS2003.pdf)|[PDF](papers/Zi_2003_PNAS.pdf)；PDF第1页为旧下载封面，正文p12576/12577/12578=第2/3/4页|
|Y02|Yoshioka S, Kinoshita S. 2002. *Effect of Macroscopic Structure in Iridescent Color of the Peacock Feathers*. Forma17:169–181. [期刊](https://forma.katachi-jp.com/abstract/1702/17020169.html)，[成功下载镜像](https://oww-files-public.sfo3.cdn.digitaloceanspaces.com/b/bc/Yoshioka_PeacockMacroStruct_Forma2002.pdf)|[PDF](papers/Yoshioka_Kinoshita_2002_Forma.pdf)；p169=PDF第1页|
|F20|Freyer P, Stavenga DG. 2020. *Biophotonics of diversely coloured peacock tail feathers*. Faraday Discuss.223:49–62. [DOI](https://doi.org/10.1039/D0FD00033G)，[大学库](https://pure.rug.nl/ws/portalfiles/portal/158743733/d0fd00033g.pdf)|[PDF](papers/optics_Freyer_Stavenga_2020_tail.pdf)；p49=PDF第2页；Table1 p52=第5页；Fig5 p57=第10页|
|F19|Freyer P, Wilts BD, Stavenga DG. 2019卷年，2018在线. *Reflections on iridescent neck and breast feathers of the peacock, Pavo cristatus*. Interface Focus9:20180043. [DOI](https://doi.org/10.1098/rsfs.2018.0043)，[大学库](https://pure.rug.nl/ws/portalfiles/portal/118754461/rsfs.2018.0043.pdf)|[PDF](papers/optics_Freyer_2019_neck.pdf)；有大学封面；用章节/图号定位，勿照F20参考文献误写为J.R.Soc.Interface|
|L11|Leertouwer HL, Wilts BD, Stavenga DG. 2011. *Refractive index and dispersion of butterfly chitin and bird keratin measured by polarizing interference microscopy*. Opt. Express19:24061–24066. [DOI](https://doi.org/10.1364/OE.19.024061)，[大学库](https://pure.rug.nl/ws/portalfiles/portal/2532751/2011OptExpressLeertouwer.pdf)|[PDF](papers/optics_Leertouwer_2011_keratin.pdf)；p24065=PDF第6页|
|S15|Stavenga DG et al. 2015. *High refractive index of melanin in shiny occipital feathers of a bird of paradise*. Light Sci.Appl.4:e243. [DOI](https://doi.org/10.1038/lsa.2015.16)，[大学库](https://pure.rug.nl/ws/portalfiles/portal/55684450/lsa201516_1_.pdf)|[PDF](papers/optics_Stavenga_2015_melanin.pdf)；正文p4=PDF第5页|
|O22|Okazaki T. 2022. *Structural Color Expression Due to Specular Reflection from Bird Feathers*. Forma37:5–12. [DOI](https://doi.org/10.55653/forma.2022.001.002)，[原始PDF](https://www.jstage.jst.go.jp/article/forma/37/1/37_5/_pdf/-char/en)|[PDF](papers/optics_Okazaki_2022_specular.pdf)；p5=PDF第1页，p11=第7页|
|K19|Kane SA et al. 2019. *How conspicuous are peacock eyespots and other colorful feathers in the eyes of mammalian predators?* PLOS ONE14:e0210924. [DOI](https://doi.org/10.1371/journal.pone.0210924)，[作者数据](https://figshare.com/s/688fb19dad98b6273324)|[PDF](papers/spectra_Kane_2019_PLOS.pdf)；文内页码=PDF页码|
|D13|Dakin R, Montgomerie R. 2013. *Eye for an eyespot: how iridescent plumage ocelli influence peacock mating success*. Behav.Ecol.24:1048–1057. [DOI](https://doi.org/10.1093/beheco/art045)，[作者论文页](https://www.roslyndakin.com/papers.html)|[PDF](papers/spectra_Dakin_Montgomerie_2013.pdf)；p1048=第1页，Fig2 p1049=第2页；下载来自作者主页链接的Google Drive|
|D16|Dakin R et al. 2016. *Biomechanics of the Peacock's Display: How Feather Structure and Resonance Influence Multimodal Signaling*. PLOS ONE11:e0152759. [DOI](https://doi.org/10.1371/journal.pone.0152759)|[PDF](papers/geom_Dakin_2016_biomechanics.pdf)；文内页码=PDF页码|
|H24|Noe Oberholtzer Hess & Natalia Dushkina. 2024. *Mechanisms and Morphology: An Analysis of Structural Coloration in Peacock Feathers*. Millersville University本科论文. [学校原始PDF](https://millersville.tind.io/record/109962/files/Oberholtzer_2024_Physics_thesis.pdf)|[PDF](papers/geom_Oberholtzer_2024_undergraduate_thesis.pdf)；按印刷p10 Table1、p11定位；非同行评审|

补充但无全文：O18 = Okazaki2018, *Reflectance Spectra of Peacock Feathers and the Turning Angles of Melanin Rods in Barbules*, Zool.Sci.35:86–91，[DOI](https://doi.org/10.2108/zs170091)。它的作者不是Jiang。Li2005和Jiang2018的完整来源见第2节。
