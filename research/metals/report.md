# 金属光学常数与鎏金铜器近照

调研日期：2026-10-29。本文面向 pbrt-v4 / Blender Cycles 的材料取数，区分实测谱、受实测约束的模型、图中曲线和仅定位到的文献。

## 先读结论与文件

推荐以**已测合金光谱决定光谱响应，以实测层厚和形貌决定表面结构**；资料缺口保留为建模假设。不要用黄铜代锡青铜，也不要把 AFM 高度 rms 直接填进无量纲 roughness。

| 请求 | 本次找到的最有用结果 | 本地交付 / 缺口 |
|---|---|---|
| 高锡、低锡青铜 | Callet–Zymla 的抛光 10、20、30 wt.% Sn 光谱椭偏；原测 200–1200 nm，公开图 400–750 nm | 原始 n、κ 数表未取得；作者记号需 **k=nκ**。没有用纯金属混合或图读伪造数据。 |
| 火镀金 / Au–Hg | 工匠火镀金 400–700 nm 相对反射实验、EDS 残汞、SEM 层厚、AFM rms；汉代实物 FIB 微结构；另有 Au–Hg 椭偏论文 | 保存 32 条成分/形貌标量；未找到可直接导入的火镀金 n、k 表。相对反射不能当绝对 R。 |
| Cu₂O、CuO | Palik 表可见段；原作者另公开 REELS 数字 XLSX；还有 Cu₂O 单晶 SE | 两份 CSV，各15节点，300–1000 nm；Palik 公开镜像已核查文件头，原始测量方法仍有未核实项。作者 XLSX 下载受阻。 |
| 金银合金 | Rioux 椭偏拟合解析模型；Peña-Rodríguez 另有实测数据 ZIP | 11份模型 CSV，各931节点，270–1200 nm；作者实测 ZIP 已定位但下载受阻。未覆盖含铜三元金箔。 |
| 原图与显微图 | 9个已知像素的馆藏原文件入口，含4张约3.9K–6.8K TIFF；另有7个馆方视图、2个论文显微图网页 PNG | [download.txt](download.txt) 每行一个链接，共18项；原图下载、重定向及放大检查未完成。具体授权及核查范围见第5组。 |

数值文件在 [data/](data/)，原始文本在 [sources/](sources/)，下载来源与 Git blob SHA 在 [sources/provenance.json](sources/provenance.json)。共 **16个 CSV**：13份 n、k 光谱、1份4点反射率转录、2份实测标量/厚度转录。光谱 CSV 使用 `wavelength_nm,n,k`，均为标准 n+ik。这里没有把重采样说成提高测量分辨率。

文件清单：

- [Cu₂O n、k](data/Cu2O_Palik_visible_nk.csv)、[CuO n、k](data/CuO_Palik_visible_nk.csv)。
- `data/AuAg_Rioux-Au*Ag*_model.csv`：11组，具体链接列在第4组。
- [Speculum 四个反射率端点](data/speculum_Tolansky_Donaldson_1947_abstract_endpoints.csv)：手工转录摘要，非完整光谱。
- [火镀金32条实测标量](data/gilding_measured_scalars.csv)：带 DOI、方法、条件和原文位置。
- [赤铜矿层10条厚度记录](data/cuprite_layer_thickness_measured.csv)：含户外青铜、历史铜材与外观阈值，区分范围和标准差。

## 1. 锡青铜：实测常数与磨光镜反射谱

### 结论与最直接来源

**已找到实际测量名义 20 wt.% Sn、10 wt.% Sn、30 wt.% Sn 锡青铜 n,κ 的论文；尚未取得其原始数值表。** 不应把纯 Cu/Sn 混合估算当作这些测量。也未核实到纯 δ / ε 相的独立可见光 n,k 表。**其 κ 使用 Max Born 记号，是标准 extinction coefficient k 除以 n，必须用 k=nκ 转换**。作者公开图可以定位研究，但目前未数字化为可导入 pbrt 的可靠 CSV。

