# 光学常数及后续模型查证笔记

检索/下载日期：2026-11-02。

## 关键判断

首选蓝孔雀眼斑的物理材质基线是 Freyer & Stavenga 2020，而不宜直接将 Zi 2003 的全部表格冠名为 Pavo cristatus。Zi 2003 原文明确是 **Pavo muticus**；Freyer 2020 方法 p50 明确采集 **Pavo cristatus 尾羽**，测六个眼斑色区。Yoshioka 2002 比较蓝色体羽（后文 2019/2020 特指颈/胸）和黄色尾覆羽，不能将其蓝羽角度数据无条件当眼斑蓝环。

## 下载论文及原始链接

|本地文件|论文/主来源|DOI / 下载链接|页码说明|
|---|---|---|---|
|`papers/optics_Freyer_Stavenga_2020_tail.pdf`|Freyer P, Stavenga DG. Biophotonics of diversely coloured peacock tail feathers. Faraday Discussions 223,49–62 (2020)|[DOI](https://doi.org/10.1039/D0FD00033G), [大学库原版 PDF](https://pure.rug.nl/ws/portalfiles/portal/158743733/d0fd00033g.pdf)|PDF 第1页为大学封面；期刊 p49 对应 PDF第2页；Table1 p52 对应PDF第5页|
|`papers/optics_Leertouwer_2011_keratin.pdf`|Leertouwer HL, Wilts BD, Stavenga DG. Refractive index and dispersion of butterfly chitin and bird keratin measured by polarizing interference microscopy. Optics Express 19,24061–24066 (2011)|[DOI](https://doi.org/10.1364/OE.19.024061), [大学库 PDF](https://pure.rug.nl/ws/portalfiles/portal/2532751/2011OptExpressLeertouwer.pdf)|PDF有1页大学封面；p24065=PDF第6页|
|`papers/optics_Stavenga_2015_melanin.pdf`|Stavenga DG, Leertouwer HL, Osorio DC, Wilts BD. High refractive index of melanin in shiny occipital feathers of a bird of paradise. Light: Science & Applications 4,e243 (2015)|[DOI](https://doi.org/10.1038/lsa.2015.16), [大学库 PDF](https://pure.rug.nl/ws/portalfiles/portal/55684450/lsa201516_1_.pdf), [正文](https://www.nature.com/articles/lsa201516)|PDF第1页大学封面；正文第4页=PDF第5页|
|`papers/Yoshioka_Kinoshita_2002_Forma.pdf`|Yoshioka S, Kinoshita S. Effect of Macroscopic Structure in Iridescent Color of the Peacock Feathers. Forma17,169–181 (2002)|[期刊](https://forma.katachi-jp.com/abstract/1702/17020169.html), [成功下载的论文镜像](https://oww-files-public.sfo3.cdn.digitaloceanspaces.com/b/bc/Yoshioka_PeacockMacroStruct_Forma2002.pdf)|无封面；p169=PDF第1页。期刊直链PDF在本环境曾返回非PDF内容；镜像为完整3MB论文|

2019 交叉验证论文：Freyer P, Wilts BD, Stavenga DG. Reflections on iridescent neck and breast feathers of the peacock, Pavo cristatus. **Interface Focus**9,20180043，DOI [10.1098/rsfs.2018.0043](https://doi.org/10.1098/rsfs.2018.0043)。在线2018-12-14，期刊卷年2019。不要照抄2020参考文献中误写的 J.R.Soc.Interface；正确刊名见 [PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC6304014/)。大学库PDF路径 [下载](https://pure.rug.nl/ws/portalfiles/portal/118754461/rsfs.2018.0043.pdf)。

## 1. 推荐复折射率：有物种/方法限定的测量反演

波长 λ 一律以 **nm** 输入。

- 角蛋白：`n_k(λ)=1.532+5890/λ²`；可见光 `k_k≈0` 是透明角蛋白建模假设（非独立测得恰好为0）。Leertouwer2011 白鹅无色羽小枝 Jamin–Lebedeff 偏振干涉显微测量及Cauchy拟合，原文 p24065、Fig2B、Fig3；A=1.532±0.001、B=(5.89±0.21)×10³ nm²。**注意原文 B 不确定度是210 nm²；2015复述成20 nm²，与原测量论文不同。** 2011测量波长390、451、494、546、588、650、715nm（p24064）；本交付CSV只取400–700nm。
- 黑色素：`n_m(λ)=1.648+23700/λ²`，`k_m(λ)=0.56 exp(−λ/270)`。Stavenga2015正文p4、Fig3b/c；A=1.648±0.003、B=(2.37±0.14)×10⁴ nm²、a=0.56±0.01、b=270±5nm。材料来源是**劳氏六线风鸟 Parotia lawesii 的枕部羽毛**，而非孔雀；完整羽小枝干涉折射率测量结合TEM中黑色素/角蛋白约各一半的假设反推出黑色素本征常数。k由透射谱同样反演；因此是有体积分数假设的测量推导，不能称为蓝孔雀分离黑色素的直接椭偏测量。
- 同样公式明确用于 P.cristatus：Freyer2019 §2.6，2020 pp51–53 Eq1。2019用EMM和FDTD比较、实测角分辨反射谱比较验证；2020对六个尾羽色区拟合验证。构成推荐使用的决定性依据。
- 2019/2020写 `ñ=n−ik`，取正k表示吸收；若渲染器/求解器使用 `exp(−iωt)` 常用 `n+ik` 则要按其约定换符号，不能把正k输入为增益。CSV的k列记录**正消光系数**。
- 旧模型n_m=2.0的数值在Zi/Yoshioka中为假设，2015正文p4及结论明确指出缺乏实验依据、明显高于其测量反演的1.7–1.8。若复现旧论文用旧n，若建立当前基线用色散式；不要混合旧参数和新n而声称逐点复现旧光谱。

`data/optical_constants_400_700nm_5nm.csv` 为上述**拟合函数的解析采样**（61个点，每5nm），不是数字化实测点。数例：

|λ nm|n_k|n_m|k_m|
|---:|---:|---:|---:|
|400|1.568813|1.796125|0.127288|
|450|1.561086|1.765037|0.105770|
|500|1.555560|1.742800|0.087890|
|550|1.551471|1.726347|0.073032|
|600|1.548361|1.713833|0.060686|
|650|1.545941|1.704095|0.050427|
|700|1.544020|1.696367|0.041902|

Yoshioka2002 p179 §4.4：蓝羽633nm透过率约10%，并在假设黑色素均匀分布、所有透射损耗由吸收造成下粗估虚部量级0.01i；这不是分离黑色素n,k光谱，不能与2015的本征k直接同类比较。Yoshioka p176用空气n=1、melanin n=2.0实数计算平均光程。

## 2. P.cristatus 尾羽六区：2020拟合模型参数

定义以2020 Fig4a p55为准：a 是沿入射/深度方向的层周期；b 为皮质表面横向中心间距；Dm是棒直径（非半径）；Da是空气通道直径；c为外层角蛋白皮质厚度；Nm是黑色素棒层数（不是总介质薄层数）。作者将模型按深度切成1nm片层；Nm=5同时有4层空气通道。保留空气相十分重要，非简单黑色素/角蛋白二元块状膜。

**下表全是 Table1 p52 的 Model 行，受解剖数据约束的光谱拟合，不是逐根直接测量。** 已转为 `data/Freyer2020_model_parameters.csv`。

|区/外观|a nm|b nm|c nm|Dm nm|Da nm|Nm|特殊上层|
|---|---:|---:|---:|---:|---:|---:|---|
|R1 黑紫|140|150|100|100|33|10|常规|
|R2 蓝绿|160|170|100|110|33|9|常规|
|R3 褐|190|150|70|110|50|5|本论文Model行**无**星号，保留首层空气|
|R4 绿黄|195|150|130|120|55|5|常规|
|R5 紫|185|190|140|100|70|3|首个a=240nm；省略第一层空气通道|
|R6 黄铜绿 单峰模型1|185|160|130|120|70|4|省略第一层空气通道|
|R6 黄铜绿 双峰模型2|185|160|150|100|70|3|首个a=240nm；省略第一层空气通道|

**c的极重要限制**：2020 p57写 Pavo 属没有现成解剖皮质厚度测量，c从匹配实测谱估计。Table1中Durrer行70–130nm和100–160nm的c范围来自**刚果孔雀 Afropavo congensis**（Durrer & Villiger1975），不能写成蓝孔雀的实测皮质厚度。2019 §2.5也明确 c=110nm 借用刚果孔雀蓝紫羽小枝平均。Table1的Durrer合并行还引用多篇原文；只按引用汇编列出，未在本子任务逐篇核对物种。

2020 Table1中的解剖范围（由该文汇编，原始Durrer论文非全部直接复核）：

|区|来源|a nm|b nm|Dm nm|Da nm|Nm|
|---|---|---|---|---|---|---|
|R1黑紫|Durrer4,5,37|150–170|140–165|100–110|33|9–11|
|R1黑紫|Jiang2018|128–151|116–134|113–126|30–40|9–11|
|R2蓝绿|Durrer4,5|157–175|150–190|100–120|未给|9–10|
|R2蓝绿|Jiang2018|153–178|112–131|106–119|52–63|5–8|
|R3褐|Durrer4,5|198–223|135–172|100–120|未给|5–7|
|R4绿黄|Durrer4,5,37|190–220|115–190|100–130|55|4–6|
|R5紫|Durrer4,5|180–228|160–250|110–130|未给|4–7|
|R6黄铜绿|Durrer4,5|180–240|140–180|110–135|未给|3–6|

机读表：`data/Freyer2020_anatomical_ranges_secondary_compilation.csv`。Jiang等2018文题 Mechanochromic response of the barbules in peacock tail feather, Optical Materials75,74–78, DOI [10.1016/j.optmat.2017.08.024](https://doi.org/10.1016/j.optmat.2017.08.024)，此处只通过2020原始研究的明确表格引用，不冒称已直接检查其TEM/SEM原文。

## 3. 多层膜与二维结构的实现含义

2020 Eq1 pp51–53：先由各1nm深度切片的体积分数fk+fm+fa=1，计算

`n_eff=(f_k n_k^w+f_m ñ_m^w+f_a n_a^w)^(1/w)`，空气n=1。

作者用 w_TE=2.5，w_TM=−1.5；不是朴素各向同性线性平均，也不是把2D棒直接丢弃。理想两相有效介质理论w=2、−2，但2019与FDTD对照后改为2.5、−1.5，2020沿用（p53）。TE电场平行黑色素棒轴，TM垂直（2019 Fig4c）；未偏振谱=(R_TE+R_TM)/2。几何法线应随羽小枝细胞的弯曲/鞍形表面变化，反射谱以局部入射角计算。

2020 p56、2019 §3.3/S2：仅模拟上侧光子堆栈已能近似反射谱；下侧堆栈/随机内核影响相对很小。若强制把上下两套结构当完美相干10µm薄膜，会有实验看不到的细密振荡；真实厚度变化与核内随机结构破坏相位。此简化适合反射，不适合声称整个羽小枝吸收/透射也完全等同。

2020 pp59–60：有限层数时首层周期、第一空气层有无及c可改变单双峰；层数多则趋于单峰。各参数有相关性，单一反射谱不足以唯一反演所有几何。色素n=2旧模型和色散新模型参数不得任意互换。

## 4. 实测谱/角度证据与幅值限制

2020 Fig5（p57）六色：粗线为分叉光纤探头、细线为单羽小枝细胞MSP。R1~450nm；R2~500nm；R3双峰~530、660nm；R4~600nm；R5双峰~450、620nm；R6同区可共存单双峰（p56、Fig5/6）。这些是论文给的近似峰位置，不是另行精确数字化结果。

2020 p51：光纤照明面积直径约1mm（p56）；MSP为5–10**µm**见方、20×NA0.45；玻璃物镜使MSP限>360nm。其白色漫反射参考板不匹配羽小枝近镜面反射角分布，作者估计探头反射率大约高4倍，故所示探头谱**除4**；MSP峰值又缩放到探头和模型。该图纵轴不可视为独立可溯源的绝对半球反射率，更适合比较谱形/峰位。表面密度、空隙、曲率造成探头与单细胞幅值不同。

2020 Fig2 p54：真正尾羽眼斑R2和R3的成像散射测量；单细胞小照斑近镜面，照斑放大后角分布变宽。此图是角分布照片，不是一组各入射角反射光谱。

2019 Fig2c,d：P.cristatus**颈羽**实测TE/TM角分辨谱，入射角0–70°，入射面平行羽轴；随着入射角增加谱蓝移，TE强度增，TM先减至约60°再增（§3.2）；Fig6与FDTD/EMM比较。MSP反射幅值按模型峰缩放（§2.3）。用来验证光学机制及角度趋势，但不得称为眼斑各色角度真值。论文数据可用性声明没有附加原始数据；补充PDF是模型图，不是CSV。

Yoshioka2002 Fig2 p172：蓝、黄羽随观察角变化反射谱；p172棒径蓝130nm/黄140nm，层间距150/190nm，层数8–12/3–6。蓝FWHM约110nm、黄约170nm（p173）；模型尺寸分别15×8、15×4（p178）。这些层数后者是作者选的有限阵列计算尺寸，不要混为解剖统计。

## 5. Li2005获取状态及可确认范围

Li Y, Lu Z, Yin H, Yu X, Liu X, Zi J. Structural origin of the brown color of barbules in male peacock tail feathers. Physical Review E72,010902(R),4页 (2005)，[DOI](https://doi.org/10.1103/PhysRevE.72.010902)，[APS摘要](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.72.010902)，[PubMed](https://pubmed.ncbi.nlm.nih.gov/16089929/)。APS全文PDF入口未能下载（harvest接口401；link.aps返回HTML），本目录未伪装保存HTML为PDF。

可由原始摘要确认：褐色主要为结构色；深度/层周期、周期数、靠表面两层间距及缺失孔会改变褐色。更详细参数仅由Freyer2020 Table1直接可复核：Li行a=185nm，首周期235nm；b=150nm，Dm=120nm，Da=75nm，Nm=6且省略首空气层。这是**2020对Li的二手汇编**，不能声称本次已直接核对Li2005某页图值或物种。2020新褐色模型并不照搬：其R3用a190nm、Nm5、无省略首空气层，与Li旧模型要分开。

## 可直接用于报告的限制

没有找到分色区独立测得的蓝孔雀n,k色散；纳米结构改变颜色，材料色散通常对色区统一。当前可运行物理基线是从他种测量推导出的色散式、在P.cristatus尾羽实测谱检验的六区TMM拟合参数，而不是“所有参数均为蓝孔雀直接实测”。最新2026预印本文题 Modulation of Avian Iridescence via Melanogenesis 检索中出现，未纳入未经核查数值。

## 6. 追加查到的2022直接TEM皮质测量（更新2020的历史缺口）

**不能把2020“没有Pavo皮质解剖数据”的话写成截至2026仍然没有。** 已下载并目视核对 [Okazaki2022, Structural Color Expression Due to Specular Reflection from Bird Feathers, Forma37,5–12, DOI10.55653/forma.2022.001.002](https://doi.org/10.55653/forma.2022.001.002)，原始开放PDF：[J-STAGE](https://www.jstage.jst.go.jp/article/forma/37/1/37_5/_pdf/-char/en)，本地 `papers/optics_Okazaki_2022_specular.pdf`（8页无封面），p5 §2.1明确Pavo cristatus尾羽。p6 §2.5明确从TEM量外表面到第一黑色素层表面、第二层表面、空腔表面的距离。p11提供：

|其图4分区|外观|皮质外表面→第一黑色素表面 nm|其他实测深度 nm|层数（p10）|
|---|---|---|---|---|
|a|黑色中心|62±6.70|→第二黑色素层202±5.26|2–3|
|b|蓝|96±5.66|→第一空腔216±23.3|11–12|
|c|浅褐|136±12.8|→第二黑色素层419±16.3|5–6|
|d|绿|144±13.2|→第一空腔296±16.0|7–8|

上述单位、数字已对PDF p11实际渲染图核对；±类型和皮质厚度的独立样本数原文该段未说明，因此不自称SD/SEM，不冒称总体统计。图4C/D（p10）有对应横/纵TEM和1µm尺。p11 Table1另给黑色素颗粒间距n=5（注意这个n=5**仅表中间距量测**，不必然指皮质厚度）：a135±17.7、b189±21.4、c179±32.4、d202±21.5nm。该“间距d”用于三维胶体式Bragg估算，**不直接等同Freyer二维模型的深度a或横向b**。

该文p7/p11的n_m=1.7、n_k=1.6、n_air=1.0是模拟采用的常数；没有新的复折射率测量，不应替代2011/2015色散。p9 Fig4B是圆偏振入射/分析器选择下实测反射谱，约45°照明，不是正常入射无偏振；a中心~420nm小峰，b蓝~440nm，c浅褐~460/570nm，d绿~410/500nm（p8–10）。作者另以Fresnel薄膜和Bragg近似对照，不能描述为完整2D传递矩阵求解。

对推荐的影响：蓝区直接实测皮质96nm与Freyer拟合100nm相近；绿144nm与130nm同量级。褐区直接实测136nm与Freyer拟合70nm不一致，中心层数2–3与Freyer黑紫模型10也不同。两文眼斑分区、样本及光照不同，**保留两套各自自洽参数和谱，不能为“凑平均”把2022的c直接换入2020模型而声称验证完成**。2022新增皮质测量对先验范围有价值，2020仍是六区完整EMM+色散匹配的现成模型基线。

2018 Okazaki另一篇 [Reflectance Spectra of Peacock Feathers and the Turning Angles of Melanin Rods in Barbules, Zoological Science35,86–91, DOI10.2108/zs170091](https://doi.org/10.2108/zs170091)，[原文摘要](https://pubmed.ncbi.nlm.nih.gov/29417896/)指出黑色素棒向羽小枝尖端呈扇形展开，而非全羽小枝严格平行；蓝480、暗蓝420、黄绿430/540、褐490/610nm（摘要近似峰值）。此题作者是Okazaki，非Jiang。仅核摘要；2018全文尚未取得，不能给未见的扭转角数值。Jiang2018原始ScienceDirect公开方法摘录已确认SEM来自P.cristatus眼斑蓝/绿/褐，DOI10.1016/j.optmat.2017.08.024；全文仍付费。

另：主任务发现Freyer2020 Table1的Zi2003转录行疑似将黄/褐层数对调。应以Zi原文p12577/Fig4（黄6、褐4）为准，不能将2020汇编的Zi行当独立测量。本笔记的2020拟合Model行和原始Durrer/Jiang来源行均已分开，不依赖该Zi转录。
