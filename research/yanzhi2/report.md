# 胭脂红（清代金红珐琅）第二轮资料

检索日期：2026-11-02。文中“没找到”均指本轮公开检索与可取得原文的范围，不能理解为证明文献不存在。

**推荐方向：先用有明确组成的含铁铅玻璃谱做灵敏度检验，同时校正基质折射率的量级；目前证据不足以将照片与模型的色相差归因于铁。** 对照谱、文物组分、厚度、铁价态必须分开使用。照片估得的 22–29° 与模型约 7°来自任务背景，本轮没有将其升级为仪器实测色度。

|任务|本轮结果|可直接检查的交付|关键缺口|
|---|---|---|---|
|1. 高铅玻璃中的铁吸收|找到作者吸收系数 α 图；另找到 PbO 25 wt%、Fe₂O₃ 1 wt% 含锰玻璃的完整可见吸光度图|两篇原PDF、原图、两套数字化CSV，见下表|**没找到**匹配 PbO≈38 wt% 的 Fe³⁺、Fe²⁺各自 ε(λ) 完整数表|
|2. 清代金红彩实测颜色|**没找到**附仪器、光源和几何的目标反射谱或 L*a*b*|已核对侯2018原表；列出逐篇检索结果|缺同一点位反射谱和光学层厚；不能用照片/拉曼代替|
|3. 折射率|找到 Appen 早期印刷原表及一件铅含量相近的现代珐琅实测值|原表页图、转录CSV、可运行估算脚本|完全匹配目标成分的实测 n(λ) **没找到**|
|4. 可选|Colomban2025可见发射谱已取得并数字化；清代Au的20–60 nm仅核到转引|完整PDF、Fig.5b原图与CSV、粒径来源链|未取得清代Au原始TEM图；2025发射谱不能作吸收谱|

## 0. 先固定对象、成分与证据性质