|来源|样品、方法|范围及数据可用性|
|---|---|---|
|Patrick Callet、Anna Zymla，2006，**Rendering of Binary Alloys — Example and Validation with Bronze**，*Computer Vision and Graphics*, Computational Imaging and Vision 32，469–476；[DOI 10.1007/1-4020-4179-9_67](https://link.springer.com/chapter/10.1007/1-4020-4179-9_67)；[作者上传全文](https://www.researchgate.net/publication/226750245_Rendering_of_binary_alloys_-_Example_and_validation_with_bronze)|配制 Cu90Sn10、Cu80Sn20、Cu70Sn30；光谱椭偏 SE；光学抛光金属样品；同实验2005文明确为质量百分数|§3 明确原始采样 **200–1200 nm、1 nm 间隔**；**Fig.1 是 400–750 nm 的 n 与 κ 曲线**。未找到公开原始数值文件；没有把图中曲线伪装为原始数据。Cu80Sn20 是本轮最接近 20–25 wt.% Sn 目标的来源。|
|Patrick Callet，2005，**Virtual Restoration of Bronze — 3D Capture and Optical Simulation in Parallel Spectral Ray-tracing**，ICHIM’05；[公开 PDF](https://www.astrale3d.com/doc/Virtual_Restoration.pdf)；[可读镜像](https://fr.scribd.com/document/624813178/CALLET-Virtual-restoration-of-bronze-3D-capture-and-optical-simulation)|同一中国铜马复原研究；§2.2明确三组Cu–Sn合金（10/20/30 percent in mass concentration），§2.5光谱椭偏，抛光样品；另用激光轮廓仪研究粗糙度|20页；Fig.6为n,κ谱、Fig.12为(n,κ)平面图。§2.5明确 n'=n[1+iκ]。PDF直抓失败，但镜像正文核实了上述组成与定义；未声称已下载原文或数表。未找到 DOI。|
|Patrick Callet，2013，**Spectral Simulation for Cultural Heritage: A Scientific Methodology and Some Examples**，Colour Group (Great Britain)；[完整32页 PDF](https://www.colour.org.uk/wp-content/uploads/2020/02/CalletSpectralSimulation-final-min.pdf)|第12页（PDF第14页）确认 Cu、Sn、10/20/30% Sn 三种合金共5样，经 SE 获得常数，SEM 检查；样品由 Anna Zymla 制备|是同一实验系列的作者独著交叉核实。文中说明采用**复介电函数插值**，并非直接插颜色、反射率或 n,k。无独立数值表，不能当作新的实测数据集。|

**κ 定义已核实，不能直接当作 pbrt 的 k：** 2006 Fig.1 κ纵轴0–30不是标准虚部k的直接量级。2005 §2.5及2013专著第2页（PDF第4页）Eq.(3)明确：`n'(λ)=n(λ)[1+iκ(λ)]`，后文说明虚部为`nκ`。故转换为常用`n+ik`时 **k(λ)=n(λ)κ(λ)**。另有同作者 [Metals, Alloys and Lighting](https://www.researchgate.net/publication/339447764_METALS_ALLOYS_AND_LIGHTING_OPTICAL_PROPERTIES_AND_SPECTRAL_SIMULATION_IN_COMPUTER_GRAPHICS) Fig.1图注明确`K=k/N`交叉核实。这个来源的ResearchGate日期标2010，其他作者参考文献列CIE x032:2007；引用定义时首选2013专著，避免猜日期。需要数字化时应对同一波长的n与κ分别提取再相乘，并把图读误差传播；本轮不生成这种低精度谱。

### 高锡 speculum 的反射谱

1. **S. Tolansky、W. K. Donaldson，1947，The Reflectivity of Speculum Metal，Journal of Scientific Instruments 24(9),248–249**。[DOI 10.1088/0950-7671/24/9/308](https://iopscience.iop.org/article/10.1088/0950-7671/24/9/308)；[原论文摘要记录](https://www.researchgate.net/publication/231146129_The_Reflectivity_of_Speculum_Metal)。测量电沉积、抛光的约45% Sn 铜锡镜面及真空蒸发到玻璃的同组成镜面，450–650 nm；摘要给出新抛光电沉积样 R(450)=0.63、R(650)=0.75；蒸发样分别0.68、0.78。摘要说潮湿环境6个月后红/蓝端下降10%/2%，这里不假定是百分点还是相对值。没有 n,k；没有确认入射角，因此**不能冒称已核实法向谱**。ResearchGate 的“2002”日期错误；1947 由期刊卷号及[作者档案](https://archives.libraries.london.ac.uk/resources/MS827.pdf)交叉核实。四个摘要明载端点已人工转录至 [data/speculum_Tolansky_Donaldson_1947_abstract_endpoints.csv](data/speculum_Tolansky_Donaldson_1947_abstract_endpoints.csv)，不是下载的完整原始光谱，不插值。

2. **E. A. Nazimudeen、T. E. Girish、Sunila Abraham，2018，On the Nature of Thin Films of Speculum Metal，Materials Today Communications 16,314–319**。[DOI 10.1016/j.mtcomm.2018.07.005](https://doi.org/10.1016/j.mtcomm.2018.07.005)；[出版社全文摘要/段落](https://www.sciencedirect.com/science/article/pii/S2352492818301302)。传统 Aranmula 铸造/磨光镜，及其热蒸发薄膜；UV–Vis 反射谱，EDS/XRD/AFM。EDS 报告表面 Cu 约62–69%、Sn约30–32%，另有 Zn/As/Pb 等微量组分；薄膜反射率高于铸件。**不是20–25% Sn**。已定位到实测反射谱研究，但公开可读摘录未给确切扫描上下限、角度或数值表，未捏造范围。全文需机构访问。

3. **E. A. Nazimudeen 等，2023，Effects of high energy electron and X-ray irradiation on the morphology, microstructure and reflectivity of cast speculum metal mirror，Radiation Physics and Chemistry 202,110503**。[DOI 10.1016/j.radphyschem.2022.110503](https://www.sciencedirect.com/science/article/pii/S0969806X22005394)。提供同类铸造 speculum 照射前/后 UV–Vis 反射、AFM 与 XRD，电子照射6/9 MeV、X射线6/10 MeV；不应把硬 X 射线反射率当作可见光反射率。未取得原始数值表与确切可见扫描区间。

### 补充椭偏来源与适用性边界

- **A. A. Wronkowska、G. Czerniak、A. Wronkowski、Ł. Skowroński，2013，Optical and microstructural characterisation of Au–Sn and Cu–Sn diffusive layers，Applied Surface Science 281,30–37**。[DOI 10.1016/j.apsusc.2013.01.115](https://www.sciencedirect.com/science/article/abs/pii/S0169433213001633)。真空顺次蒸发/共蒸发到玻璃，Cu底层20 nm，调Sn厚度至原子比1:1；VASE + 透过谱，0.6–6.5 eV（约190.7–2066.4 nm），Drude–Lorentz 拟合有效复介电函数。Sn/Cu双层出现Cu6Sn5，共蒸发膜出现Cu10Sn3；这是**超薄、多相扩散膜的有效光学响应**，不是Cu3Sn纯相，也不是考古高锡镜块材。未取得全文参数表/原始表。
- **Jelena Wohlwend、Alla S. Sologubenko、Max Döbeli、Henning Galinski、Ralph Spolenak，2022（2021在线），Chemical Engineering of Cu–Sn Disordered Network Metamaterials，Nano Letters 22(2),853–859**。[DOI 10.1021/acs.nanolett.1c03545](https://pubs.acs.org/doi/10.1021/acs.nanolett.1c03545)。出版社明确列出 [SI PDF](https://pubs.acs.org/doi/suppl/10.1021/acs.nanolett.1c03545/suppl_file/nl1c03545_si_001.pdf)（nl1c03545_si_001.pdf，8.9MB）含“measured optical constants”。体系是Al–Cu–Sn共溅射后去Al的纳米网络，未成功打开SI，故尚不能确定其中测量的是纯金属致密膜、合金膜还是网络有效常数；**列作待取数的线索，不列作铜镜nk表**。
- **R. J. Nastasi-Andrews、R. E. Hummel，1977，Optical properties and electronic structure of dilute Cu-Au, Cu-Zn, Cu-Al, Cu-Ga, Cu-Si, Cu-Ge, Cu-Sn, and Cu-As alloys，Physical Review B 16,4314**。[DOI 10.1103/PhysRevB.16.4314](https://journals.aps.org/prb/abstract/10.1103/PhysRevB.16.4314)。α相稀合金差分反射测量，目标是带间跃迁阈值；摘要没有完整绝对R/n/k及组成/扫描上下限，不宜称为可用5–15% Sn光谱。
- **Pedemonte M.; Spotorno R.; Magnozzi M.; Criaco C.; Lupi C.; Sforzini; Piccardo P.，Traces of Fire: Macroscopic Colour as a Marker of Composition and Non-Equilibrium in Cu–Sn Bronzes**，[热那亚大学机构记录](https://unige.iris.cineca.it/handle/11567/1321665)，状态为“In corso di stampa”（待出版）。摘要明确1–16 wt.% Sn、铸态/均匀化态，SE测n,k，另11 wt.%研究冷却速率与微偏析。但记录**无附件、无期刊/年份/DOI及波段**，不能算已经交付的数值数据；适合后续追踪。

### 必须纠正的组成/相解释

“约20–25 wt.% Sn 的铜镜”“speculum”“纯δ相”“纯ε相”并非同一成分。由式量算（Cu=63.546、Sn=118.710）：Cu31Sn8约32.53 wt.% Sn；Cu41Sn11约33.39 wt.% Sn；Cu3Sn约38.37 wt.% Sn。20–25 wt.% Sn 块材可包含富Cu相与高Sn金属间化合物，热历史、表面富锡/腐蚀和相分数均可能改变实测结果。现代相图表将δ写成Cu41Sn11、ε写成正交Cu3Sn；见 **S. Fürtauer et al.,2013,The Cu–Sn phase diagram, Part I: New experimental results,Intermetallics 34,142–147**，[DOI 10.1016/j.intermet.2012.10.004](https://doi.org/10.1016/j.intermet.2012.10.004) · [PMC作者全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4819024/)。不要仅因标题有Cu3Sn就把γ相立方理论模型当作ε相光学实测。

### 搜索与取数边界

本轮公开检索没有发现已核实可下载的 Cu–Sn 二元合金完整 n,k 原始表，也未核实 refractiveindex.info 有锡青铜条目；其 Cu–Zn 黄铜数据不能替代 Cu–Sn。不能从单条法向 R(λ) 唯一反演两个未知函数 n(λ)、k(λ)。已明确区分：实测原表、论文曲线、作者模型/插值和未读取的线索。二进制下载限制另在文末说明。

## 2. 火镀金：反射谱、残汞、厚度与微结构

本组光谱、成分和形貌均注明测量对象；没有把反射强度曲线冒充绝对反射率或 n、k。

### 直接适用：火镀金表面可见光反射谱、Hg、厚度与微结构

**Prakash Joshi, Nikesh Maharjan, Anupam K C, Mim Lal Nakarmi (2022)**, “Characterization of Gold Thin Films Deposited by Centuries-old Fire-gilding Method”, *Indian Journal of Pure & Applied Physics* **60**, 117–125，[DOI **10.56042/ijpap.v60i2.57063**](https://doi.org/10.56042/ijpap.v60i2.57063)。[迁站出版商条目](https://or.niscpr.res.in/index.php/IJPAP/article/view/2236?articlesBySimilarityPage=10)和[2022 年卷期目录](https://op.niscpr.res.in/index.php/IJPAP/issue/view/65)核实 DOI；迁站条目显示上传日 2023-06-01，但卷期及原 PDF 为 2022 年 2 月。

- [官方文献记录](https://nopr.niscpr.res.in/handle/123456789/59301)；[迁站后的官方全文 PDF（成功读取）](https://or.niscpr.res.in/index.php/IJPAP/article/download/2236/572/6120)；[PDF 阅读页](https://or.niscpr.res.in/index.php/IJPAP/article/view/2236/572)。旧 NOPR PDF 503，CORE PDF 403，不作为唯一下载入口。
- 尼泊尔工匠制作铜底火镀金；原始膏体 Au:Hg 约 1:4–1:5（质量比），不能当成最终表层组成。
- EDS 平滑区 **Au 72.4、Hg 6.7、Cu 3.7、C 5.6、O 3.7、Al 7.0、Si 0.9 wt%**；多孔区 **Au 57.3、Hg 5.5、Cu 9.7、C 9.5、O 10.2、Al 4.5、Si 3.2 wt%**。保留原始多元素基准，不能写成二元 Au93.3Hg6.7。只对 Au+Hg 重归一才分别得到 Hg 约 8.47%、8.76%，这是推算，不是作者另测的成分。
- **反射谱 400–700 nm**，室温；钨卤灯、1200 line/mm 单色仪、硅探测器，约 **23°** 入射、100 Hz 斩波与锁相放大。图 6 单/双涂层、图 8 压光前后、图 11 氧化铁处理前后。纵轴是 **relative reflectance**，不是已校准绝对 R，也不是法向；未找到可下载原始数值，不能由此唯一求 n、k。
- 单涂层截面 SEM 厚约 **2 µm**，有空间变化。AFM rms：单/双涂层 **34/24 nm**；另一组压光前后 **20.3/6.6 nm**；再一组氧化铁处理前后 **30/11 nm**。这些是三组比较，不能把 34→6.6 合成同一试样演变。
- AFM/SEM：连接金颗粒为数百 nm；亚 µm 孔；约 µm 宽、纵向可达数 µm 的长间隙。图 2/5/7/9 是有 µm 扫描坐标的 AFM，图 3 为表面及截面 SEM。PDF 图像截图接口失败，尚未独立核验 SEM 每个标尺数字及图片像素尺寸。
- 版权：迁站出版商条目明确 **CC BY 4.0**（©2023，迁站日期）；旧 NOPR 有通用保留版权提示，以该文章特定许可为准，仍不是 CC0。

### 独立的火镀金反射谱与 AFM 复现

**P. Joshi, N. Maharjan, M. L. Nakarmi (2022)**, “Comparative Study of Fire-Gilded and Electroplated Gold Films on Copper Substrates”, *Journal of Nepal Physical Society* **8(3)**, 13–19, [DOI 10.3126/jnphyssoc.v8i3.50717](https://doi.org/10.3126/jnphyssoc.v8i3.50717)；[官方全文 PDF](https://www.nepjol.info/index.php/JNPhysSoc/article/view/50717/37851)。

现代工匠铜底火镀金 FG 与电镀 EP；膏体 Au:Hg=1:5 质量比，最终 Hg 未在本篇定量。AFM tapping，**5×5 µm**，FG rms **8.1 nm**，EP **21 nm**（图 2，表面 top view 与 3D）。反射测量同样钨卤灯/单色仪/Si、约 **23°**；图 3 **400–700 nm relative reflectance**，FG 在这套实验中更高，未给 n、k 或绝对 R 数值表。图 5 另有约 10×10 µm 带坐标 AFM（注意刻蚀处理已改变表面）。不是证明所有古代鎏金都比电镀平滑。[出版商条目](https://www.nepjol.info/index.php/JNPhysSoc/article/view/50717)明确保留全部版权，非 CC0。

### 中国鎏金铜器实物的 Hg、厚度与截面显微照片

**Ruiwen Ma, Zhimin Li, Ming Tang, Tongxiu Zheng, Hui Fang, Qinglin Ma (2025)**, “Microstructural characteristics and formation of the gilded artifacts excavated from Han Tomb situated in Qufu, Shandong, China”, *npj Heritage Science* **13**, 93, [DOI **10.1038/s40494-025-01657-3**](https://doi.org/10.1038/s40494-025-01657-3)；[全文](https://www.nature.com/articles/s40494-025-01657-3)。

山东曲阜九龙山鲁王墓 M3 西汉车马器 14 件；SEM–EDS 15 kV，FIB–SEM–EDS 3–5 kV。11 件层内 **Hg 2.6–17.4 wt%**；另 3 件 **<0.8 wt%**，作者依据多孔颗粒微结构和 Cu 扩散判断仍为火镀金，并明确其解释需实验验证。三类层厚 **2.3–4.8 µm、2.2–3.0 µm、>10 µm**。GYLJ3 的 FIB 切片：上/中/下约 **1/7/1 µm**，纳米/微米/纳米级晶粒；上层 **Au84.5 Hg5.0 Cu3.5 wt%**、中层 **Au82.8 Hg9.4 Cu3.3 wt%**（未列元素勿自补到 100%）。图 3 颗粒/孔洞，图 4 全层及纳米晶截面。相结构为作者推断，未做 XRD/TEM 确证。

图页：[图 3](https://www.nature.com/articles/s40494-025-01657-3/figures/3)，[图 4](https://www.nature.com/articles/s40494-025-01657-3/figures/4)。出版商 HTML 中给出的原始实际图片链接（URL请求宽度上限685 px；实际像素未读取，不是猜测 full URL）：

```
https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs40494-025-01657-3/MediaObjects/40494_2025_1657_Fig3_HTML.png
https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs40494-025-01657-3/MediaObjects/40494_2025_1657_Fig4_HTML.png
```

当前工具访问图文件 cache miss，像素高和标尺数字未独立读出；不可声称已检查高分辨原图。版权 **CC BY-NC-ND 4.0**，图片随论文许可，除另有 credit line；不是 CC0。原始数据可向作者合理索取，网页没有数据文件。未发邮件。

### Hg 的“最低含量”不能当绝对规律

**Raphael Margreiter, Jonas Baumann, Ioanna Mantouvalou, Martin Radtke, Uwe Reinholz, Erik Strub (2022)**, “Investigations on fire-gilding”, *Archaeometry* **64(6)**, 1465–1478, [DOI 10.1111/arcm.12797](https://doi.org/10.1111/arcm.12797)，[官方全文](https://onlinelibrary.wiley.com/doi/10.1111/arcm.12797)。实验复刻 Cu/Ag 底火镀金，SR-XRF 及老化实验；Ag 界面 Hg 富集、Cu 底未见同样富集。作者认为其研究的正常火镀金体含量通常不会低于 **5% Hg**，引述古样常见 8% 至 >20%，并研究温度、时间、层厚影响。不能拿“5%”否定上面的 Ma 2025 低 Hg 案例；两篇对象、采样深度、判据不同。此文没有可见光 n、k / R 表。

### 真正的 Au–Hg 椭偏研究（有模型，尚未拿到可直接导入的 n、k 表）

**A. Paulauskas, A. Selskis, V. Bukauskas, V. Vaicikauskas, A. Ramanavicius, Z. Balevicius (2018)**, “Real time study of amalgam formation and mercury adsorption on thin gold film by total internal reflection ellipsometry”, *Applied Surface Science* **427 Part B**, 298–303, [DOI 10.1016/j.apsusc.2017.08.236](https://doi.org/10.1016/j.apsusc.2017.08.236)，[出版商正文预览与摘要](https://www.sciencedirect.com/science/article/abs/pii/S0169433217325473)。

商业 SPR 芯片，Cr 黏附层/玻璃上的磁控溅射多晶 Au 经 Hg 吸附，形成树枝状表层；动态全内反射椭偏 TIRE + Bruggeman EMA，回归为 **Hg16.00±0.43%、Au84.00±0.43%**。摘要没有说明该百分数是质量、原子还是体积基准；EMA 常是体积分数，但此处未核实，**不能标 wt% 或 at%**。作者考虑非均匀表层并拟合光学参数。这不是加热火镀金样品，也不是独立成分确定的均匀块体 Au–Hg 实测光学常数。全文受访问限制；波长范围与 n、k 数值表未核实，不导出臆测 CSV。

**Andrius Paulauskas, Saulius Tumenas, Algirdas Selskis, Tomas Tolenis, Audrius Valavicius, Zigmas Balevicius (2018)**, “Hybrid Tamm-surface plasmon polaritons mode for detection of mercury adsorption on 1D photonic crystal/gold nanostructures by total internal reflection ellipsometry”, *Optics Express* **26(23)**, 30400–30408, [DOI 10.1364/OE.26.030400](https://doi.org/10.1364/OE.26.030400)，[PubMed 记录](https://pubmed.ncbi.nlm.nih.gov/30469914/)。TIRE + 深度折射率梯度 amalgam model；不是古器物，未核实完整光谱数据表。相关 [2019 年作者博士论文](https://epublications.vu.lt/object/elaba%3A41264159/index.html)，104 页，ISBN9786090702109，可作为后续取得两篇完整参数的入口；本次 full text 未成功打开。

### 排除与使用建议

- 没有找到可下载、组成及相态明确、360–830 nm 或至少 400–750 nm 的火镀金 Au–Hg **实测 n、k 数值表**。已有直接可用证据是实际火镀金的 **400–700 nm 相对反射曲线**与形貌、成分。
- 不能把 Au 与液体 Hg 的 n、k 线性混合称为实测 Au–Hg。TIRE 的 EMA 拟合是相应非均匀感测层的模型；用于古鎏金只能作为建模假设。
- 几何/粗糙参数有原始实验支撑；AFM rms 高度 nm **不是** Cycles roughness 或 microfacet α。需要相关长度/斜率或 BRDF 才能转换，不要直接把 6.6 nm 填进无量纲 roughness。
- 截面微米厚鎏金可按不透明金属处理是渲染建模判断；“露铜、红锈”宜用破损覆盖与独立材质/几何表达。观察图中的红色也不能仅凭颜色确定 Cu2O。
- 可选旁支：矿物 Weishanite 只有四点反射率的手册数据（480/534/589/656 nm）且约 Hg40 wt%、含 Ag，与少量汞火镀金不同；各二级站波长还有不一致，本次不把它充当目标连续光谱。

未核实到可直接用于本项目的量化光泽度 GU 数据；上述 AFM rms 不是光泽度。

## 3. 铜氧化物与锈层厚度

### 氧化物：已保存的可见光 n、k

**可立即使用的数值表是 Palik 手册表的公开转录镜像；其来源层级低于出版社原表，已保留原文件和 Git blob SHA，便于复核。** 两个 CSV 均保留 300–1000 nm 的 15 个原始表节点（间隔 50 nm），只把 µm 换成 nm；未加密采样，未数字化图线。可以在节点间插值覆盖 360–830 nm，但 1 nm 重采样不会增加实测分辨率。

| 材料 | 样品与来源 | 数据文件 / 原文件 | 方法、范围及限制 |
|---|---|---|---|
| Cu₂O，赤铜矿 | 手册标为 cubic cuprous oxide；多来源汇编 | [本地 CSV](data/Cu2O_Palik_visible_nk.csv) · [公开 .nk 数值文件](https://raw.githubusercontent.com/ulfgri/nk/master/palik/Cu2O.nk) · [存储库页面](https://github.com/ulfgri/nk/blob/master/palik/Cu2O.nk) | 全表 0.30–125 µm；可见部分追溯到 Karlsson 等 1982；其余红外来自 O’Keeffe、Heltemes、Dawson 等，部分 n 为插值。**未读取到原测量论文的方法全文，不能确认具体仪器/反演法，不能称作已核实椭偏数据。** |
| CuO，黑铜矿/tenorite | 手册标为 polycrystalline cupric oxide | [本地 CSV](data/CuO_Palik_visible_nk.csv) · [公开 .nk 数值文件](https://raw.githubusercontent.com/ulfgri/nk/master/palik/CuO.nk) · [存储库页面](https://github.com/ulfgri/nk/blob/master/palik/CuO.nk) | 全表 0.30–2.5 µm；唯一列出的原始实验来源为 Karlsson 等 1982；这是多晶标量数据，不能代表单晶 CuO 的完整各向异性介电张量。原文仪器/反演法尚未核实。 |

**原始书目：**Carl G. Ribbing、Arne Roos，*Copper Oxides (Cu₂O, CuO)*，E. D. Palik 编，*Handbook of Optical Constants of Solids II*，pp.875–882（原卷 1991；出版社电子合订版页面标 1998），[章节 DOI 10.1016/B978-0-08-055630-7.50054-7](https://doi.org/10.1016/B978-0-08-055630-7.50054-7)。镜像文件头明确对应 p.880、p.882；[原引用索引](https://github.com/ulfgri/nk/blob/master/palik/REFERENCES.txt)将可见部分关联到 **B. Karlsson、C. G. Ribbing、A. Roos、E. Valkonen、T. Karlsson，1982，Optical Properties of Some Metal Oxides in Solar Absorbers，Physica Scripta 25(6A),826–831，[DOI 10.1088/0031-8949/25/6A/044](https://doi.org/10.1088/0031-8949/25/6A/044)**。不是 ResearchGate 错标的 2006 年。

以下数值直接来自所保存 CSV，标准记号为 n+ik，n、k 无量纲：

| λ / nm | Cu₂O n | Cu₂O k | CuO n | CuO k |
|---:|---:|---:|---:|---:|
| 400 | 2.80 | 0.99 | 2.34 | 0.87 |
| 450 | 3.06 | 0.60 | 2.45 | 0.77 |
| 500 | 3.12 | 0.35 | 2.54 | 0.68 |
| 550 | 3.10 | 0.19 | 2.58 | 0.59 |
| 600 | 3.02 | 0.13 | 2.65 | 0.50 |
| 650 | 2.90 | 0.10 | 2.72 | 0.40 |
| 700 | 2.83 | 0.083 | 2.88 | 0.31 |
| 750 | 2.77 | 0.070 | 2.97 | 0.22 |

**数据清理边界：**镜像完整红外表有 `-0.0001`，显然不能作为被动材料的负吸收直接送进渲染器；本次只导出 300–1000 nm，两种材料在此段均为有效正值，原始 .nk 未改动。手册和其磁盘数据仍保留版权，不能因为镜像在 GitHub 就标 CC0。相较之下，后述 refractiveindex.info 数据文件明确为 CC0。

### 氧化物：原作者数字数据与独立椭偏交叉来源

**Dahlang Tahir、Sven Tougaard，2012，Electronic and optical properties of Cu, CuO and Cu₂O studied by electron spectroscopy，Journal of Physics: Condensed Matter 24,175002，[DOI 10.1088/0953-8984/24/17/175002](https://doi.org/10.1088/0953-8984/24/17/175002)。** 方法为 XPS 验相、REELS（150–2000 eV 入射电子）及介电响应模型/多重散射校正、Kramers–Kronig 变换求 n、k；不是光学椭偏。样品由多晶铜在真空系统中受控氧化得到 Cu₂O、再制 CuO；XPS 确认表层相，氧化深度至少约 15 nm。论文模型覆盖 0–100 eV。

作者在 2023 年公开 **1 至约 100 eV（约 1240–12.4 nm）** 数字表，足以覆盖全部目标可见光：[Zenodo 数据页，DOI 10.5281/zenodo.7669849](https://zenodo.org/records/7669849)。[CuO 与 Cu₂O 原始 XLSX](https://zenodo.org/records/7669849/files/Optical%20data%20n%20%26%20k%20for%20CuO%20and%20Cu2O.xlsx?download=1)，54.5 kB，作者标示 MD5 `55bb01e6199cf190ce38d7ea2f669353`。这是应优先取得的原作者机器可读数据；**本次文字抓取器读取该 XLSX 报 Unicode decoding error，终端网络也不可用，未成功落盘或转成 CSV**，不能把本地 Palik 表说成这份 REELS 数据。能量轴换算用 λ[nm]=1239.841984/E[eV]，转换后需按 λ 升序重排。

还有两项独立光学测量可检查细节差异：

- **Takayuki Ito、Takahiro Kawashima、Hiroyuki Yamaguchi、Taizo Masumi、Sadao Adachi，1998，Optical Properties of Cu₂O Studied by Spectroscopic Ellipsometry，Journal of the Physical Society of Japan 67,2125–2131，[DOI 10.1143/JPSJ.67.2125](https://doi.org/10.1143/JPSJ.67.2125)。** 浮区法生长 Cu₂O 单晶，室温 SE，**1.2–5.2 eV≈238–1033 nm**；给出介电函数、n、k、法向 R 及跃迁拟合。未取得独立原始数表。[带出版商摘要的书目记录](https://cir.nii.ac.jp/crid/1390282679156305152?lang=en)。
- **Francisc Haidu、Michael Fronk、Ovidiu D. Gordan、Camelia Scarlat、Georgeta Salvan、Dietrich R. T. Zahn，2011，Dielectric function and magneto-optical Voigt constant of Cu₂O: A combined spectroscopic ellipsometry and polar magneto-optical Kerr spectroscopy study，Physical Review B 84,195203，[出版商 / DOI 10.1103/PhysRevB.84.195203](https://journals.aps.org/prb/abstract/10.1103/PhysRevB.84.195203)。** 块体 Cu₂O，SE **0.73–10 eV≈124–1698 nm**，另测 Kerr。未取得数表。注意网页标题抽取会丢下标，正文对象是 Cu₂O，不能错归为 CuO。

refractiveindex.info 的 [Cu₂O/Querry](https://refractiveindex.info/?shelf=main&book=Cu2O&page=Querry) 是压片 **2.5–55.6 µm**；[CuO/Brimhall](https://refractiveindex.info/?shelf=main&book=CuO&page=Brimhall) 是铜上氧化膜 **10.1–34.8 nm**。二者都不覆盖可见光，不能外推到 400–750 nm。

### 铜器表面的赤铜矿层厚

| 样品 / 实测结果 | 方法和适用条件 | 原始出处 |
|---|---|---|
| 青铜自然锈层 **5–10 µm**，主要为 Cu₂O | Cu90.70、Sn5.27、Zn3.77、Pb0.08 wt.% 铸造试片；Ljubljana 屋顶室外暴露 9 年。金相截面，SEM–EDXS、Raman 等定相；是局部厚度范围，非均值±误差。论文 Fig.3a 可见截面。 | Tadeja Kosec、Mirjam Bajt Leban、Polonca Ropret、Matjaž Finšgar，2024，*The impact of urban rain on the changes of bare and artificially patinated bronze during 9-year exposure*，Environmental Science and Pollution Research 31,31925–31941，[DOI 10.1007/s11356-024-33369-9](https://link.springer.com/article/10.1007/s11356-024-33369-9)。 |
| Cu₂O 厚约 **0.8±0.2 µm** 时形成充分遮盖铜色的棕黑外观 | 多种室外铜样品；IRAS 经恒电流还原和 SEM 标定厚度，再与反射/色度比较。**这是外观阈值，绝不是所有器物的锈层厚度上限。** | C. Leygraf、Tingru Chang、Gunilla Herting、Inger Odnevall Wallinder，2019，*The origin and evolution of copper patina colour*，Corrosion Science 157,337–346，[DOI 10.1016/j.corsci.2019.05.025](https://doi.org/10.1016/j.corsci.2019.05.025)。 |

历史实物也有截面统计：**Tingru Chang、Inger Odnevall Wallinder、Daniel de la Fuente、Belen Chico、Manuel Morcillo、Jean-Marie Welter、Christofer Leygraf，2017，Analysis of Historic Copper Patinas. Influence of Inclusions on Patina Uniformity，Materials 10(3),298，[DOI 10.3390/ma10030298](https://doi.org/10.3390/ma10030298)**。16–19 世纪安装的八处欧洲铜屋顶，每种材料取五幅 SEM 截面，按层面积换算平均厚度。Table 3 的 Cu₂O 厚度：Prague 4.2±3.3、Graz 9.1±4.4、Drottningholm 9.5±6.1、Maria Dreieichen 9.9±6.9、Helsinki 1.1±0.7、Kronborg 4.1±3.9、Otto Wagner Church 9.7±4.8、Stockholm Old Town 10.3±6.6 µm；±为标准差。[作者全文 Table 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC5503407/)。这是含夹杂历史铜材，成分不等同于高锡镜。

以上厚度数值已另存 [厚度 CSV](data/cuprite_layer_thickness_measured.csv)。没有把它们移植成所有汉唐铜器或鎏金下腐蚀层的统一厚度。大气形成的含缺陷 Cu₂O 可呈棕黑色，不能用理想红色晶体的 n、k 保证重现所有锈层；本文研究也未证明所有照片的红斑都是赤铜矿。

## 4. 金银合金

### 11 份已保存的模型光谱

**David Rioux、Simon Vallières、Sébastien Besner、Philip Muñoz、Eric Mazur、Michel Meunier，2014（2013 在线），An Analytic Model for the Dielectric Function of Au, Ag, and their Alloys，Advanced Optical Materials 2,176–182，[DOI 10.1002/adom.201300457](https://doi.org/10.1002/adom.201300457)。** 模型拟合五组 80 nm 合金薄膜椭偏实验：Au、Au:Ag=2:1、1:1、1:2、Ag。refractiveindex.info 提供 Au 含量 0、10、…、100% 的 **270–1200 nm、1 nm 间隔**采样表，覆盖 360–830 nm。

已保存全部 11 组，每组 931 行，标准 n+ik：`data/AuAg_Rioux-Au*Ag*_model.csv`。它们是**受椭偏约束的解析模型采样值**，不是对每一种 10% 配比都做了一次新实验，也不是原始 Ψ、Δ；文件名保留 `_model`。数据库百分比的质量/原子基准没有在简短条目明确，本轮未拿到原论文成分定义全文，故这里沿用其标签，不擅自按金箔 wt.% 选用。

| 组成标签 | 本地 CSV | 数据页 / 原始数值文件 |
|---|---|---|
| Au100Ag0 | [CSV](data/AuAg_Rioux-Au100Ag0_model.csv) | [数据库页面](https://refractiveindex.info/?shelf=other&book=Au-Ag&page=Rioux-Au100Ag0) · [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au100Ag0.yml) |
| Au90Ag10 | [CSV](data/AuAg_Rioux-Au90Ag10_model.csv) | [数据库页面](https://refractiveindex.info/?shelf=other&book=Au-Ag&page=Rioux-Au90Ag10) · [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au90Ag10.yml) |
| Au80Ag20 | [CSV](data/AuAg_Rioux-Au80Ag20_model.csv) | [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au80Ag20.yml) |
| Au70Ag30 | [CSV](data/AuAg_Rioux-Au70Ag30_model.csv) | [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au70Ag30.yml) |
| Au60Ag40 | [CSV](data/AuAg_Rioux-Au60Ag40_model.csv) | [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au60Ag40.yml) |
| Au50Ag50 | [CSV](data/AuAg_Rioux-Au50Ag50_model.csv) | [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au50Ag50.yml) |
| Au40Ag60 | [CSV](data/AuAg_Rioux-Au40Ag60_model.csv) | [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au40Ag60.yml) |
| Au30Ag70 | [CSV](data/AuAg_Rioux-Au30Ag70_model.csv) | [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au30Ag70.yml) |
| Au20Ag80 | [CSV](data/AuAg_Rioux-Au20Ag80_model.csv) | [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au20Ag80.yml) |
| Au10Ag90 | [CSV](data/AuAg_Rioux-Au10Ag90_model.csv) | [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au10Ag90.yml) |
| Au0Ag100 | [CSV](data/AuAg_Rioux-Au0Ag100_model.csv) | [YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/other/alloys/Au-Ag/nk/Rioux-Au0Ag100.yml) |

例如 Au90Ag10：400 nm 时 n=1.49030、k=1.83589；550 nm 时 n=0.32858、k=2.70240；750 nm 时 n=0.21001、k=4.71008。全部为模型表节点，不是额外实测。数据库文件自身 [CC0 声明](https://github.com/polyanskiy/refractiveindex.info-database)；保留的原始 YAML 与 [provenance.json](sources/provenance.json) 记录各文件 SHA。

### 金银合金：另有原作者公开实测数表

**Ovidio Peña-Rodríguez、Magdalena Caro、Antonio Rivera、José Olivares、José Manuel Perlado、Alfredo Caro，2014，Optical properties of Au–Ag alloys: An ellipsometric study，Optical Materials Express 4(2),403–410，[DOI 10.1364/OME.4.000403](https://doi.org/10.1364/OME.4.000403)。** 电子束共蒸发 Au–Ag/Si，膜厚170–330 nm，RBS 测成分与厚度；室温75° SE，**0.73–5.8 eV≈214–1698 nm**，Kramers–Kronig 一致 B-spline 拟合致密层，表面用 EMA 粗糙层处理。[出版商提供的全文预览](https://www.researchgate.net/publication/263768045_Optical_properties_of_Au-Ag_alloys_An_ellipsometric_study)。

原作者的 [Zenodo 数据集，DOI 10.5281/zenodo.50484](https://zenodo.org/records/50484) 有 [Au-Ag_Alloy.zip](https://zenodo.org/records/50484/files/Au-Ag_Alloy.zip?download=1)，9.7 kB，MD5 `094a015c89bc0157240b31478f68be82`。[ZIP 预览](https://zenodo.org/records/50484/preview/Au-Ag_Alloy.zip?include_deleted=0)实际列出 `xAg_000/008/015/024/035/048/066/074/085/100.dat` 十文件；x 是 Ag 组成分数，不能与 Rioux 文件的 Au 标签混读。**ZIP 已定位，二进制下载受当前环境限制，尚未落盘转换；也尚未检查 .dat 头部的轴单位。** 不把 Rioux CSV 说成该作者数据。此系列为二元 Au–Ag；含铜金箔还需对应 Au–Ag–Cu 光学数据，不能当成已覆盖三元合金。

### 渲染使用时的物理边界

这些是材料光谱资料与建模判断，不是已经跑过的 pbrt/Cycles 材质验证：

- 本报告统一输出标准 n+ik；Callet 的 κ 必须乘 n。普通 Fresnel 法向反射率为 `R0=((n-1)^2+k^2)/((n+1)^2+k^2)`，假设空气侧、平整界面、均匀半无限材料。单条 R0 不能唯一确定 n 和 k。
- 铜镜的合金相与火镀金的 Au(Hg,Cu) 是不同材料；不能用纯 Cu、Sn 或 Au、Hg 的 n、k 线性平均冒充合金实测。
- Cu₂O/CuO 是有吸收的氧化物。有限厚锈层覆盖金属时，还需基底和层厚；只设“金属度=1”不会表达层内吸收/透射。强散射、多孔腐蚀层也未必适合单一平整薄膜模型。
- 实测 AFM rms 是高度统计量，单位 nm；GGX/Beckmann 粗糙度是与微表面斜率有关的无量纲参数。缺相关长度或 BRDF 时不能直接换算。
- 微米级完整鎏金层按不透明金属建模是合理起点；露铜、锈斑和裂纹需空间覆盖/几何信息。是否还应求有限膜透射，取决于实际厚度与孔洞，不是仅由“鎏金”名称决定。

## 5. 高清馆藏照片与显微图

以下照片的馆方页面均把材质列为 gilt bronze；仅凭这一材质名称，不能确认每件都采用汞齐火镀金。Cleveland 图像按馆方 [Open Access 政策](https://www.clevelandart.org/open-access) 为 CC0；[CC0 1.0 授权](https://creativecommons.org/publicdomain/zero/1.0/)。Met 页面标为 Public Domain，Commons 的馆方捐赠文件亦标 CC0。

**验证范围：**已核对馆方藏品页面的实物尺寸、材质和授权。下面的像素尺寸/文件大小来自 Wikimedia Commons 原文件条目或分类索引，不是 EXIF 中可能遗留的母版尺寸。本环境无法下载二进制原图或打开浏览器作原图视觉检查；因此表面描述依馆方文字，未宣称已看清亚毫米颗粒、划痕。图中红色不能仅凭颜色鉴定为 Cu₂O，需 Raman/XRD 等证据。

原图链接采用 Commons 的 `Special:Redirect/file/` 无尺寸参数入口（重定向到原文件，不是缩略图）；原文件重定向在本环境未能完成网络验证。

| ID | 对象 / 馆藏号 | 原文件像素 / 格式 | 实物尺寸 | 页面、原图与适用部位 |
|---|---|---|---|---|
| P1 | 阿弥陀佛 Amitabha；大理，11 世纪中期；CMA 1942.1082 | 5549 × 5513；TIFF，87.55 MB | 高 230 mm | [馆方页面](https://www.clevelandart.org/art/1942.1082) · [原图](https://commons.wikimedia.org/wiki/Special:Redirect/file/China%2C_Yunnan_province%2C_Dali_kingdom_-_Amitabha_-_1942.1082_-_Cleveland_Museum_of_Art.tif) · [原文件元数据](https://commons.wikimedia.org/wiki/File:China%2C_Yunnan_province%2C_Dali_kingdom_-_Amitabha_-_1942.1082_-_Cleveland_Museum_of_Art.tif)。脸、躯干、腿部鎏金脱落和深色露底；馆方文字明确记录。 |
| P2 | 佛坐像；明，16 世纪；CMA 1970.149.1 | 6000 × 6539；TIFF，112.27 MB | 高 99 mm | [馆方页面](https://www.clevelandart.org/art/1970.149.1) · [原图](https://commons.wikimedia.org/wiki/Special:Redirect/file/China%2C_Ming_dynasty_-_Seated_Buddha_-_1970.149.1_-_Cleveland_Museum_of_Art.tif) · [原文件元数据](https://commons.wikimedia.org/wiki/File:China%2C_Ming_dynasty_-_Seated_Buddha_-_1970.149.1_-_Cleveland_Museum_of_Art.tif)。小型实物配大图，适合裁切面部/胸前金层磨损；馆方明确记录深棕色露底。 |
| P3 | 佛坐像；明，16 世纪；CMA 1970.149.2 | 6000 × 6810；TIFF，116.92 MB | 高 99 mm | [馆方页面](https://www.clevelandart.org/art/1970.149.2) · [原图](https://commons.wikimedia.org/wiki/Special:Redirect/file/China%2C_Ming_dynasty_-_Seated_Buddha_-_1970.149.2_-_Cleveland_Museum_of_Art.tif) · [原文件元数据](https://commons.wikimedia.org/wiki/File:China%2C_Ming_dynasty_-_Seated_Buddha_-_1970.149.2_-_Cleveland_Museum_of_Art.tif)。面部鎏金磨损；馆方文字明确记录。 |
| P4 | 观音菩萨；隋，581–618；CMA 1962.217 | 3881 × 4174；TIFF，46.36 MB | 高 83 mm | [馆方页面](https://www.clevelandart.org/art/1962.217) · [原图](https://commons.wikimedia.org/wiki/Special:Redirect/file/China%2C_Sui_dynasty_-_Bodhisattva_Guanyin_-_1962.217_-_Cleveland_Museum_of_Art.tif) · [原文件元数据](https://commons.wikimedia.org/wiki/File:China%2C_Sui_dynasty_-_Bodhisattva_Guanyin_-_1962.217_-_Cleveland_Museum_of_Art.tif)。馆方记录下身、腿部脱金露底；小器物有利于观察毫米级表面变化。 |
| P5 | 观音坐像；明，约 1450；CMA 1916.19 | 3400 × 3382；JPEG，1.06 MB | 221 × 167 mm | [馆方页面](https://www.clevelandart.org/art/1916.19) · [原图](https://commons.wikimedia.org/wiki/Special:Redirect/file/China%2C_Ming_dynasty_-_Seated_Guanyin_-_1916.19_-_Cleveland_Museum_of_Art.jpg) · [原文件元数据](https://commons.wikimedia.org/wiki/File:China%2C_Ming_dynasty_-_Seated_Guanyin_-_1916.19_-_Cleveland_Museum_of_Art.jpg)。复杂纹饰凹处磨损露底，适合比较保留鎏金与深色区域。 |
| P6 | 六牙宝装象；辽，约 11 世纪；CMA 1980.24 | 3400 × 2969；JPEG，1.05 MB | 高 185 mm | [馆方页面](https://www.clevelandart.org/art/1980.24) · [原图](https://commons.wikimedia.org/wiki/Special:Redirect/file/Clevelandart_1980.24.jpg) · [原文件元数据](https://commons.wikimedia.org/wiki/File:Clevelandart_1980.24.jpg)。器物/动物形制；鞍毯浮雕、金色表面与深色斑块，馆方文字记录磨损。 |
| P7 | 水月观音；五代至宋，900–1100；CMA 1984.7 | 3214 × 3400；JPEG，991 KB | 高 176 mm | [馆方页面](https://www.clevelandart.org/art/1984.7) · [原图](https://commons.wikimedia.org/wiki/Special:Redirect/file/Clevelandart_1984.7.jpg) · [原文件元数据](https://commons.wikimedia.org/wiki/File:Clevelandart_1984.7.jpg)。馆方记录躯干与底座的磨损、氧化和露底。 |

P1–P3 的 TIFF 像素/大小见 [Cleveland 中国佛像原文件分类索引](https://commons.wikimedia.org/wiki/Category:Sculptures_of_Buddhas_from_China_in_the_Cleveland_Museum_of_Art)。该分类还列有大理阿弥陀佛 3400 × 3377 的 JPEG，但 TIFF 大得多。P4 的 [原文件条目](https://commons.wikimedia.org/wiki/File:China,_Sui_dynasty_-_Bodhisattva_Guanyin_-_1962.217_-_Cleveland_Museum_of_Art.tif) 明确给出 3881 × 4174。不要误选同分类的 1915.334.1：馆方材质为 marble，并非鎏金铜。

### Met：同一尊北魏大像的两张开放照片

[弥勒佛 26.123 / object 42733](https://www.metmuseum.org/art/collection/search/42733)，北魏太和十年（486），鎏金青铜、残留颜料、分范铸造；1403 × 622 × 489 mm；馆方页面 Public Domain。以下版本的尺寸是 Commons 实际文件像素；如 EXIF 出现 5410 × 7210，不应当作下载 JPEG 的实际分辨率。

| ID | 图像 | 原文件像素 | 原图、元数据 |
|---|---|---|---|
| P8 | Met DP170102，CC0 | 3001 × 4000 | [原图](https://commons.wikimedia.org/wiki/Special:Redirect/file/%E5%8C%97%E9%AD%8F%E5%A4%AA%E5%92%8C%E5%8D%81%E5%B9%B4_%E9%9D%92%E9%8A%85%E9%8E%8F%E9%87%91%E5%BD%8C%E5%8B%92%E4%BD%9B%E5%83%8F-Buddha_Maitreya_%28Mile_fo%29_MET_DP170102.jpg) · [原文件元数据与授权](https://commons.wikimedia.org/wiki/File:%E5%8C%97%E9%AD%8F%E5%A4%AA%E5%92%8C%E5%8D%81%E5%B9%B4_%E9%9D%92%E9%8A%85%E9%8E%8F%E9%87%91%E5%BD%8C%E5%8B%92%E4%BD%9B%E5%83%8F-Buddha_Maitreya_%28Mile_fo%29_MET_DP170102.jpg) |
| P9 | Met DP210262，CC0 | 2890 × 3879 | [原图](https://commons.wikimedia.org/wiki/Special:Redirect/file/%E5%8C%97%E9%AD%8F%E5%A4%AA%E5%92%8C%E5%8D%81%E5%B9%B4_%E9%9D%92%E9%8A%85%E9%8E%8F%E9%87%91%E5%BD%8C%E5%8B%92%E4%BD%9B%E5%83%8F-Buddha_Maitreya_%28Mile_fo%29_MET_DP210262.jpg) · [原文件元数据与授权](https://commons.wikimedia.org/wiki/File:%E5%8C%97%E9%AD%8F%E5%A4%AA%E5%92%8C%E5%8D%81%E5%B9%B4_%E9%9D%92%E9%8A%85%E9%8E%8F%E9%87%91%E5%BD%8C%E5%8B%92%E4%BD%9B%E5%83%8F-Buddha_Maitreya_%28Mile_fo%29_MET_DP210262.jpg) |

### 另有馆方直接图像接口，适合找细节/反面

[Met 1974.268.8a–c 佛坐像](https://www.metmuseum.org/art/collection/search/61820)，晚 4 至早 5 世纪，高 165、宽 70、深 35 mm；页面 Public Domain，并提供七视图。下面均为从馆方页面实际取得的图像链接，但本环境未取得像素尺寸，故不混入上表的已知分辨率文件。

- [主视图](https://collectionapi.metmuseum.org/api/collection/v1/iiif/61820/1851362/main-image)
- [附图 1](https://collectionapi.metmuseum.org/api/collection/v1/iiif/61820/163747/main-image)
- [附图 2](https://collectionapi.metmuseum.org/api/collection/v1/iiif/61820/163751/main-image)
- [附图 3](https://collectionapi.metmuseum.org/api/collection/v1/iiif/61820/163752/main-image)

[Cleveland 1979.20 菩萨立像](https://www.clevelandart.org/art/1979.20)，隋、晚 6 世纪，高 115 mm，CC0；图像搜索索引直接暴露 [正面 JPEG](https://openaccess-cdn.clevelandart.org/1979.20/1979.20_print.jpg)、[附图 0](https://openaccess-cdn.clevelandart.org/alternate/1979.20/1979.20_alt0_print.jpg)、[附图 2](https://openaccess-cdn.clevelandart.org/alternate/1979.20/1979.20_alt2_print.jpg)。未取得这三个 JPEG 的实际像素尺寸；未把 print URL 推断为 full TIFF。

**尺度换算：**照片没有标尺。应在原图中测量器物上下端的投影像素高 `h_px`，用 `h_px / 实物高度_mm` 得到全物体的近似 px/mm；不能使用整张图高（含留白）。该值仅可用于接近相同深度、朝向的局部区域；曲面、透视、底座高度和摄影俯角会改变局部比例，不适合由全高精确反推微孔尺寸。


### 论文显微图：可量尺度与图像授权

| 图像 | 文件/所在页面 | 尺度和像素核查 | 授权 |
|---|---|---|---|
| Joshi 等 IJPAP 2022，Fig.2、3、5、7、9 | [官方 PDF](https://or.niscpr.res.in/index.php/IJPAP/article/download/2236/572/6120)；Fig.2、3 在印刷 p.120（PDF第4页），Fig.7在 p.122。 | AFM 有 µm 坐标；正文确认 Fig.2a 为20×20 µm，Fig.2c为2×2 µm；Fig.3 为表面、孔洞和截面SEM。未取到独立原始位图尺寸，截图工具失败，未独立读出各 SEM 标尺细字。 | [文章许可页](https://or.niscpr.res.in/index.php/IJPAP/article/view/2236)：CC BY 4.0；需署名。 |
| Joshi 等 JNPS 2022，Fig.2 | [官方 PDF](https://www.nepjol.info/index.php/JNPhysSoc/article/view/50717/37851)，印刷p.15（PDF第3页） | 正文和图注明确 **5×5 µm**；火镀金 z量程50 nm、电镀250 nm；数值量程不同，不能直接比较图中明暗。位图像素未取得。 | [文章页](https://www.nepjol.info/index.php/JNPhysSoc/article/view/50717)保留版权；未确认开放再利用许可。 |
| Ma 等 2025，Fig.3，汉代鎏金层截面颗粒/孔洞 | [图页](https://www.nature.com/articles/s40494-025-01657-3/figures/3) · [实际 HTML PNG](https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs40494-025-01657-3/MediaObjects/40494_2025_1657_Fig3_HTML.png) | URL请求宽度上限 **685 px**，实际宽高未读取；这是网页版本，**未称最大原图**。具体标尺数字未独立读出。 | [全文权利声明](https://www.nature.com/articles/s40494-025-01657-3)：CC BY-NC-ND 4.0，留意单图 credit line。 |
| Ma 等 2025，Fig.4，FIB全层、纳米晶界面 | [图页](https://www.nature.com/articles/s40494-025-01657-3/figures/4) · [实际 HTML PNG](https://media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs40494-025-01657-3/MediaObjects/40494_2025_1657_Fig4_HTML.png) | URL请求宽度上限 **685 px**，实际宽高未读取；正文量得上/中/下层约1/7/1 µm。全文图页有 Full size image 入口，本环境访问失败；不可把正文层厚当作图中已读出的标尺。 | 同上，CC BY-NC-ND 4.0；非CC0。 |

显微图中有测量坐标的 AFM 是本轮最明确的尺度参考；SEM/FIB 则已定位到相关图和正文测量，但未完成逐图高分辨标尺核读。不会把论文低清网页图冒称开放博物馆高清原照。

## 核查结果与仍有缺口的交付项

13份保留的光谱原文件均通过 Git blob SHA 校验；本地光谱已核对列数、波长顺序、有限值、n/k非负、目标可见波段覆盖，以及与保留源文件的逐节点一致性；反射率使用0–1，形貌表保留单位、条件和来源。标量转录与模型采样在文件名和正文中区分。馆藏尺寸与许可核对了馆方页面；像素尺寸来自具体文件元数据，未以EXIF母版尺寸冒充实际文件。

本轮尚未完成的具体事项：

1. Callet 10/20/30 wt.% Sn 原始1 nm数表；纯δ、纯ε相的独立可见 n、k；20–25 wt.% Sn 的已核实法向完整反射数表。
2. 成分、相态明确的火镀金连续 n、k，或校准绝对反射谱。现有400–700 nm相对曲线已定位，未冒充绝对光谱。
3. Tahir–Tougaard 的氧化物 XLSX、Peña-Rodríguez 的 Au–Ag ZIP：确实公开存在，URL和校验值已给出，但二进制下载/转换受环境限制，未保存成CSV。终端网络请求被限制；网页文字和GitHub文本读取可用。已通过后者取得氧化物手册镜像和金银模型CSV。
4. 全部分辨率馆藏原图的实际下载、Commons原文件重定向检查，以及表面颗粒/划痕的放大视觉检查；显微图的原始像素和每根标尺数字。不能据当前图片清单保证每幅照片均能分辨所需粒径，也不能仅凭颜色把红斑定相为Cu₂O。

本次未创建渲染场景，也未声称通过 pbrt 或 Cycles 重现实物。研究文本中的“可作为建模起点”与文献实测结果已分开。
