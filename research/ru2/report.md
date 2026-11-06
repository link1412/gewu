# 汝窑天青釉第二轮：可计算的化学和光学数据

检索日期：2026-10-29。第一轮：`../ru/report.md`。

## 0. 推荐方向、完成标准与实际交付边界

推荐先建立有版本和样品身份的光谱计算输入：铁的分价态吸收、两玻璃相折射率、晶体各向异性折射率、结构尺寸分别输入；用同一片的成分、厚度、价态和反射谱验证。钠钙玻璃的铁吸收谱可做迁移假设，不能直接称汝釉参数。Zhou 的两相 EDS 比整体组成更适合估算折射率差，但纳米相的 SEM-EDS 混相误差仍是关键限制。

可检查的标准：六项需求逐项有结果或“没找到”；数值注明样品、单位、源表/图、实测或推算；本地数值文件能重新读入；原图与论文必须有真实文件才能算下载完成。

**实际状态：已交付数值转录/重建 CSV 与来源记录；原始 PDF、论文原图和馆藏最高分辨率照片的下载受阻，不能算完成。** 只读到部分原文，没有原始二进制文件。`files/` 内 CSV 是本轮转录或计算产物，不是作者发布的原始数据。不要把网址清单当成已下到的文件。

数据性质约定：**论文实测**包含 XRF/EDS 结果；**论文拟合重建**指本轮按作者公式和参数生成；**本轮推算**需额外假设；**不确定**表示适用性或读图未核；**没找到**不等于文献从未存在。

## 1. 铁离子吸收数据

**本项已得到可计算的钠钙玻璃 Fe²⁺ 谱，以及 Fe³⁺ 高斯参数表；未得到汝釉/纯钙铝硅酸盐的独立 350–1100 nm 摩尔吸收全谱。** 

### 1.1 钠钙玻璃：实际数值，能重建曲线

