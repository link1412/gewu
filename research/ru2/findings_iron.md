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
