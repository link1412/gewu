# 锡青铜光学数据调研（2026-10-29）

## 结论与最直接来源

**已找到实际测量名义 20 wt.% Sn、10 wt.% Sn、30 wt.% Sn 锡青铜 n,κ 的论文；尚未取得其原始数值表。** 不应把纯 Cu/Sn 混合估算当作这些测量。也未核实到纯 δ / ε 相的独立可见光 n,k 表。**其 κ 使用 Max Born 记号，是标准 extinction coefficient k 除以 n，必须用 k=nκ 转换**。作者公开图可以定位研究，但目前未数字化为可导入 pbrt 的可靠 CSV。

|来源|样品、方法|范围及数据可用性|
|---|---|---|
|Patrick Callet、Anna Zymla，2006，**Rendering of Binary Alloys — Example and Validation with Bronze**，*Computer Vision and Graphics*, Computational Imaging and Vision 32，469–476；[DOI 10.1007/1-4020-4179-9_67](https://link.springer.com/chapter/10.1007/1-4020-4179-9_67)；[作者上传全文](https://www.researchgate.net/publication/226750245_Rendering_of_binary_alloys_-_Example_and_validation_with_bronze)|配制 Cu90Sn10、Cu80Sn20、Cu70Sn30；光谱椭偏 SE；光学抛光金属样品；同实验2005文明确为质量百分数|§3 明确原始采样 **200–1200 nm、1 nm 间隔**；**Fig.1 是 400–750 nm 的 n 与 κ 曲线**。未找到公开原始数值文件；没有把图中曲线伪装为原始数据。Cu80Sn20 是本轮最接近 20–25 wt.% Sn 目标的来源。|
|Patrick Callet，2005，**Virtual Restoration of Bronze — 3D Capture and Optical Simulation in Parallel Spectral Ray-tracing**，ICHIM’05；[公开 PDF](https://www.astrale3d.com/doc/Virtual_Restoration.pdf)；[可读镜像](https://fr.scribd.com/document/624813178/CALLET-Virtual-restoration-of-bronze-3D-capture-and-optical-simulation)|同一中国铜马复原研究；§2.2明确三组Cu–Sn合金（10/20/30 percent in mass concentration），§2.5光谱椭偏，抛光样品；另用激光轮廓仪研究粗糙度|20页；Fig.6为n,κ谱、Fig.12为(n,κ)平面图。§2.5明确 n'=n[1+iκ]。PDF直抓失败，但镜像正文核实了上述组成与定义；未声称已下载原文或数表。未找到 DOI。|
|Patrick Callet，2013，**Spectral Simulation for Cultural Heritage: A Scientific Methodology and Some Examples**，Colour Group (Great Britain)；[完整32页 PDF](https://www.colour.org.uk/wp-content/uploads/2020/02/CalletSpectralSimulation-final-min.pdf)|第12页（PDF第14页）确认 Cu、Sn、10/20/30% Sn 三种合金共5样，经 SE 获得常数，SEM 检查；样品由 Anna Zymla 制备|是同一实验系列的作者独著交叉核实。文中说明采用**复介电函数插值**，并非直接插颜色、反射率或 n,k。无独立数值表，不能当作新的实测数据集。|

**κ 定义已核实，不能直接当作 pbrt 的 k：** 2006 Fig.1 κ纵轴0–30不是标准虚部k的直接量级。2005 §2.5及2013专著第2页（PDF第4页）Eq.(3)明确：`n'(λ)=n(λ)[1+iκ(λ)]`，后文说明虚部为`nκ`。故转换为常用`n+ik`时 **k(λ)=n(λ)κ(λ)**。另有同作者 [Metals, Alloys and Lighting](https://www.researchgate.net/publication/339447764_METALS_ALLOYS_AND_LIGHTING_OPTICAL_PROPERTIES_AND_SPECTRAL_SIMULATION_IN_COMPUTER_GRAPHICS) Fig.1图注明确`K=k/N`交叉核实。这个来源的ResearchGate日期标2010，其他作者参考文献列CIE x032:2007；引用定义时首选2013专著，避免猜日期。需要数字化时应对同一波长的n与κ分别提取再相乘，并把图读误差传播；本轮不生成这种低精度谱。

## 高锡 speculum 的反射谱

1. **S. Tolansky、W. K. Donaldson，1947，The Reflectivity of Speculum Metal，Journal of Scientific Instruments 24(9),248–249**。[DOI 10.1088/0950-7671/24/9/308](https://iopscience.iop.org/article/10.1088/0950-7671/24/9/308)；[原论文摘要记录](https://www.researchgate.net/publication/231146129_The_Reflectivity_of_Speculum_Metal)。测量电沉积、抛光的约45% Sn 铜锡镜面及真空蒸发到玻璃的同组成镜面，450–650 nm；摘要给出新抛光电沉积样 R(450)=0.63、R(650)=0.75；蒸发样分别0.68、0.78。摘要说潮湿环境6个月后红/蓝端下降10%/2%，这里不假定是百分点还是相对值。没有 n,k；没有确认入射角，因此**不能冒称已核实法向谱**。ResearchGate 的“2002”日期错误；1947 由期刊卷号及[作者档案](https://archives.libraries.london.ac.uk/resources/MS827.pdf)交叉核实。四个摘要明载端点已人工转录至 [data/speculum_Tolansky_Donaldson_1947_abstract_endpoints.csv](data/speculum_Tolansky_Donaldson_1947_abstract_endpoints.csv)，不是下载的完整原始光谱，不插值。

2. **E. A. Nazimudeen、T. E. Girish、Sunila Abraham，2018，On the Nature of Thin Films of Speculum Metal，Materials Today Communications 16,314–319**。[DOI 10.1016/j.mtcomm.2018.07.005](https://doi.org/10.1016/j.mtcomm.2018.07.005)；[出版社全文摘要/段落](https://www.sciencedirect.com/science/article/pii/S2352492818301302)。传统 Aranmula 铸造/磨光镜，及其热蒸发薄膜；UV–Vis 反射谱，EDS/XRD/AFM。EDS 报告表面 Cu 约62–69%、Sn约30–32%，另有 Zn/As/Pb 等微量组分；薄膜反射率高于铸件。**不是20–25% Sn**。已定位到实测反射谱研究，但公开可读摘录未给确切扫描上下限、角度或数值表，未捏造范围。全文需机构访问。

3. **E. A. Nazimudeen 等，2023，Effects of high energy electron and X-ray irradiation on the morphology, microstructure and reflectivity of cast speculum metal mirror，Radiation Physics and Chemistry 202,110503**。[DOI 10.1016/j.radphyschem.2022.110503](https://www.sciencedirect.com/science/article/pii/S0969806X22005394)。提供同类铸造 speculum 照射前/后 UV–Vis 反射、AFM 与 XRD，电子照射6/9 MeV、X射线6/10 MeV；不应把硬 X 射线反射率当作可见光反射率。未取得原始数值表与确切可见扫描区间。

## 补充椭偏来源与适用性边界

- **A. A. Wronkowska、G. Czerniak、A. Wronkowski、Ł. Skowroński，2013，Optical and microstructural characterisation of Au–Sn and Cu–Sn diffusive layers，Applied Surface Science 281,30–37**。[DOI 10.1016/j.apsusc.2013.01.115](https://www.sciencedirect.com/science/article/abs/pii/S0169433213001633)。真空顺次蒸发/共蒸发到玻璃，Cu底层20 nm，调Sn厚度至原子比1:1；VASE + 透过谱，0.6–6.5 eV（约190.7–2066.4 nm），Drude–Lorentz 拟合有效复介电函数。Sn/Cu双层出现Cu6Sn5，共蒸发膜出现Cu10Sn3；这是**超薄、多相扩散膜的有效光学响应**，不是Cu3Sn纯相，也不是考古高锡镜块材。未取得全文参数表/原始表。
- **Jelena Wohlwend、Alla S. Sologubenko、Max Döbeli、Henning Galinski、Ralph Spolenak，2022（2021在线），Chemical Engineering of Cu–Sn Disordered Network Metamaterials，Nano Letters 22(2),853–859**。[DOI 10.1021/acs.nanolett.1c03545](https://pubs.acs.org/doi/10.1021/acs.nanolett.1c03545)。出版社明确列出 [SI PDF](https://pubs.acs.org/doi/suppl/10.1021/acs.nanolett.1c03545/suppl_file/nl1c03545_si_001.pdf)（nl1c03545_si_001.pdf，8.9MB）含“measured optical constants”。体系是Al–Cu–Sn共溅射后去Al的纳米网络，未成功打开SI，故尚不能确定其中测量的是纯金属致密膜、合金膜还是网络有效常数；**列作待取数的线索，不列作铜镜nk表**。
- **R. J. Nastasi-Andrews、R. E. Hummel，1977，Optical properties and electronic structure of dilute Cu-Au, Cu-Zn, Cu-Al, Cu-Ga, Cu-Si, Cu-Ge, Cu-Sn, and Cu-As alloys，Physical Review B 16,4314**。[DOI 10.1103/PhysRevB.16.4314](https://journals.aps.org/prb/abstract/10.1103/PhysRevB.16.4314)。α相稀合金差分反射测量，目标是带间跃迁阈值；摘要没有完整绝对R/n/k及组成/扫描上下限，不宜称为可用5–15% Sn光谱。
- **Pedemonte M.; Spotorno R.; Magnozzi M.; Criaco C.; Lupi C.; Sforzini; Piccardo P.，Traces of Fire: Macroscopic Colour as a Marker of Composition and Non-Equilibrium in Cu–Sn Bronzes**，[热那亚大学机构记录](https://unige.iris.cineca.it/handle/11567/1321665)，状态为“In corso di stampa”（待出版）。摘要明确1–16 wt.% Sn、铸态/均匀化态，SE测n,k，另11 wt.%研究冷却速率与微偏析。但记录**无附件、无期刊/年份/DOI及波段**，不能算已经交付的数值数据；适合后续追踪。

## 必须纠正的组成/相解释

“约20–25 wt.% Sn 的铜镜”“speculum”“纯δ相”“纯ε相”并非同一成分。由式量算（Cu=63.546、Sn=118.710）：Cu31Sn8约32.53 wt.% Sn；Cu41Sn11约33.39 wt.% Sn；Cu3Sn约38.37 wt.% Sn。20–25 wt.% Sn 块材可包含富Cu相与高Sn金属间化合物，热历史、表面富锡/腐蚀和相分数均可能改变实测结果。现代相图表将δ写成Cu41Sn11、ε写成正交Cu3Sn；见 **S. Fürtauer et al.,2013,The Cu–Sn phase diagram, Part I: New experimental results,Intermetallics 34,142–147**，[PMC作者全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4819024/)。不要仅因标题有Cu3Sn就把γ相立方理论模型当作ε相光学实测。

## 搜索与取数边界

本轮公开检索没有发现已核实可下载的 Cu–Sn 二元合金完整 n,k 原始表，也未核实 refractiveindex.info 有锡青铜条目；其 Cu–Zn 黄铜数据不能替代 Cu–Sn。不能从单条法向 R(λ) 唯一反演两个未知函数 n(λ)、k(λ)。已明确区分：实测原表、论文曲线、作者模型/插值和未读取的线索。
