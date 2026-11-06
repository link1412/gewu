# Cu₂O、CuO 与金银合金

## 氧化物：已保存的可见光 n、k

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

## 氧化物：原作者数字数据与独立椭偏交叉来源

**Dahlang Tahir、Sven Tougaard，2012，Electronic and optical properties of Cu, CuO and Cu₂O studied by electron spectroscopy，Journal of Physics: Condensed Matter 24,175002，[DOI 10.1088/0953-8984/24/17/175002](https://doi.org/10.1088/0953-8984/24/17/175002)。** 方法为 XPS 验相、REELS（150–2000 eV 入射电子）及介电响应模型/多重散射校正、Kramers–Kronig 变换求 n、k；不是光学椭偏。样品由多晶铜在真空系统中受控氧化得到 Cu₂O、再制 CuO；XPS 确认表层相，氧化深度至少约 15 nm。论文模型覆盖 0–100 eV。

作者在 2023 年公开 **1 至约 100 eV（约 1240–12.4 nm）** 数字表，足以覆盖全部目标可见光：[Zenodo 数据页，DOI 10.5281/zenodo.7669849](https://zenodo.org/records/7669849)。[CuO 与 Cu₂O 原始 XLSX](https://zenodo.org/records/7669849/files/Optical%20data%20n%20%26%20k%20for%20CuO%20and%20Cu2O.xlsx?download=1)，54.5 kB，作者标示 MD5 `55bb01e6199cf190ce38d7ea2f669353`。这是应优先取得的原作者机器可读数据；**本次文字抓取器读取该 XLSX 报 Unicode decoding error，终端网络也不可用，未成功落盘或转成 CSV**，不能把本地 Palik 表说成这份 REELS 数据。能量轴换算用 λ[nm]=1239.841984/E[eV]，转换后需按 λ 升序重排。

还有两项独立光学测量可检查细节差异：

- **Takayuki Ito、Takahiro Kawashima、Hiroyuki Yamaguchi、Taizo Masumi、Sadao Adachi，1998，Optical Properties of Cu₂O Studied by Spectroscopic Ellipsometry，Journal of the Physical Society of Japan 67,2125–2131，[DOI 10.1143/JPSJ.67.2125](https://doi.org/10.1143/JPSJ.67.2125)。** 浮区法生长 Cu₂O 单晶，室温 SE，**1.2–5.2 eV≈238–1033 nm**；给出介电函数、n、k、法向 R 及跃迁拟合。未取得独立原始数表。[带出版商摘要的书目记录](https://cir.nii.ac.jp/crid/1390282679156305152?lang=en)。
- **Francisc Haidu、Michael Fronk、Ovidiu D. Gordan、Camelia Scarlat、Georgeta Salvan、Dietrich R. T. Zahn，2011，Dielectric function and magneto-optical Voigt constant of Cu₂O: A combined spectroscopic ellipsometry and polar magneto-optical Kerr spectroscopy study，Physical Review B 84,195203，[出版商 / DOI 10.1103/PhysRevB.84.195203](https://journals.aps.org/prb/abstract/10.1103/PhysRevB.84.195203)。** 块体 Cu₂O，SE **0.73–10 eV≈124–1698 nm**，另测 Kerr。未取得数表。注意网页标题抽取会丢下标，正文对象是 Cu₂O，不能错归为 CuO。

refractiveindex.info 的 [Cu₂O/Querry](https://refractiveindex.info/?shelf=main&book=Cu2O&page=Querry) 是压片 **2.5–55.6 µm**；[CuO/Brimhall](https://refractiveindex.info/?shelf=main&book=CuO&page=Brimhall) 是铜上氧化膜 **10.1–34.8 nm**。二者都不覆盖可见光，不能外推到 400–750 nm。

## 铜器表面的赤铜矿层厚

| 样品 / 实测结果 | 方法和适用条件 | 原始出处 |
|---|---|---|
| 青铜自然锈层 **5–10 µm**，主要为 Cu₂O | Cu90.70、Sn5.27、Zn3.77、Pb0.08 wt.% 铸造试片；Ljubljana 屋顶室外暴露 9 年。金相截面，SEM–EDXS、Raman 等定相；是局部厚度范围，非均值±误差。论文 Fig.3a 可见截面。 | Tadeja Kosec、Mirjam Bajt Leban、Polonca Ropret、Matjaž Finšgar，2024，*The impact of urban rain on the changes of bare and artificially patinated bronze during 9-year exposure*，Environmental Science and Pollution Research 31,31925–31941，[DOI 10.1007/s11356-024-33369-9](https://link.springer.com/article/10.1007/s11356-024-33369-9)。 |
| Cu₂O 厚约 **0.8±0.2 µm** 时形成充分遮盖铜色的棕黑外观 | 多种室外铜样品；IRAS 经恒电流还原和 SEM 标定厚度，再与反射/色度比较。**这是外观阈值，绝不是所有器物的锈层厚度上限。** | C. Leygraf、Tingru Chang、Gunilla Herting、Inger Odnevall Wallinder，2019，*The origin and evolution of copper patina colour*，Corrosion Science 157,337–346，[DOI 10.1016/j.corsci.2019.05.025](https://doi.org/10.1016/j.corsci.2019.05.025)。 |

历史实物也有截面统计：**Tingru Chang、Inger Odnevall Wallinder、Daniel de la Fuente、Belen Chico、Manuel Morcillo、Jean-Marie Welter、Christofer Leygraf，2017，Analysis of Historic Copper Patinas. Influence of Inclusions on Patina Uniformity，Materials 10(3),298，[DOI 10.3390/ma10030298](https://doi.org/10.3390/ma10030298)**。16–19 世纪安装的八处欧洲铜屋顶，每种材料取五幅 SEM 截面，按层面积换算平均厚度。Table 3 的 Cu₂O 厚度：Prague 4.2±3.3、Graz 9.1±4.4、Drottningholm 9.5±6.1、Maria Dreieichen 9.9±6.9、Helsinki 1.1±0.7、Kronborg 4.1±3.9、Otto Wagner Church 9.7±4.8、Stockholm Old Town 10.3±6.6 µm；±为标准差。[作者全文 Table 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC5503407/)。这是含夹杂历史铜材，成分不等同于高锡镜。

以上厚度数值已另存 [厚度 CSV](data/cuprite_layer_thickness_measured.csv)。没有把它们移植成所有汉唐铜器或鎏金下腐蚀层的统一厚度。大气形成的含缺陷 Cu₂O 可呈棕黑色，不能用理想红色晶体的 n、k 保证重现所有锈层；本文研究也未证明所有照片的红斑都是赤铜矿。

## 金银合金：11 份已保存的模型光谱

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

## 金银合金：另有原作者公开实测数表

**Ovidio Peña-Rodríguez、Magdalena Caro、Antonio Rivera、José Olivares、José Manuel Perlado、Alfredo Caro，2014，Optical properties of Au–Ag alloys: An ellipsometric study，Optical Materials Express 4(2),403–410，[DOI 10.1364/OME.4.000403](https://doi.org/10.1364/OME.4.000403)。** 电子束共蒸发 Au–Ag/Si，膜厚170–330 nm，RBS 测成分与厚度；室温75° SE，**0.73–5.8 eV≈214–1698 nm**，Kramers–Kronig 一致 B-spline 拟合致密层，表面用 EMA 粗糙层处理。[出版商提供的全文预览](https://www.researchgate.net/publication/263768045_Optical_properties_of_Au-Ag_alloys_An_ellipsometric_study)。

原作者的 [Zenodo 数据集，DOI 10.5281/zenodo.50484](https://zenodo.org/records/50484) 有 [Au-Ag_Alloy.zip](https://zenodo.org/records/50484/files/Au-Ag_Alloy.zip?download=1)，9.7 kB，MD5 `094a015c89bc0157240b31478f68be82`。[ZIP 预览](https://zenodo.org/records/50484/preview/Au-Ag_Alloy.zip?include_deleted=0)实际列出 `xAg_000/008/015/024/035/048/066/074/085/100.dat` 十文件；x 是 Ag 组成分数，不能与 Rioux 文件的 Au 标签混读。**ZIP 已定位，二进制下载受当前环境限制，尚未落盘转换；也尚未检查 .dat 头部的轴单位。** 不把 Rioux CSV 说成该作者数据。此系列为二元 Au–Ag；含铜金箔还需对应 Au–Ag–Cu 光学数据，不能当成已覆盖三元合金。

## 渲染使用时的物理边界

这些是材料光谱资料与建模判断，不是已经跑过的 pbrt/Cycles 材质验证：

- 本报告统一输出标准 n+ik；Callet 的 κ 必须乘 n。普通 Fresnel 法向反射率为 `R0=((n-1)^2+k^2)/((n+1)^2+k^2)`，假设空气侧、平整界面、均匀半无限材料。单条 R0 不能唯一确定 n 和 k。
- 铜镜的合金相与火镀金的 Au(Hg,Cu) 是不同材料；不能用纯 Cu、Sn 或 Au、Hg 的 n、k 线性平均冒充合金实测。
- Cu₂O/CuO 是有吸收的氧化物。有限厚锈层覆盖金属时，还需基底和层厚；只设“金属度=1”不会表达层内吸收/透射。强散射、多孔腐蚀层也未必适合单一平整薄膜模型。
- 实测 AFM rms 是高度统计量，单位 nm；GGX/Beckmann 粗糙度是与微表面斜率有关的无量纲参数。缺相关长度或 BRDF 时不能直接换算。
- 微米级完整鎏金层按不透明金属建模是合理起点；露铜、锈斑和裂纹需空间覆盖/几何信息。是否还应求有限膜透射，取决于实际厚度与孔洞，不是仅由“鎏金”名称决定。