侯佳钰、丁银忠、李合、吕成龙：《故宫博物院藏康熙、雍正朝两件珐琅彩瓷无损分析》，《故宫学刊》19（2018），pp.211–220。[故宫原PDF](https://img.dpm.org.cn/Uploads/File/2020/04/15/u5e96e25da139c.pdf)｜[本地PDF](sources/color/hou_2018_kangxi_yongzheng.pdf)｜[雍正原表p.216](sources/color/hou2018_page8.png)｜[成分CSV](sources/color/hou2018_carmine_composition.csv)。

|样品|SiO₂|PbO|K₂O|Na₂O|Fe₂O₃|MnO|Au₂O₃|定位与性质|
|---|---:|---:|---:|---:|---:|---:|---:|---|
|雍正黄地珐琅彩花卉盘残件：胭脂红|51.75|38.13|2.90|2.28|1.14|0.05|0.11|p.216 表1续表，PDF第8页；**XRF无标样半定量，wt%氧化物报告值**|
|康熙黄地珐琅彩缠枝牡丹纹碗残件：胭脂红|51.34|34.28|3.99|1.46|0.18|0.02|0.07|p.215 表1，PDF第7页；同一方法|

雍正其余数字：MgO 0.73、Al₂O₃ 1.80、CaO 1.02、TiO₂ 0.02、CuO 0.08 wt%；As₂O₃ 为 trace；SnO₂、Sb₂O₃、CoO 为“/”。“/”未擅自改成零，完整转录见CSV。

|核查项|原文说明及对模型的约束|
|---|---|
|测量方法|p.211（PDF第3页）：EDAX EAGLE III XXL 能量色散XRF；40 kV、300–400 µA；真空；200 s活时间；300 µm束斑；每样品测3点；无标样软件半定量。[方法页](sources/color/hou2018_page3.png)|
|铁价态|Fe₂O₃是总铁的氧化物报告方式，**不等于实测Fe³⁺占比**。同理，Au₂O₃表头不表示证明存在Au³⁺。这是本轮对方法的解释；论文p.216将红彩归为金红着色。|
|红层厚度|康熙胭脂红层约 **25 µm**，p.212–213 图3及正文。**雍正胭脂红层厚度没找到**；雍正黄、绿、黑层的25–30 µm不能借作其红层厚度。|
|对象适用性|上述组分属于这两件故宫残件；不能直接赋给大都会1971.180.248或上博其他器物。B不在此XRF可测范围内，组分表不能排除未计硼。|

## 1. 铁在含铅硅酸盐玻璃中的可见吸收

### 1.1 已取得的两套原始实验

|文献、原文与本地文件|PbO、铁及其他组分|仪器、厚度、谱量|页码/图号与可用性|
|---|---|---|---|
|Ookawa, Sakurai, Mogi & Yokokawa (1997), *Optical Spectroscopic Study of Lead Silicate Glasses Doped Heavily with Iron Oxide*, **Materials Transactions JIM 38:220–225**。[DOI](https://doi.org/10.2320/matertrans1989.38.220)｜[出版社PDF](https://www.jstage.jst.go.jp/article/matertrans1989/38/3/38_3_220/_pdf)｜[本地PDF](sources/iron/Ookawa_1997_lead_silicate_iron.pdf)|名义基体 **0.5PbO·0.5SiO₂+xFe₃O₄**。x=.002时，本轮批料换算 PbO≈78.54 wt%、总铁折Fe₂O₃≈0.337 wt%；x=.01时≈77.53%、1.664%；A-4（x=.05）≈72.84%、7.82%。这些质量百分数为**本轮推算**，非作者实测Pb/Si组分。|室温Shimadzu UV-365；4000–40000 cm⁻¹；样厚 **0.002–0.2 cm**；不同厚度吸光度差分扣除表面反射。总铁AAS，Fe价态用化学分光法。|p.220实验、p.221表1、**p.222图3/4**。[图3](sources/iron/Ookawa_1997_Fig3.png)｜[图4](sources/iron/Ookawa_1997_Fig4.png)。实测作者α，单位cm⁻¹；纸面可见区蓝端截顶，不能恢复380–780 nm完整谱。|
|Klysubun et al. (2015), *Understanding the blue color in antique mosaic mirrored glass from the Temple of the Emerald Buddha, Thailand*, **X-Ray Spectrometry 44:116–123**。[DOI](https://doi.org/10.1002/xrs.2586)｜[NIST原PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=917140)｜[本地PDF](sources/iron/Klysubun_2015_antique_blue_lead_glass.pdf)|参考玻璃 **R5** 名义批料wt%：PbO **25.00**、SiO₂ **58.50**、Na₂O6.60、CaO5.50、K₂O1.30、Al₂O₃1.50、Fe₂O₃ **1.00**、MnO **0.24**；另ZnO .06、As₂O₃ .08、SnO₂ .10、Sb₂O₃ .04、BaO .11；无Co/Cu。|Agilent Cary300，透射190–900 nm；R系列厚 **0.4 mm = 0.04 cm**；A=log₁₀(1/T)。R5为淡黄色。|公开稿未印页码：**PDF p.4表3及方法，p.5价态，p.7图8**。[配方/方法页](sources/iron/Klysubun_2015_p4.png)｜[图8](sources/iron/Klysubun_2015_Fig8.png)。有380–780 nm实测吸光度，但含Mn，且未明确扣Fresnel反射。|

|值得保留的定量约束|数字、定位|性质及限制|
|---|---|---|
|同一铁总量下的氧化还原差异|Ookawa p.221表1：A-4空气中 **Fe²⁺/Fe总=.07**，B-4 Ar中 **.28**；图4两谱明显不同|实测价态比例；不能只按总铁浓度定谱形|
|混合价态产生的红区带|Ookawa **p.224表3，E带**：中心14200–14700 cm⁻¹（本轮换算约680–704 nm）；拟合峰高A-2 .16、B-2 .50、A-3 .62、B-3 3.2、A-4 16 cm⁻¹。[参数转录CSV](sources/iron/Ookawa_1997_Table3_band_E.csv)|高斯拟合；作者归为Fe²⁺→Fe³⁺间价电荷转移。高铁体系有非线性，不能把该带按7.82→1.14 wt%直接线性缩放。|
|R5价态|Klysubun PDF p.5：**Fe²⁺/Fe³⁺=.25±.08**；由此本轮换算Fe²⁺/Fe总≈20%|XANES标定推定的价态比例；不是独立Fe²⁺/Fe³⁺消光系数|

### 1.2 可复用数值：R5全可见区、A-4部分可见区

以下都是**本轮从实测曲线读图数字化**，不是作者发布的原始数表。R5读图不确定度估约±0.01 A；A-4约±2 cm⁻¹，均非仪器误差。

- [R5 380–780 nm CSV](sources/iron/Klysubun_2015_Fig8_R5_digitized.csv)：附表观自然对数衰减系数 `α_app=ln(10)·A/0.04 cm`。**α_app是本轮计算，含反射、基玻璃、Mn等贡献，不是纯铁实测μₐ。**
- [A-4 520–780 nm CSV](sources/iron/Ookawa_1997_Fig4_A4_digitized.csv)：保留作者“α”命名。作者以吸光度厚度差定义α，但原文未明确对数底，**不要未经核查直接放进 exp(−αd)**。
- 图3低铁曲线的红端接近坐标轴、分线不稳，只保留原图，没有强行补数；缺失波段没有外推。

|λ / nm|R5 A（实测图采点）|R5 α_app / cm⁻¹（推算）|
|---:|---:|---:|
|380|0.386|22.22|
|400|0.301|17.33|
|420|0.265|15.25|
|440|0.244|14.05|
|460|0.227|13.07|
|480|0.213|12.26|
|500|0.202|11.63|
|520|0.194|11.17|
|540|0.187|10.76|
|560|0.179|10.30|
|580|0.173|9.96|
|600|0.170|9.79|
|620|0.166|9.56|
|640|0.161|9.27|
|660|0.158|9.10|
|680|0.156|8.98|
|700|0.154|8.86|
|720|0.152|8.75|
|740|0.149|8.58|
|760|0.147|8.46|
|780|0.145|8.35|

**本项仍没找到：**接近故宫基体、可将 Fe³⁺与 Fe²⁺分开的摩尔吸光系数表；以及同时有成分、厚度、完整可见透/反射谱的清代浇黄或素三彩黄数据。两套现有谱都只能作为组成明确的对照，不能叫作“清代胭脂红中的铁吸收谱”。[详细查证记录](sources/iron/findings.md)。

### 1.3 重要但未取得全文的线索

|线索|已核实内容|未取得内容/不纳入定量的原因|
|---|---|---|
|Morsi, Ibrahim & Morsi (2017), *Characterization of sodium lead silicate glasses containing low and high levels of Fe₂O₃ and effect of its replacement for Na₂O*, **J. Mater. Sci.: Mater. Electron.28:9566–9574**，[DOI](https://doi.org/10.1007/s10854-017-6704-1)|配方mol%为(25−x)Na₂O−xFe₂O₃−25PbO−50SiO₂，x=0,.25,.5,1,3,5,7,10,15,16,20；有UV/可见/NIR实验|全文下载返回406；谱图、厚度与可用系数未核实。25 mol% PbO不能误写25 wt%。|
|Hou et al. (2022), *The origins of imperial yellow glazed porcelain in the Ming Dynasty…*, **Archaeometry64:59–70**，[DOI](https://doi.org/10.1111/arcm.12692)|明代黄釉；公开全文索引可见色度/反射相关图4、Pb/Fe组成及厚度研究|PDF返回403；未获得可核验数表，且非清代，未充作本任务已交付数据。|

## 2. 清代胭脂红/胭脂水/金红彩的反射谱或 L*a*b*

**没找到符合要求的数值。光源、仪器、测量几何也因此不能补写。**“研究了呈色”不等于做了反射测色。下表分别标明“原文中没有”与“未取得全文，无法判断”。

|文献/对象|本轮读到的内容与定位|颜色数据状态|
|---|---|---|
|侯佳钰等2018，见第0节|p.211 XRF方法，p.215–216成分表；显微断面|已核全文：没有目标反射谱或L*a*b*|
|贾翠等2018，《故宫南大库出土黑地珐琅彩瓷的科学分析和工艺研究》，**《故宫博物院院刊》(1):130–137**。[原PDF](https://www.dpm.org.cn/Uploads/File/2018/06/01/u5b110ee358252.pdf)｜[本地PDF](sources/color/jia_2018_black_ground_enamel.pdf)|p.133表一、p.136红彩分析；XRF、LIBS、Raman，红彩归为胶体金|已核全文：没有目标反射谱或L*a*b*；LIBS和拉曼峰不是可积分的颜色反射谱|
|熊樱菲、何文权2005，《清代红釉（彩）瓷的呈色元素分析》，**《文物保护与考古科学》17(4):23–27**|书目信息由[原文引用文献5](https://yznkxjs.xml-journal.net/cn/article/pdf/preview/10.7538/yzk.2011.45.11.1399.pdf)核实|未取得全文；未找到色值，不能断言全文没有|
|赵灵委等2018，《几件明代斗彩和清代粉彩瓷片的科学分析》，**《文物保护与考古科学》30(5):98–109**，[作者机构记录](https://jczx.siom.ac.cn/zxjj/rcdw/202505/t20250529_548378.html)|目标材料范围内的中文论文|未取得全文；未找到反射谱/色值和测量元数据|
|Mills & Kerr 1999，*A study of ruby-pink enamels on Chinese porcelain…*，ISAC’99 **pp.258–265**（部分书目至266）|[大都会2023论文参考文献pp.105–106](https://resources.metmuseum.org/resources/metpublications/pdf/BellemareCaroStamm_Metropolitan_Museum_Journal_v_58_2023.pdf)核实书目；另有[同题会议摘要DOI](https://doi.org/10.1179/sic.2000.45.s2.021)|1999原文未取得；后文称其为48件器物的XRF研究，不能将此转述成测色实测|
|Ping et al.2026，*Arsenic, gold and smalt…Qianlong-period famille-rose architectural tiles from Yuanmingyuan*，**JAS189:106522**，[DOI](https://doi.org/10.1016/j.jas.2026.106522)｜[北大记录](https://ir.pku.edu.cn/handle/20.500.11897/789629)|乾隆期圆明园粉彩建筑砖；公开预览归粉色于胶体金|未取得全文；预览未提供目标反射谱/色值或TEM粒径数字|
|曹春娥等2011，《无铅、砷金红粉彩颜料的呈色机理》，**《硅酸盐学报》39(11):1734–1739**，[DOI](https://doi.org/10.14062/j.issn.0454-5648.2011.11.022)｜[官方摘要](https://jccsoc.cbpt.cnki.net/portal/journal/portal/client/paper/9293f260e984b5d4e83ebd667bac01f7)|摘要提到分光测色、约520 nm吸收、TEM金粒20–30 nm|**现代无铅无砷样品，非清代实物**；全文/图号/色度条件未核实，不填补本项|
|故宫、上博典藏照片|[故宫胭脂红釉盘](https://www.dpm.org.cn/collection/ceramic/227018.html)｜[上博介绍](https://www.shanghaimuseum.net/mu/frontend/pg/m/article/id/RI00004033)|没有同图配套校准色度与测量几何；照片像素估色不算文物实测|

检索使用“胭脂红/胭脂水/金红彩/粉彩瓷＋反射率/反射光谱/色度/Lab/测色/光源”，及“Qing/Yongzheng/famille rose/ruby-pink＋reflectance/colorimetry/spectrophotometer”；排除了同名食品色素、胭脂虫红和无测色元数据的数字色卡。更多说明见[查证记录](sources/color/findings.md)。

## 3. 铅钾硅酸盐玻璃的折射率

### 3.1 可取得的实测对照

|来源|成分与数字|方法及定位|适用边界|
|---|---|---|---|
|Palomar, Pradell & Mosa (2025), **Materials18:1137**，[DOI](https://doi.org/10.3390/ma18051137)｜[本地PDF](sources/index/materials_2025_18_1137.pdf)｜[表1原页](sources/index/materials_2025_p8.png)|现代历史配方重建珐琅 **R8B1S：n=1.604±0.006**。表列wt%：PbO38.2、SiO₂34.3、K₂O17.9、Na₂O3.7、Al₂O₃ .2。|**p.8表1；p.5 §2.3**。J.A.Woollam M-2000U/WVASE32可变角光谱椭偏；65°/70°/75°；模型反演n、k。|属于实验光学数据拟合；Pb接近而Si/K相差很大。**表中单一n的对应波长没找到，不能改称n_D**。方法的波段文字也有不一致，见详细记录。|
|与目标完整组成直接相符的实测 n_D 或 n(λ)|**没找到**|—|不能用上面1.604替代文物实测值|

### 3.2 Appen 原印刷表：按 mol% 加和

取得的是 A.A.Appen 等参与编著的 **1963年《Справочник по производству стекла》（玻璃生产手册）第1卷，p.206式(6)、p.207表72**，不是1949首发表。[全书在线扫描](https://djvu.online/file/0G175FonTgj0Y)｜[式(6)原页](sources/index/appen1963_p206.png)｜[表72及组成公式原页](sources/index/appen1963_p207.png)｜[转录CSV](sources/index/appen1963_table72_transcribed.csv)。原页已逐项查看。

|氧化物|表72部分折射率因子 n̄ᵢ|部分平均色散 D̄ᵢ=n_F−n_C|注释|
|---|---:|---:|---|
|SiO₂|1.4585–1.475|0.00675|随组成变化，见下式|
|PbO|2.150–2.350|0.05280–0.07440|随组成变化，见下式|
|K₂O|1.575|0.01300|括号值1.595、.01320仅二元碱硅酸盐用|
|Na₂O|1.590|0.01420|括号值1.575、.01400仅二元碱硅酸盐用；原页另有四星脚注，保留在扫描中|

这些是**经验加和因子，不是纯氧化物的独立折射率**。计算式为 `n_D=Σ(mᵢ n̄ᵢ)/Σmᵢ`，mᵢ用氧化物 **mol%**，归一化分母为100；不可把wt%直接乘这些因子。

|组成依赖|原表公式与约束|
|---|---|
|SiO₂|mol%≤67取1.475；>67取 `n̄_SiO₂=1.475−0.0005(m_SiO₂−67)`。|
|PbO|`n̄_PbO=2.350−0.0067(S−50)`；`D̄_PbO×10⁵=7440−72(S−50)`。原页把S写成氧化物求和符号，没有紧邻枚举成员；后期资料将其解释为SiO₂+B₂O₃+Al₂O₃的mol%和。下面只保留SiO₂作网络形成物，因此明确取S=m_SiO₂。未对漏项做隐含补全。|
|波长与范围|[INTERGLAD官方手册](https://www.interglad.jp/interglad7/doc/interglad7manual6_14e.20180201.pdf) **p.9 §(10)①**：Appen方法为室温D线；铅系要求SiO₂+Al₂O₃+B₂O₃≥50 mol%。这是后期使用说明，不代替系数原表。[本地PDF](sources/index/interglad7manual_appendix_2018.pdf)。|

### 3.3 对目标组成的透明近似：n_D≈1.58，不是实测

只取侯2018的四主项：PbO38.13、SiO₂51.75、K₂O2.90、Na₂O2.28 wt%，合计 **95.06 wt%**；**漏去其余4.94 wt%后**，将各项质量先除摩尔质量，再以所保留摩尔数归一化。不是完整文物成分预测。

|保留氧化物|归一化mol%|本次组成依赖因子|
|---|---:|---:|
|PbO|15.53464|2.160252|
|SiO₂|78.32061|1.469340|
|K₂O|2.79958|1.575|
|Na₂O|3.34517|1.590|

**本轮推算 n_D=1.5837，作为量级建议只写约1.58。** 四项截断、XRF半定量、漏测组分和经验公式都会限制精度；不能将其当380–780 nm无色散的精确n。原表另有平均色散因子，但单个n_D不能唯一确定连续n(λ)。[计算脚本](sources/index/calculate_index.py)｜[计算明细CSV](sources/index/hou2018_four_oxide_approximation.csv)；运行：`python3 sources/index/calculate_index.py`。

**没找到：**完全匹配目标的实测n(λ)、Appen1949首发表全文、1974书中对应原表。1963原书表已取得，不将其冒称首发表。[第3项详细记录](sources/index/findings.md)。

## 4. 可选：清代Au粒径与 Colomban2025 可见光谱

Colomban, Tang & Simsek-Franci (2025), *Non-Invasive Study of Gold Nanoparticles in Famille rose and Ruby-Back Qing Porcelain by Luminescence, Low-Wavenumber Raman Scattering and pXRF*, **Applied Sciences15:12265**。[DOI](https://doi.org/10.3390/app152212265)｜[完整本地PDF](sources/colomban2025/Colomban_2025_ApplSci_15_12265.pdf)。

|资料|数字及原文位置|性质与边界|
|---|---|---|
|可见发射曲线|**p.9 Fig.5b**，图内标峰：ruby **594.7 nm**、pink **607.4 nm**；glaze **598.7、623.2 nm**。[原图](sources/colomban2025/fig5b_visible_luminescence.png)｜[整页](sources/colomban2025/page_09.png)|激光激发的发射强度，无绝对辐射单位；**不是反射谱、吸收谱或白光色度**。|
|可复用曲线表|[Fig.5b数字化CSV](sources/colomban2025/fig5b_digitized_emission.csv)：520–645 nm，5 nm步长；另附[脚本](sources/colomban2025/digitize_fig5b.py)|本轮图像采点，非作者原始数据。重合分不开的pink点留空；读图约±0.5 nm、±300图示强度单位，不包含实验误差。|
|峰位群体差异|**p.11 Fig.6b及正文**：常见发射峰约545 nm；部分点约564 nm。[原页](sources/colomban2025/page_11.png)|不能以Fig.5b的单一曲线峰代表所有清代金红。|
|测量条件|p.4–5 §2.3：Labram HR800；514.5、457.9 nm激光；50×长工作距物镜、NA .45；约5×5 µm²分析点|不是D65等标准光源下的反射测色。Fig.5另写457.8 nm，保留原文差异。|
|该文是否给清代Au TEM粒径|**没有**。p.10明确说不能直接定粒径；p.11提及 **10–50 nm** 的TEM结果来自**铜红釉Cu颗粒**，对Au只是类比|不可将10–50 nm写成清代金红Au实测。|
|清代Au 20–60 nm的文献链|Barber & Freestone (1990), **Archaeometry32:33–45，p.43**明确转引Kingery & Vandiver1986：18世纪中国famille rose透明粉红珐琅Au颗粒 **20–60 nm**。[DOI](https://doi.org/10.1111/j.1475-4754.1990.tb01079.x)｜[作者上传全文页面](https://www.researchgate.net/publication/229720080_An_investigation_of_the_origin_of_the_colour_of_the_Lycurgus_Cup_by_analytical_TEM)|**核到转引，不是核到原始TEM图**。原章为*Ceramics and Civilization II* pp.363–381/382，原TEM图号、仪器与统计数没找到；PDF下载403。[来源链记录](sources/particles/README.md)。|

**原文内部标注问题：**Fig.5b图注写glaze×10、ruby(defects)、green，而图内写glaze、pink、ruby。本次采数照图内名称，未自行重新认定采样点或强度倍数；不以不同曲线强度比作定量结论。详见[谱图说明](sources/colomban2025/README.md)。

## 5. 这些资料能怎样约束下一轮模型

|推荐动作|证据依据|可证伪/停止条件|
|---|---|---|
|用R5谱检查“额外短波吸收”能产生多大方向性变化|组成与1 wt%铁接近，且380–780 nm完整；但Mn和反射混入|标为替代基体敏感性试算；不把拟合成功解释成铁被证实。若依赖很大的浓度缩放或任意基线，就不能据此定量归因。|
|保留Fe价态与红区带，不只加单调黄色滤镜|Ookawa同铁量不同价态谱有差别；拟合存在680–704 nm带|高铁谱不得直接线性缩放成文物1.14 wt%谱；缺少相近基质、价态数据时停止宣称独立Fe贡献已确定。|
|将基质n_D约1.58作为核对量级|Appen原表可复算；近铅量对照实测n约1.60，但成分不同|正式定n(λ)前仍需完整组成或相近配方实测；不以单个近似n_D替代全色散。|
|用目标实物的反射谱验证色相，而非仅馆藏照片|第2项关键缺口；对象成分与厚度亦不同|未取得校准反射谱前，**本轮不能证明铁足以解释7°→22–29°**；下一步测量应记录白板、光源/观察者、几何、SCI/SCE与点位。|

## 6. 本地交付索引

|路径|内容|
|---|---|
|[sources/iron/](sources/iron/)|Ookawa1997、Klysubun2015原PDF，相关页/图，吸收与吸光度CSV、拟合表、查证记录|
|[sources/color/](sources/color/)|侯2018、贾2018原PDF，侯方法/组分页图，康熙/雍正胭脂红组分CSV、颜色数据缺项记录|
|[sources/index/](sources/index/)|Appen1963原页扫描（非拼装的完整原书PDF）、原表CSV；Materials2025与官方手册PDF；估算脚本/CSV|
|[sources/colomban2025/](sources/colomban2025/)|2025完整原PDF、Fig.5b/6原图、p.8–11页图、发射谱CSV与复现脚本|
|[sources/particles/README.md](sources/particles/README.md)|清代Au粒径的转引链与未取得原始TEM图的说明|
|[sources/manifest.csv](sources/manifest.csv)|交付文件的字节数和SHA-256校验清单|

原文可取得者已保存；未取得者仅给书目、链接与缺失状态，没有生成替代PDF。CSV明确区分原表转录、实测图数字化和本轮推算。
