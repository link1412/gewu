# 任务3：折射率与色散（2026-10-29）

## 可直接用于计算的钙长石数据

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

## Appen：找到可运行的nD加和式，但没有完整汝釉/分相专用色散表

Duminis, Shahid, Karpukhina & Hill (2018), *Predicting refractive index of fluoride containing glasses for aesthetic dental restorations*, Dental Materials 34 e83–e88, [DOI](https://doi.org/10.1016/j.dental.2018.01.024)，[作者机构存档PDF地址](https://qmro.qmul.ac.uk/xmlui/bitstream/handle/123456789/48883/Duminis%20et%20al.%202018.%20Predicting%20refractive%20index.pdf?sequence=1)。检索索引可读 eq.1 / Table1，直接文件请求返回失败。其式为

`nD = Σ(C_i × f_i)/100`，`C_i=100(w_i/M_i)/Σ(w_j/M_j)`。

这里 w 为氧化物质量（可wt%，先换摩尔），M为氧化物摩尔质量，C为**氧化物mol%**；f为**加和因子**，无量纲，不等于纯氧化物晶体折射率。表1：SiO2 1.4585；Al2O3 1.52；P2O5 1.31；Na2O 1.575；ZnO 1.71；K2O 1.575；CaO 1.73；SrO 1.775。人工转录 [CSV](files/index_Appen_Duminis2018.csv)。Na、Si取值与其他版本有差异，故保留版本来源，不拼成“完整Appen原始表”。FeO、Fe2O3、MgO、TiO2的本表系数**没找到**，不能用该8项表无说明地计算完整汝釉。

本研究在约20°C用钠D线Becke line法测量牙科玻璃，作者“within 0.005”是对其**系列专用含氟修正**的准确度，**不是古汝釉或通用Appen模型的误差保证**。来源 [PubMed原文摘要](https://pubmed.ncbi.nlm.nih.gov/29402539/)。其λ连续色散系数**没找到**。

[INTERGLAD Ver.7 官方手册2018，pp.9–10](https://www.interglad.jp/interglad7/doc/interglad7manual6_14e.20180201.pdf)明确列有室温 Appen nD 与Abbe数模型；含B2O3时SiO2需44–64或71–80 mol%；含TiO2时总R2O<15 mol%、SiO2 50–80 mol%；含CdO或PbO时SiO2+Al2O3+B2O3≥50 mol%。来源书Appen *Kimiya Stekla*, Leningrad 1974。手册此次可读，但**17氧化物的完整系数表没找到**；不能据名称就声称色散可算。

### 另一个明确的 Appen 系数版本（不可与上表静默混用）

Queen Mary University of London 发明人的 [EP3013762B1 *Leucite glass ceramics*](https://patents.google.com/patent/EP3013762B1/en)，说明书 Appen factor 表给：Al2O3 1.520；CaO 1.730；Na2O **1.590**；Li2O 1.695；MgO **1.610**；K2O **1.575**（Na2O<1 mol%用 **1.595**）；SiO2 **1.475**（SiO2≤67 mol%），在67–100 mol%时为 `1.5085−0.0005 pSiO2`；TiO2在50–80 mol%SiO2条件下为 `2.480−0.005 pSiO2`（2.230–2.080）。p是**mol%**，说明书最后一句明确需从重量换成摩尔。网页Si公式右端误排为nSiO2，Ti末式误排为α，但文字与范围足以识别；应保留误排说明，不能宣称直接核对过原版Appen书。

该专利提供组成依赖Si/Ti以及Mg因子，较适合作低硼硅酸盐的**估算版本**；但缺FeO/Fe2O3因子、无色散及古汝釉验证误差。**完整两相n(λ)目前仍算不齐**。专利公开不等于图片取得CC许可；PDF未下载。

## Huggins：已定位原始数值表；连续全谱公式仍待核原文

原始系列：
- Huggins 1940 [Density, JOSA30,420–430](https://doi.org/10.1364/JOSA.30.000420)：`V_O=k+bSi+cSi N_Si+Σ c_M N_M`，N为每个氧原子的阳离子数；k依退火历史。
- Huggins1940 [Refractive index, JOSA30,495–504](https://doi.org/10.1364/JOSA.30.000495)：每摩尔氧的折射加和，表2aM用于Gladstone–Dale式；表3a'M用于Newton式，**两组不可混用**。
- Huggins1940 [Dispersion, JOSA30,514–518](https://doi.org/10.1364/JOSA.30.000514)：增加一个元素常数可算可见色散；其优质体系中 nF−nC平均差约(5–8)×10⁻⁵（论文摘要），不是汝釉误差。
- Huggins, Sun & Davis1942 [Dispersion II, JOSA32,635–650](https://doi.org/10.1364/JOSA.32.000635)：加入通用项和Ca/Ba/Pb修正；表1完整数值在出版社检索索引可读。
- Huggins & Sun1943 [Calculation of density and optical constants of a glass from its composition in weight percentage, JACerS26,4–11](https://doi.org/10.1111/j.1151-2916.1943.tb15176.x)：wt%等价表达，非1941（INTERGLAD手册这条年份疑误）。

Fantone1983 [Applied Optics22,432–440](https://doi.org/10.1364/AO.22.000432) 表I、II、V在出版社网页可读，重列Huggins的体积与折射常数。表V包括Ca'、Ba'、Pb''修正行；仅拿主行线性相加会丢掉原模型机制。**此次没有核到完整公式与g/d单位缩放，不把它包装成已验证的连续波长求解器**。原始表主要针对透明硅酸盐玻璃，铁为FeIII，FeII无对应常数；汝釉的混合价态、吸收共振及分相不能只用这一套实部n加和模型概括。

Fluegel：找到的glassproperties公开模型为粘度/密度等；**没有找到带可核系数的Fluegel折射率/色散模型**。不拿Fluegel密度模型冒作n模型。

## 文件获取状态

本次仅落盘人工转录CSV与本说明。没有下载到作者PDF、INTERGLAD PDF、Shannon2002 PDF或Medenbach1997 HTML。已提供实际找到的URL。任何后续下载的文件应另核文件类型/页码/版权。

### 三轴连续曲线的可复现再拟合（本文推算）

另保存 [拟合脚本](files/index_fit_anorthite.py) 与 [系数CSV](files/index_anorthite_Sellmeier_refit.csv)。用表6逐轴对 `1/(n²−1)` 关于 `−1/λ²` 做无权最小二乘；**λ用μm，A单位μm²，B无量纲**，解出 `n(λ)=sqrt(1+1/(B−A/λ²))`。

|主轴|A / μm²|B|最大绝对n残差|采样区间 / nm|
|---|---:|---:|---:|---|
|α|0.00732387370241|0.697466266239|0.000161|435.8–643.8|
|β|0.00694790121851|0.684148087867|0.000268|404.7–643.8|
|γ|0.00719232937106|0.678408944507|0.000190|404.7–643.8|

以上**不是作者发表的逐轴系数**，只用于实测区间内插值；β轴最大拟合残差略大于作者±0.0002测量估计，故不能宣称这次单项拟合达到比该值更高精度。无需用平均A/B覆盖各轴；原始CSV保留所有采样值供重选插值法。未把拟合在350–1100 nm的数学外推作为已知实测色散。

专利版 Appen 因子的机器可读表达式及适用条件已另存 [CSV](files/index_Appen_EP3013762B1.csv)，不补入Fe因子。用这个版本时应单独报告被剔除/缺失氧化物的总wt%和mol%，**不得静默去铁后归一化，再把结果称作完整釉相nD**。

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