来源：[Volotinen, Parker & Bingham (2008), *Phys. Chem. Glasses B* 49(5), 258–270，作者上传全文](https://www.researchgate.net/publication/233587586_Concentrations_and_Site_Partitioning_of_Fe2_and_Fe3_Ions_in_a_Soda-Lime-Silica_Glass_Obtained_by_Optical_Absorbance_Spectroscopy)；[大学正式书目](https://shura.shu.ac.uk/5707/)。Table 3（p.263）实际参数已转录至 [files/iron_Volotinen2008_table3_transcribed.csv](files/iron_Volotinen2008_table3_transcribed.csv)。授权：论文版权保留；作者公开全文不等于开放许可；CSV 为来源事实的转录，非下载的论文原件。

基玻璃 **15Na₂O–15CaO–70SiO₂，mol%**；Table 3 适用添加 **0.05–0.5 mol% Fe₂O₃** 的电炉玻璃。价态通过光谱拟合提取；Fe²⁺ 强度借用 Bamford 在 1000 nm 的 **ε=30 L mol⁻¹ cm⁻¹** 定标，对应 **S=11.920 (cm·mol%)⁻¹**，并非每个波长都独立作湿化学绝对标定。作者明确绝对准确度仍需校准。

表内 ν₀、σ 单位 cm⁻¹，H 单位 (cm·mol%)⁻¹；全部为**论文拟合参数**，不是本轮测量：

|峰|ν₀|σ|H|
|---|---:|---:|---:|
|p1 Fe²⁺ 四配位|3590|700|2.065|
|p2 Fe²⁺ 四配位|4950|660|3.183|
|p3 Fe²⁺ 六配位|7490|1430|5.198|
|p4 Fe²⁺ 六配位|10380|2390|10.944|
|p5 Fe²⁺ UV|46700|5700|1000|
|p6 Fe³⁺ 四配位|21550|1350|0.218|
|p7 Fe³⁺ 四配位|22740|650|0.270|
|p8 Fe³⁺ 四配位|24020|650|0.323|
|p9 Fe³⁺ 四配位|26220|480|0.959|
|p10 Fe³⁺ 六配位|14700|1700|0.310|
|p11 Fe³⁺ 六配位|18350|2000|0.210|
|p12 Fe³⁺ 六配位|25190|530|0.255|
|p13 Fe³⁺ 六配位|27250|530|0.098|
|p14 Fe³⁺ UV|39360|3050|1900|

按 Eq.2，`P_i(ν)=H_i exp[-(ν−ν₀ᵢ)²/(2σᵢ²)]`，`ν=10⁷/λ_nm`。**本轮推算**：Fe²⁺ 取 p1–p5 之和，以 `30/11.920` 换算为 L mol⁻¹ cm⁻¹；已保存 [350–1100 nm、1 nm 步长 CSV](files/iron_Volotinen2008_reconstructed_350_1100nm.csv) 及 [重建脚本](files/iron_reconstruct_volotinen.py)。1000 nm 计算 ε=30.001，回到论文定标30（差异为表格舍入）。这套谱是实验拟合曲线重建，不能称作本轮取得的原始测量谱。


抽查用谱值（**本轮按上述论文拟合参数重建**，并非新的实测）：

| λ/nm | Fe²⁺ ε / L·mol⁻¹·cm⁻¹ |
|---:|---:|
| 350 | 16.0082 |
| 380 | 4.20474 |
| 400 | 1.79328 |
| 450 | 0.249211 |
| 500 | 0.0516295 |
| 550 | 0.142918 |
| 600 | 0.868467 |
| 650 | 3.07597 |
| 700 | 7.24664 |
| 800 | 18.6134 |
| 900 | 26.8146 |
| 1000 | 30.001 |
| 1100 | 30.8057 |

**Fe³⁺ 归一化仍有不确定性，CSV 故保留分量而不伪造唯一答案**：正文 Eq.1 的四/六配位混合系数 nₜ 在定标处写0.5，但 p.263 对380 nm的归一化强度又报告约1.19（含UV）及0.94（不含UV）；逐项表值求和更接近未再乘0.5的结果。CSV同时给出按公式 nₜ=0.5 的谱与直接表值求和谱，这不是可信区间，也不是两种独立实测；应核对论文原PDF/联系作者后解决归一化再作绝对颜色预测。图4图例与表3的配位标签也有不一致；此处采用表3标签。Fe²⁺ 定标无此问题。

以上模型采用十进制吸光度；用于传输方程 `exp(-μ_a L)` 时须令 `μ_a=ln(10) ε c`，c 单位 mol/L，L 单位 cm。不能把其数值直接与自然指数吸收系数相加。

### 1.2 接近石灰铝硅酸盐：E-glass 的可靠点值和可描图位置

原始来源：[Klement, Kraxner & Liška (2009), *Ceramics–Silikáty* 53(3),180–183，PDF](https://www.ceramics-silikaty.cz/2009/pdf/2009_03_180.pdf)；[期刊摘要](https://www.ceramics-silikaty.cz/2009/2009_03_180.htm)。版权：期刊原文；本轮未找到明确开放许可。

**论文实测校准** εFe²⁺(1000 nm)=**15.99 ± 0.09 L mol⁻¹ cm⁻¹**。基玻璃 Center(0.25)，mol%：SiO₂57.27、B₂O₃4.59、Al₂O₃8.96、CaO26.49、MgO2.44、Fe₂O₃0.25（Table1）。它含硼，不能当纯CAS。Table2：该片总铁折Fe₂O₃为0.712±0.001 wt%；[Fe²⁺]=0.061±0.005 mol/L、[Fe³⁺]=0.180±0.004 mol/L、Fe²⁺/ΣFe=0.25±0.02。价态：湿化学1,10-phenanthroline络合分光光度法。板厚1–2 mm，300–2200 nm测量，修正反射并归一到1 cm。

**可描图已定位、原图未取得**：Fig.1（PDF第2页/p.181）为7样品的UV–VIS–NIR实验吸收；Fig.3（第3页/p.182）为5000与10000 cm⁻¹附近分峰。web文本可核验，但截图返回Cache miss，不能冒称已下载，也未臆读图上点值。Fe³⁺380 nm峰被电荷转移吸收遮盖，论文明确不能定其强度；**Fe³⁺独立摩尔全谱：没找到**。

### 1.3 更适合描取的原始谱来源（未取得文件）

1. [Uchino et al. (2000), DOI 10.1016/S0022-3093(99)00617-1，公开案卷中的原论文PDF](https://s3-us-west-1.amazonaws.com/ptab-filings%2FPGR2024-00039%2F1078)。Fig.1（p.74，PDF第3页）有 Fe²⁺(6)、Fe³⁺(4) 的波长谱，Fig.2（p.76，第5页）是经验缩放的 Fe³⁺(6) 项。基玻璃 wt%：SiO₂71.9、Al₂O₃1.4、MgO3.8、CaO9.1、Na₂O13.8。Fe²⁺湿化学、总Fe以XRF定，板厚5 mm；200–2100 nm。**纵轴不是摩尔ε**，是 wt%⁻¹ mm⁻¹，论文传输式用自然指数。六配位Fe³⁺项带未知配位浓度比例k；不能当绝对摩尔谱。PDF版权©2000 Elsevier、all rights reserved；案卷公开不改变版权。已web核读，未成功下载/截图。
2. [Vercamer (2016)博士论文，*Spectroscopic and Structural Properties of Iron in Silicate Glasses*](https://ustverre.fr/wp-content/uploads/2025/09/PhD-thesis-Vercamer-1.pdf)，[HAL记录](https://theses.hal.science/tel-01458771)。Appendix B，Fig.B.8（印刷页210）直接给出 NCS05 的 Fe²⁺、Fe³⁺ 摩尔吸收谱，纵轴 cm⁻¹·L·mol⁻¹，横轴波数cm⁻¹、上轴波长nm；**Fe³⁺画线乘了10**。Fig.B.7为线性吸收系数，不能混用。三种氧化还原样品线性分离、先扣背景和UV边缘，故B.8不能作为含氧→铁电荷转移尾部的总吸收。**完整基玻璃组成、原图与精确逐点值：本轮没取得**。授权未找到。17.8 MB PDF超出web抓取上限，HAL访问受阻。

### 1.4 IVCT、青瓷薄片

- **Fe²⁺–Fe³⁺ IVCT的绝对摩尔吸收谱350–1100 nm：没找到。** [Bingham et al. (1999), *Redox and clustering of iron in silicate glasses*](https://shura.shu.ac.uk/5858/) 的原始研究摘要确认70SiO₂–15Na₂O–15CaO(mol%)、0.1–5 mol%Fe₂O₃玻璃中随铁增多出现的可见吸收与 Fe²⁺–O²⁻–Fe³⁺相互作用相关；但本轮未取得可独立量化该项的曲线/配对浓度。不能给它随意套一个单离子ε，更不能把所有约700 nm弱峰都叫IVCT。
- **青瓷釉薄片已知厚度透射率T(λ)或本征吸收系数μa(λ)：没找到。** 不能以釉面漫反射“absorbance”替代薄片透射。
- 相关但不满足薄片条件：[Ren et al.(2026), DOI10.1038/s40494-026-02383-0](https://www.nature.com/articles/s40494-026-02383-0)。南宋郊坛下官窑，Fig.5b、200–2300 nm Cary7000积分球釉面“吸收谱”；1075 nm峰等仅作作者归属参考。论文未给摩尔ε，方法是釉面，不是已知光程的透射；**此谱不能直接反演μa**。页面标为Open access；本轮未核验具体许可版本，授权没找到。图文件本轮未取得。

### 1.5 下载限制与已落盘文件

未把失败下载保存为PDF。已成功落盘的是**转录/计算文件**而非PDF/图原件：

- `files/iron_Volotinen2008_table3_transcribed.csv`：14行论文拟合参数及表内±误差。
- `files/iron_Volotinen2008_reconstructed_350_1100nm.csv`：751行推算谱，明确Fe³⁺归一化歧义。
- `files/iron_reconstruct_volotinen.py`：可复算脚本，内含1000 nm定标检查。

应用到汝釉的限制：钠钙基质和汝釉组成不同；E-glass点值与钠钙定标就相差接近二倍。该文件应作为敏感性分析或初始模型，不能冒称汝釉的成分特定吸收常数。

用于后续模型的单位推导（本轮推算，非新测值）：若密度ρ以g/cm³、p为氧化物的**wt%数值**，则 `[Fe²⁺]=10ρp_FeO/M_FeO`、`[Fe³⁺]=20ρp_Fe2O3/M_Fe2O3`，单位mol/L；仅当这些p分别是真正分价态氧化物含量时成立。XRF“总铁折Fe₂O₃”须另乘独立测得Fe²⁺/ΣFe比例来分配，不能把它全部算成Fe³⁺。这里ρ、价态比例与汝釉特定ε都不能从现有钠钙基质数据臆定。

## 2. 清凉寺北宋汝釉、胎与分相组成

### 2.1 Zhou 2023：整体及图4两相

以下全部为**论文实测、氧化物模式报告，单位 wt%**；逐行来源为 [Zhou et al. 2023](https://doi.org/10.3390/coatings13061011) 表1、2，清凉寺出土 R1/R2。`—` 是原表短横，不自行当零。CSV：[zhou2023_compositions_wt.csv](files/zhou2023_compositions_wt.csv)。表中 Fe₂O₃ 是总铁的报告形式；XRF/EDS 不分 Fe²⁺/Fe³⁺，并非真正的全三价测量。

| 样品/测点（源表） | Na₂O | MgO | Al₂O₃ | SiO₂ | P₂O₅ | K₂O | CaO | TiO₂ | MnO | Fe₂O₃* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R1釉（表1） | 0.8 | 2.2 | 16.4 | 59.5 | 0.4 | 3.2 | 15.2 | 0.2 | 0.1 | 1.9 |
| R2釉（表1） | 0.5 | 2.0 | 16.3 | 60.3 | 0.4 | 3.6 | 14.7 | 0.2 | 0.2 | 1.9 |
| R1胎（表1） | 0.2 | 0.6 | 29.1 | 64.2 | — | 1.3 | 1.4 | 1.2 | — | 2.0 |
| R2胎（表1） | 0.2 | 0.7 | 27.3 | 65.7 | — | 1.5 | 1.6 | 1.2 | — | 1.9 |
| R1 钙长石 EDS1（表2） | 1.0 | 1.1 | 28.5 | 50.3 | 0.0 | 0.9 | 17.4 | 0.1 | 0.1 | 0.6 |
| R1 富硅相 EDS2（表2） | 1.1 | 1.4 | 12.8 | 67.5 | 0.3 | 4.8 | 10.4 | 0.2 | 0.0 | 1.6 |
| R1 富钙相 EDS3（表2） | 0.5 | 2.5 | 11.0 | 62.7 | 0.7 | 3.0 | 16.7 | 0.4 | 0.1 | 2.5 |
| R2 成排富钙小滴 EDS2（表3） | 0.8 | 3.0 | 10.1 | 59.6 | 0.1 | 3.5 | 20.0 | 0.3 | 0.2 | 2.5 |

原文 §2.2：SEM-EDS 为 15 kV、低真空60 Pa、工作距离10 mm、采集30 s，P/B-ZAF 定量。§3.1.2明确指定表2 EDS2/3分别为富硅/富钙；钙长石用形貌、EDS和 Raman 联合判断。**不确定性**：几十至数百 nm 的相小于通常15 kV SEM-EDS作用体积，测点可能含邻相；上述不是已验证的纯相端元。R2成排小滴中 TEM/SAED 发现硅灰石，不能无条件当作全非晶滴。

### 2.2 Shi 2020：另一批清凉寺古片

以下为**论文 XRF 实测，wt%**；来源 [Shi et al. 2020](https://doi.org/10.1016/j.ceramint.2020.06.139) 表3，预印PDF第15页（文件页）。四片均由北京故宫提供的清凉寺出土古片；R1/R2为天青，R3绿黄、R4天绿。它们与 Zhou 的同名 R1/R2 **不是同一片**。CSV：[shi2020_compositions_wt.csv](files/shi2020_compositions_wt.csv)。

| 样片 | Na₂O | MgO | Al₂O₃ | SiO₂ | K₂O | CaO | TiO₂ | Fe₂O₃* | P₂O₅ | MnO₂ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R1 | .02 | 1.97 | 14.08 | 70.65 | 2.58 | 8.26 | .16 | 1.54 | .63 | .11 |
| R2 | .37 | 2.00 | 14.79 | 71.63 | 2.44 | 6.52 | .13 | 1.48 | .52 | .12 |
| R3 | .35 | .93 | 12.27 | 74.35 | 1.90 | 7.59 | .18 | 1.87 | .39 | .17 |
| R4 | .10 | 1.09 | 11.56 | 75.24 | 1.82 | 8.24 | .11 | 1.20 | .52 | .12 |

同文 §3.3、图8b的表面 XPS 拟合 Fe²⁺/Fe³⁺原子百分比分别为 **57.41/42.59、66.37/33.63、42.26/57.74、46.71/53.29**（论文实测拟合）。**分开化学测得的体相 FeO、Fe₂O₃：没找到。** 为便于核查单位，附 [conditional_split CSV](files/shi2020_surface_redox_and_conditional_split.csv)：仅在“表面比例等于体相比例”假设下，用 `FeO = T × f₂ × 2M(FeO)/M(Fe₂O₃)`，`Fe₂O₃ = T × (1−f₂)`计算。它是**本轮条件推算，不推荐作为体相实测输入**；不能把该比例挪到 Zhou 两相中。

[Li et al. 2005](https://doi.org/10.1016/j.ceramint.2004.07.002) 的 N1–N6 属清凉寺第四烧造区，报告胎 Al₂O₃ **25.91–28.95 wt%**、SiO₂ **62.48–65.95 wt%**（论文实测范围，§3.1）。本轮未找到其逐片全氧化物wt%表，不把 Seger 摩尔式冒充wt%。[Chen 2020](https://doi.org/10.1002/ces2.10058) 表1是复烧配方，FeO=1.31 wt%不属于其古片的分价态化学实测，故未混入上表。

## 3. 折射率与色散

### 可直接用于计算的钙长石数据

**已找到三个主折射率的逐波长实测表**。O. Medenbach & R. D. Shannon (1997), *Refractive indices and optical dispersion of 103 synthetic and mineral oxides and silicates measured by a small-prism technique*, JOSAB 14, 3299–3318, DOI [10.1364/JOSAB.14.003299](https://doi.org/10.1364/JOSAB.14.003299)。[出版社表6、表7及样品表](https://opg.optica.org/josab/abstract.cfm?uri=josab-14-12-3299)。数据已人工转录为 [CSV](files/index_anorthite_measured_Medenbach1997.csv)，不是下载的论文附件。

| λ / nm | nα=nx | nβ=ny | nγ=nz |
|---:|---:|---:|---:|
|643.8|1.5719|1.5805|1.5852|
|576.9|1.5749|1.5835|1.5883|
|546.0|1.5769|1.5853|1.5901|
|508.6|1.5794|1.5880|1.5928|
|480.0|1.5817|1.5904|1.5953|
|468.0|1.5831|1.5916|1.5965|
|435.8|1.5867|1.5952|1.6002|
|404.7|没找到（表空白）|1.5992|1.6052|

以上为**论文实测**，小棱镜法、Hg–Cd灯，作者估计 n 的不确定度 ±0.0002（摘要）。样品为 Great Sitka Island, Alaska 无色天然钙长石；表1化学式网页版显示 Ca0.96Na0.05Al1.93Fe0.02Si2.0O8（2002汇编写 Si2.04，故完整化学式存在不同转录，未自行修正）。它是光学参考矿物，**不是汝釉原位钙长石的测量**。

论文以 `1/(n²−1)=−A/λ²+B` 单项 Sellmeier 拟合。表7给 **论文推算** 的 589.3 nm 三轴 n 为 1.5743、1.5829、1.5876；λ→∞为 1.5600、1.5689、1.5729；平均 A=72×10⁻¹⁶ m²，平均 B=0.6867。**A和B是三个主轴的平均，不能把这对平均系数分别当作三轴的系数。** 如需三条连续曲线，可分别拟合表6，必须标为“本文对论文数据再拟合”。这里未外推到350或1100 nm；350–404.7、643.8–1100 nm的三轴实测值**没找到**。

授权：论文页 ©1997 Optical Society of America，明确开放再用许可**没找到**。CSV为科学事实数据转录；论文PDF未能下载，未将网页摘要假装成PDF。


### 三轴连续曲线的可复现再拟合（本文推算）

另保存 [拟合脚本](files/index_fit_anorthite.py) 与 [系数CSV](files/index_anorthite_Sellmeier_refit.csv)。用表6逐轴对 `1/(n²−1)` 关于 `−1/λ²` 做无权最小二乘；**λ用μm，A单位μm²，B无量纲**，解出 `n(λ)=sqrt(1+1/(B−A/λ²))`。

|主轴|A / μm²|B|最大绝对n残差|采样区间 / nm|
|---|---:|---:|---:|---|
|α|0.00732387370241|0.697466266239|0.000161|435.8–643.8|
|β|0.00694790121851|0.684148087867|0.000268|404.7–643.8|
|γ|0.00719232937106|0.678408944507|0.000190|404.7–643.8|

以上**不是作者发表的逐轴系数**，只用于实测区间内插值；β轴最大拟合残差略大于作者±0.0002测量估计，故不能宣称这次单项拟合达到比该值更高精度。无需用平均A/B覆盖各轴；原始CSV保留所有采样值供重选插值法。未把拟合在350–1100 nm的数学外推作为已知实测色散。


### Appen：找到可运行的nD加和式，但没有完整汝釉/分相专用色散表

Duminis, Shahid, Karpukhina & Hill (2018), *Predicting refractive index of fluoride containing glasses for aesthetic dental restorations*, Dental Materials 34 e83–e88, [DOI](https://doi.org/10.1016/j.dental.2018.01.024)，[作者机构存档PDF地址](https://qmro.qmul.ac.uk/xmlui/bitstream/handle/123456789/48883/Duminis%20et%20al.%202018.%20Predicting%20refractive%20index.pdf?sequence=1)。检索索引可读 eq.1 / Table1，直接文件请求返回失败。其式为

`nD = Σ(C_i × f_i)/100`，`C_i=100(w_i/M_i)/Σ(w_j/M_j)`。

这里 w 为氧化物质量（可wt%，先换摩尔），M为氧化物摩尔质量，C为**氧化物mol%**；f为**加和因子**，无量纲，不等于纯氧化物晶体折射率。表1：SiO2 1.4585；Al2O3 1.52；P2O5 1.31；Na2O 1.575；ZnO 1.71；K2O 1.575；CaO 1.73；SrO 1.775。人工转录 [CSV](files/index_Appen_Duminis2018.csv)。Na、Si取值与其他版本有差异，故保留版本来源，不拼成“完整Appen原始表”。FeO、Fe2O3、MgO、TiO2的本表系数**没找到**，不能用该8项表无说明地计算完整汝釉。

本研究在约20°C用钠D线Becke line法测量牙科玻璃，作者“within 0.005”是对其**系列专用含氟修正**的准确度，**不是古汝釉或通用Appen模型的误差保证**。来源 [PubMed原文摘要](https://pubmed.ncbi.nlm.nih.gov/29402539/)。其λ连续色散系数**没找到**。

[INTERGLAD Ver.7 官方手册2018，pp.9–10](https://www.interglad.jp/interglad7/doc/interglad7manual6_14e.20180201.pdf)明确列有室温 Appen nD 与Abbe数模型；含B2O3时SiO2需44–64或71–80 mol%；含TiO2时总R2O<15 mol%、SiO2 50–80 mol%；含CdO或PbO时SiO2+Al2O3+B2O3≥50 mol%。来源书Appen *Kimiya Stekla*, Leningrad 1974。手册此次可读，但**17氧化物的完整系数表没找到**；不能据名称就声称色散可算。

#### 另一个明确的 Appen 系数版本（不可与上表静默混用）

Queen Mary University of London 发明人的 [EP3013762B1 *Leucite glass ceramics*](https://patents.google.com/patent/EP3013762B1/en)，说明书 Appen factor 表给：Al2O3 1.520；CaO 1.730；Na2O **1.590**；Li2O 1.695；MgO **1.610**；K2O **1.575**（Na2O<1 mol%用 **1.595**）；SiO2 **1.475**（SiO2≤67 mol%），在67–100 mol%时为 `1.5085−0.0005 pSiO2`；TiO2在50–80 mol%SiO2条件下为 `2.480−0.005 pSiO2`（2.230–2.080）。p是**mol%**，说明书最后一句明确需从重量换成摩尔。网页Si公式右端误排为nSiO2，Ti末式误排为α，但文字与范围足以识别；应保留误排说明，不能宣称直接核对过原版Appen书。

该专利提供组成依赖Si/Ti以及Mg因子，较适合作低硼硅酸盐的**估算版本**；但缺FeO/Fe2O3因子、无色散及古汝釉验证误差。**完整两相n(λ)目前仍算不齐**。专利公开不等于图片取得CC许可；PDF未下载。

专利版 Appen 因子的机器可读表达式及适用条件已另存 [CSV](files/index_Appen_EP3013762B1.csv)，不补入Fe因子。用这个版本时应单独报告被剔除/缺失氧化物的总wt%和mol%，**不得静默去铁后归一化，再把结果称作完整釉相nD**。

### Huggins：已定位原始数值表；连续全谱公式仍待核原文

原始系列：
- Huggins 1940 [Density, JOSA30,420–430](https://doi.org/10.1364/JOSA.30.000420)：`V_O=k+bSi+cSi N_Si+Σ c_M N_M`，N为每个氧原子的阳离子数；k依退火历史。
- Huggins1940 [Refractive index, JOSA30,495–504](https://doi.org/10.1364/JOSA.30.000495)：每摩尔氧的折射加和，表2aM用于Gladstone–Dale式；表3a'M用于Newton式，**两组不可混用**。
- Huggins1940 [Dispersion, JOSA30,514–518](https://doi.org/10.1364/JOSA.30.000514)：增加一个元素常数可算可见色散；其优质体系中 nF−nC平均差约(5–8)×10⁻⁵（论文摘要），不是汝釉误差。
- Huggins, Sun & Davis1942 [Dispersion II, JOSA32,635–650](https://doi.org/10.1364/JOSA.32.000635)：加入通用项和Ca/Ba/Pb修正；表1完整数值在出版社检索索引可读。
- Huggins & Sun1943 [Calculation of density and optical constants of a glass from its composition in weight percentage, JACerS26,4–11](https://doi.org/10.1111/j.1151-2916.1943.tb15176.x)：wt%等价表达，非1941（INTERGLAD手册这条年份疑误）。

Fantone1983 [Applied Optics22,432–440](https://doi.org/10.1364/AO.22.000432) 表I、II、V在出版社网页可读，重列Huggins的体积与折射常数。表V包括Ca'、Ba'、Pb''修正行；仅拿主行线性相加会丢掉原模型机制。**此次没有核到完整公式与g/d单位缩放，不把它包装成已验证的连续波长求解器**。原始表主要针对透明硅酸盐玻璃，铁为FeIII，FeII无对应常数；汝釉的混合价态、吸收共振及分相不能只用这一套实部n加和模型概括。

Fluegel：找到的glassproperties公开模型为粘度/密度等；**没有找到带可核系数的Fluegel折射率/色散模型**。不拿Fluegel密度模型冒作n模型。

### 1940版的D线与F−C色散加和因子（有密度时可用）

Huggins1940色散论文**表I**逐项转录于 [CSV](files/index_Huggins1940_D_FminusC.csv)，主要项 `(aD, aF−C)`：Si(12.506,0.18355)、Na(6.019,0.1564)、K(9.53,0.2032)、Mg(8.7,0.18)、Ca(12.64,0.2689)、Al(10.7,0.16)、FeIII(33.0,10.0)，体积因子按cm³/mol阳离子的克原子基准使用。这组保留1940版，**没有拼入1942版修正项**。

把Huggins1940折射论文摘要描述的Gladstone–Dale加和关系用现代摩尔记号重写，可计算两个光学量（这是**公式代数重写**，不是新的实测）：

```
q_i = w_i / M_i
Q_O = Σ_i y_i q_i                         # 氧化物MxOy的氧原子摩尔数
N_M = x_i q_i / Q_O                       # 每mol氧的M阳离子mol数
V_O = (Σ_i w_i / rho) / Q_O               # cm3/mol O；rho用g/cm3
n_D = 1 + Σ_M a_D,M N_M / V_O
n_F - n_C = Σ_M a_F-C,M N_M / V_O
V_D = (n_D - 1)/(n_F - n_C)
```

质量w用g；wt%以100g为基准即可。D=589.294 nm、F=486.133 nm、C=656.273 nm（[HOYA官方谱线表](https://www.hoya-opticalworld.com/english/technical/002.html)）；D与He d=587.562 nm应区分。这套1940加和式在已知密度时可运行；仅有氧化物组成，还需要密度预测模型。它仅给D线n和F−C差值；**不能由二者唯一恢复350–1100 nm全谱**。有FeII时缺系数，不能把FeIII因子套给FeII。高FeIII项靠近强吸收导致大色散，对古釉的可信误差**没找到**。Huggins1940实验拟合误差只应按其原测试体系解释。

### 文件获取状态

本项仅落盘转录/计算CSV和脚本。原始论文及手册未下载，实际请求结果见 `files/download_attempts.json`。

## 4. 贾翠等2016图5、6：裂纹测量


原文：贾翠、张雪雁、丁银忠、陈铁梅，《无损分析方法在宋代冰裂纹青瓷研究中的应用》，《故宫学刊》2016（总第十七辑），303–309。[院方论文页](https://www.dpm.org.cn/research_talk/252220.html)；[院方 PDF](https://www.dpm.org.cn/Uploads/File/2020/03/31/u5e82bd5beacda.pdf)。2020 是文件上传年份，不能据此更改出版年。

检索系统能返回原文 p.305 和 p.307 的文字；本轮 PDF 本体始终超时，未见到图 5、6 图像或坐标，因此不能从图推数。

| 所求 | 结果及证据等级 |
|---|---|
| 图 5 的对象 | **原文报告**：5a 为清凉寺汝官窑，5b 为老虎洞官窑；5a1/a2、5b1/b2 是相应的 ImageJ 处理图。汝片光学观察放大 **10 倍**。来源 p.307。放大倍率不是可用于长度换算的标尺。 |
| 裂纹层级 | **原文观察**：较大而深的网状直裂纹包围区域内，有更细、白边、不规则、层叠的冰裂纹；汝片花瓣状向交汇处层叠，官窑片偏鱼鳞状同向。来源 p.307。 |
| 图 6 | **原文报告**：OLS4000 激光共聚焦的汝官窑冰裂纹表面形貌、表面起伏测量。不能把釉面高度差直接叫贯穿裂纹深度。来源 p.307。 |
| 裂纹宽、贯入深、倾角、细纹间距、胞大小 | **没找到可核数字**；图 5、6 未核读。不是证明论文没有数字。 |
| 图内坐标及单位 | **没找到**；正文说取得微米级数据，不足以核定某图横纵轴量程、单位和数值。 |
| 原图/PDF 文件与许可 | **未下载成功**。院方提供公开阅读；没找到开放再利用许可，不标 CC。 |

样品来源 p.305：清凉寺窑出土的三片天青冰裂纹及一片天青直裂纹汝官窑对照；官窑来自老虎洞。该样品身份由论文报告，不是据照片认定。


## 5. 汝釉反射谱与原图状态

**作者原始数值反射谱 CSV：没找到。指定三篇的最高分辨率原图：本轮未下载成功。** 下面是定位结果，不声称已完成描谱。

| 来源/位置 | 坐标、样品和方法 | 原文件与授权 | 状态 |
|---|---|---|---|
| [Zhou 2023 图10a](https://www.mdpi.com/2079-6412/13/6/1011) | 横轴波长380–700 nm；纵轴反射率%；R1/R2内外表面4曲线。Ci64、4 mm孔径；SCI/SCE等具体设置没找到 | [出版方PNG](https://www.mdpi.com/coatings/coatings-13-01011/article_deploy/html/images/coatings-13-01011-g010.png)，无550缩略后缀；作者CC BY 4.0 | 原图请求429/Cache miss；像素、纵轴刻度范围没核到，不能称全站最高；未造数值 |
| [Chen 2020 图3、图4](https://ceramics.onlinelibrary.wiley.com/doi/full/10.1002/ces2.10058) | 文件第4页/刊页180。B面板均500–700 nm；A全范围、纵轴确切名称/刻度/单位没核到。古片与复烧对照，不能把每条曲线当古汝。SE1020C-025-DUVN、卤素灯 | [出版方PDF](https://ceramics.onlinelibrary.wiley.com/doi/pdf/10.1002/ces2.10058)；[图3导出入口](https://ceramics.onlinelibrary.wiley.com/action/downloadFigures?doi=10.1002%2Fces2.10058&id=ces210058-fig-0003&partId=)，[图4导出入口](https://ceramics.onlinelibrary.wiley.com/action/downloadFigures?doi=10.1002%2Fces2.10058&id=ces210058-fig-0004&partId=)；作者CC BY 4.0 | PDF正文可读、二进制未落盘；导出图请求失败。绝对标定、白板、采集几何没找到，不当绝对albedo |
| [Shi 2020 图8a](https://doi.org/10.1016/j.ceramint.2020.06.139) | UV–vis–NIR **吸收谱**，不是反射谱；文件第18页。Cary5000；纵轴完整单位与厚度/反射校正没核到 | [预印PDF](https://wiki.glazy.org/uploads/short-url/a4OBSHFfZKh3GDKeTng8taj61g5.pdf)，Elsevier版权声明；自由复用授权没找到 | 本文的反射谱图没找到；不能将图8a当μa或ε直接输入 |

Zhou 图10为腐蚀出土片的表面结果；不能和无腐蚀传世器照片混作同一验证目标。陈文图3/4的实测强度也不能仅因题名有 reflective 就补写成反射率百分数。Zhou 表4的主波长不是逐波长反射率，也不能用它重建唯一光谱。

## 6. 台北故宫指定器与薄粉厚绿候选近照


下表尺寸均为**馆方公布**，cm；不是照片推算。照片没有光谱轴、没有标尺及色卡，不能替代反射率测量；器物直径也不能直接给透视照片的全图统一比例。

| 器物 | 官方记录、尺寸 | 薄釉粉/积釉绿的证据 | 图像交付现状 |
|---|---|---|---|
| 故瓷005176N000000000 汝窯 青瓷洗 | [官方 27528](https://digitalarchive.npm.gov.tw/Collection/Detail/27528?dep=U)：高 **4.7**、口径 **15.9**、底径 **13.4** | 馆方说明周壁较薄、底稍厚，天青釉局部微粉色。不能由此推定每个粉区都是厚度造成。 | main imageId **393663**，另取 393664、393665 直链；未取得二进制，像素没找到。 |
| 故瓷013962N000000000 汝窯 青瓷盤 | [官方 37](https://digitalarchive.npm.gov.tw/Collection/Detail?dep=U&id=37)：高 **3.3**、口径 **18.4**、足径 **12.7** | 馆方明确记载积釉偏绿、薄釉透胎呈粉红；最匹配目标。 | main imageId **393828**，另取 393829 直链；未取得二进制，像素没找到。 |
| 故瓷018182N000000000 汝窯 青瓷盤 | [官方 61067](https://digitalarchive.npm.gov.tw/Collection/Detail/61067?dep=U)：高 **3.2–3.7**、口径 **14.9**、足径 **10.8** | 馆方明确记口沿釉薄处淡粉红、全器淡碧浅粉二色。 | main imageId **391458**；只能列为待下载、待视觉验收候选。 |
| 故瓷017855N000000000 汝窯青瓷盤 | [官方 1766](https://digitalarchive.npm.gov.tw/Collection/Detail/1766?dep=U)：高 **4.6**、口径 **21.5**、足径 **15.7** | 馆方记釉薄处微粉，内壁底缘积釉有冰裂纹；未明确该处绿色，不能替馆方补写。 | main imageId **400715**；待下载与视觉验收。 |
| 故瓷018048N000000000 汝窯 青瓷洗「奉華」銘 | [官方 33](https://digitalarchive.npm.gov.tw/opendata/Pub/Detail/33?dep=U&mode=full)：高 **2.3**、口径 **12.7**、底径 **10.1** | 馆方记粉青釉局部粉色光泽；未给厚度对应，不当作已证明的薄粉厚绿例子。 | main imageId **391952**；待下载与视觉验收。 |

### 分辨率、授权及下载边界

以上数字典藏记录统一明确：**100 万像素低阶图 CC0；600 万像素中阶图 CC BY 4.0；文字 CC BY 4.0**。馆方“关于本站”说明 IIIF 可浏览 600 万像素图（61067 页面“使用方式”）。这是平台公开档位，不代表本轮已取得600万像素，亦不是相机底片最高分辨率证明。姓名标示：`汝窯 青瓷盤／洗，國立故宮博物院，臺北，CC BY 4.0 @ www.npm.gov.tw`。授权来源为各馆藏页的“網站資料開放宣告”。

本轮只读到馆方文字，GetImage 返回 Forbidden/Cache miss。因此**没有实际下载的 JPG/PDF，也没有逐像素验证照片的薄粉厚绿效果**。中阶下载弹窗另有验证码，本轮未提交。未提供虚假的像素或“最高分辨率已下载”结论。可重取线索保存于 `files/npm_download_manifest.tsv`，不能当成已下载图像目录。

IIIF viewer 入口已由院方页面点击获得，见 manifest；真正 IIIF JSON manifest 地址**没找到**，不要将 viewer URL 冒称 manifest JSON。

## 7. 建模用法与仍缺的实验约束

本轮建议的计算接口（**本轮方案**）：将 `μa(λ)` 与 `μs(λ)` 分开；用玻璃相局部铁浓度及价态计算吸收，再结合分相、晶体和气泡散射解有限厚层的光输运。先做样品内验证，再做跨样品比较。折射率组成模型输出是估计；相折射率差在弱对比散射中影响很大，需传播其不确定性。

从十进吸光度到自然指数吸收：若 `A₁₀ = ε c l`，c为mol/L、l为cm，`μa[cm⁻¹] = ln(10) ε[L mol⁻¹ cm⁻¹] c[mol/L]`，`μa[m⁻¹]=100 μa[cm⁻¹]`（数学换算）。若给的是透射率且无反射/散射校正，`−ln(T)/l`只是表观衰减，不能直接认为全为铁吸收。

仍缺：同一汝片的两相真实端元、各相体积分数/数密度与三维粒径分布、体相分相铁价态、玻璃密度、玻璃两相实测n(λ)、经校准的绝对反射谱/透射谱。IVCT也需铁邻对与局部结构信息；不应仅按总体Fe²⁺与Fe³⁺浓度线性相加成一个“通用IVCT ε”。

## 8. 本地文件与运行核验

| 文件 | 内容与性质 |
|---|---|
| [iron_Volotinen2008_table3_transcribed.csv](files/iron_Volotinen2008_table3_transcribed.csv) | 14行论文拟合参数，含表中误差；源为Volotinen2008表3 |
| [iron_Volotinen2008_reconstructed_350_1100nm.csv](files/iron_Volotinen2008_reconstructed_350_1100nm.csv) | 751行本轮重建谱；Fe³⁺两种解释未裁定 |
| [iron_reconstruct_volotinen.py](files/iron_reconstruct_volotinen.py) | 重建公式与1000nm检查；仅Python标准库 |
| [zhou2023_compositions_wt.csv](files/zhou2023_compositions_wt.csv)、[shi2020_compositions_wt.csv](files/shi2020_compositions_wt.csv) | 论文XRF/EDS数值转录；空白保留为未报值 |
| [shi2020_surface_redox_and_conditional_split.csv](files/shi2020_surface_redox_and_conditional_split.csv) | XPS表面价态转录与体相条件推算，不能混为化学实测分价态 |
| [钙长石实测表](files/index_anorthite_measured_Medenbach1997.csv)、[再拟合系数](files/index_anorthite_Sellmeier_refit.csv)、[拟合脚本](files/index_fit_anorthite.py) | 原始表数值转录、本文推算分开；脚本需NumPy |
| [Appen牙科论文版](files/index_Appen_Duminis2018.csv)、[Appen专利版](files/index_Appen_EP3013762B1.csv)、[Huggins1940版](files/index_Huggins1940_D_FminusC.csv) | 三份有版本区分的系数/条件转录，不混用 |
| [npm_download_manifest.tsv](files/npm_download_manifest.tsv) | 官方馆藏/IIIF浏览入口及8条待取图像URL；不保证这些动态链接仍有效或属于600万档 |
| [download_sources.py](files/download_sources.py)、[download_attempts.json](files/download_attempts.json) | 原文件重取脚本与本轮18项失败记录；没有把HTML错误页存成PDF/JPG；自动重取不负责验证码和最高档位选择 |

已重新运行两个数值脚本：Fe²⁺1000nm重建30.001；钙长石再拟合D线四位值与原文表7一致。已检查CSV波长350–1100nm共751点、1nm连续、数值有限且非负，以及报告内本地文件链接存在。该核验验证转录后计算和文件组织，**不是独立验证论文的测量精度或汝釉适用性**。原图未取得，无法完成视觉验收与描谱；馆藏最高分辨率图、贾翠图5/6定量仍受阻。
