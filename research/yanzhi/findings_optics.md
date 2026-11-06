# 金红光谱与金光学常数：已核对的原始来源

检索日期：2026-11-02。下文现代实验不能冒充清代胭脂红碗实测。

## 可见吸收光谱

| 对象与来源 | 已发表曲线与覆盖范围 | 数值、方法与性质 | 可获取文件及限制 |
|---|---|---|---|
| J. M. Fernández Navarro、M. A. Villegas，1992，*Preparation of gold ruby glasses by the sol-gel method*，*Glastechnische Berichte* **65**(2),32–40；DOI：没找到；[TIB原文PDF](https://oa.tib.eu/renate/bitstreams/15d3b9aa-f386-4dc5-aa1f-1f968a937402/download) | **Fig.1,p.34；Fig.2a–d,p.35**：横轴330–810 nm，完整覆盖所需380–780 nm。Fig.3,p.36为前驱体金溶胶，须与固体样品区分。 | **实测**UV–Vis吸收：Perkin-Elmer Lambda 9；样片约1 mm（p.34 §2.3）。Fig.1的Au-2是纯SiO₂溶胶凝胶，配方Au **0.0010 wt%**（p.33,Table1，**配料值，非成品化学实测**）；热处理200/400/600/700°C。正文p.35给Au-2在600°C的带峰 **582 nm（实测光谱）**。 | 本地 `sources/Fernandez_Navarro_Villegas_1992.pdf`；已目视核对 `sources/Navarro_1992_p3.png`（印刷p.34）、`sources/Navarro_1992_p4.png`（p.35）。未找到机器可读原始谱表；未做曲线数字化。此为现代纯硅基质，不能将582 nm直接当作清代铅玻璃彩峰。 |
| H. Takebe、M. Okamoto、K. Mori，2021，*Fabrication of gold ruby glasses using solar panel glass cullet*，*J. Ceram. Soc. Jpn.* **129**(9),590–593，[DOI10.2109/jcersj2.21087](https://doi.org/10.2109/jcersj2.21087) | **Fig.6a–d,p.593：发表的是400–700 nm**，不完整覆盖380–780；实验方法p.592称实际扫描200–2000 nm，间隔及狭缝1 nm。 | **实测**Hitachi U-4100，1 mm厚玻璃，9个位置。图6标峰 **521±7、526±5、533±2、544±2 nm**，对应580/600/620/680°C、10天；**注意正文把末值写成546 nm，与图内544±2不一致，不能悄悄选一个。** 不确定度原文称各位置的scattering range，未说明为标准差。作者称粒径5–15 nm是**引用他人资料推测，非本样TEM测量**。 | [出版社PDF直链](https://www.jstage.jst.go.jp/article/jcersj2/129/9/129_21087/_pdf/-char/en)，本地 `sources/Takebe_2021.pdf`；实际目视核对 `sources/Takebe_2021_p4.png`。没有找到原始数字谱表。现代B₂O₃调节太阳能玻璃，不能移植为清代配方。 |

清代单色胭脂红碗的**380–780 nm绝对反射率数字表：本分工检索没找到**。激光激发的发光谱不是白光反射率/吸收率，不能直接用于反射色校准。

## Au 的体材料 n,k 数据

| 来源 | 数值性质、测量对象和页图 | 获取位置 |
|---|---|---|
| P. B. Johnson、R. W. Christy，1972，*Optical Constants of the Noble Metals*，*Physical Review B* **6**,4370–4379，[DOI10.1103/PhysRevB.6.4370](https://doi.org/10.1103/PhysRevB.6.4370) | **实测反射/透射再反演n,k**，室温真空蒸镀膜，非颗粒、非红彩。原文Table I,p.4374列49个能量点；数据库转为波长 **0.1879–1.9370 µm**。例如数据库Au **λ=0.5209 µm,n=0.62,k=2.081**，**λ=0.5486 µm,n=0.43,k=2.455**（数据库引用原实测，未插值）。 | [refractiveindex.info页面](https://refractiveindex.info/?shelf=main&book=Au&page=Johnson)；[CC0 YAML直链](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/main/Au/nk/Johnson.yml)。已存 `sources/Au_Johnson.yml`；仅换格式、不插值的CSV：`sources/Au_Johnson_nk.csv`，列wavelength_um,n,k。 |
| K. M. McPeak、S. V. Jayanti、S. J. P. Kress、S. Meyer、S. Iotti、A. Rossinelli、D. J. Norris，2015，*Plasmonic Films Can Easily Be Better: Rules and Recipes*，*ACS Photonics* **2**,326–333，[DOI10.1021/ph5004237](https://doi.org/10.1021/ph5004237) | **实测椭偏后求ε**；Fig.4为金属膜介电函数；SI §1A,p.S1–S2为方法。Au是硅模板剥离的热蒸镀膜，10 Å/s、3×10⁻⁸ Torr，非纳米颗粒。官方数表141行，**300–1700 nm、步长10 nm**；Au为第4/5列ε₁/ε₂。**SI方法写400–1750 nm，因此数表300–390 nm超出所述仪器采集区间，原文未解释；仍保留并标注。** | [ACS官方数据页，DOI10.1021/ph5004237.s002](https://acs.figshare.com/articles/dataset/Plasmonic_Films_Can_Easily_Be_Better_Rules_and_Recipes/2049039)；[官方原数据txt](https://ndownloader.figshare.com/files/3620391)已存 `sources/ph5004237_si_002.txt`。[官方SI PDF](https://ndownloader.figshare.com/files/3620403)已存同名文件；[作者稿](https://arxiv.org/pdf/1603.02132)已存 `sources/McPeak_2015.pdf`。[CC0 n,k YAML](https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/main/database/data/main/Au/nk/McPeak.yml)及无插值CSV分别已存 `sources/Au_McPeak.yml`、`sources/Au_McPeak_nk.csv`。 |

McPeak数表本身是ε，数据库n,k是换算数，不是另一次测量。转换关系：ε=(n+ik)²；n=√[(|ε|+ε₁)/2]，k=√[(|ε|−ε₁)/2]（被动介质正k约定）。例如YAML在520 nm给n=0.529126640,k=2.129735899。两套数表都覆盖可见区，**选一套保持自洽，并将bulk Drude项换成粒径修正项**；不能把金属n,k直接赋给整层红彩。

## 小颗粒表面散射：A系数必须连同长度定义引用

基本文献：U. Kreibig、M. Vollmer，1995，*Optical Properties of Metal Clusters*，Springer Series in Materials Science **25**，[DOI10.1007/978-3-662-09109-8](https://doi.org/10.1007/978-3-662-09109-8)。本次没有取得书内相关页全文，**不把“普适A=1”冒充本书实测结论**。以下可直接核查的实验原论文足以支持尺寸修正。

| 原始来源 | 方程与A | 适用对象、证据和性质 |
|---|---|---|
| S. Berciaud、L. Cognet、P. Tamarat、B. Lounis，2005，*Observation of Intrinsic Size Effects in the Optical Response of Individual Gold Nanoparticles*，*Nano Letters* **5**(3),515–518，[DOI10.1021/nl050062t](https://doi.org/10.1021/nl050062t)，[作者原版PDF](https://www.cognet-research.com/uploads/8/8/0/3/88031742/2005nanoletters1.pdf)；本地 `sources/Berciaud_2005.pdf` | **p.517**：γ(D)=γ₀+**2 A vF/D**，即γ(R)=γ₀+A vF/R；**最佳拟合A=0.25**；ħωp=9.0 eV，ħγ₀≈70 meV，vF=1.4 nm/fs为**采用的模型输入/引用值，非该文独立实测**。 | 5/10/20/33 nm金颗粒（尺寸以TEM检验），PVOH/玻璃盖片加硅油环境；建模设nm=1.5（**模型假设**）。Fig.2,p.516为单颗粒515–580 nm吸收实测/模型对照；Fig.4,p.517为峰与宽度随D；A是**实测吸收谱反演的拟合值**，不等于清代玻璃界面的实测A。该文直接观察D≤10 nm的额外展宽。 |

复现修正（推导，不是清代实测）：保持所选体材料表的带间项，使用

`ε_particle(ω,R) = ε_bulk(ω) + ωp²/[ω(ω+iγ_bulk)] − ωp²/[ω(ω+i(γ_bulk+A_R vF/R))]`。

其中频率统一用rad/s；若用eV，两个阻尼项同时乘ħ。**A_R=0.25**是上述特定实验的半径约定，不是可无证据锁定的胭脂红材料常数。不能在原始体材料Drude项上只“再加一个完整Drude项”。对几十nm颗粒还需保留Mie迟滞与辐射散射；对几nm颗粒体材料介电函数加经典表面项仍属模型，不能称已获得真实红彩n,k。

常见“A=0.33”来源检查：Hu et al. 2008的[原作者综述/实验总结](https://pmc.ncbi.nlm.nih.gov/articles/PMC2563424/)在讨论Berciaud时采用 **Leff=4R/3** 的约定，得到A≈0.33；同一物理项转换回R约定是A_R≈0.2475，解释了与原论文0.25的关系（**这里的0.2475为代数换算**）。该综述不作为新增清代参数；最终报告可只保留可核查的Berciaud原始实验0.25和定义，避免多余二手引用。

## 使用边界

清代金红彩基质n、颗粒半径分布和Au浓度尚需由材料分工证据决定。上述资料解决“有无完整可见吸收图”和“金的体n,k怎样取得、粒径修正怎样写”；它们没有给出清代碗的绝对反射光谱、红彩粗糙度、厚度或统一A。没有这些资料时不从照片反推唯一物理参数。
