# 第1项：高铅硅酸盐中的铁吸收

## 可以直接交付的结论

**找到了高铅玻璃的实测吸收系数图，也找到了较接近目标铁浓度、PbO 25 wt% 的含铁铅玻璃完整可见吸光度图；没有找到同时匹配 PbO≈38 wt%、Fe₂O₃≈1.14 wt%、独立 Fe³⁺/Fe²⁺、380–780 nm 全谱的消光系数数值表。** 不应把下列任一谱作为故宫胭脂红的已知铁本征谱。

| 来源 | 精确位置 | 数字与条件 | 实测/推算 | 对建模的意义和局限 |
|---|---|---|---|---|
| M. Ookawa, T. Sakurai, S. Mogi, T. Yokokawa, *Optical Spectroscopic Study of Lead Silicate Glasses Doped Heavily with Iron Oxide*, Materials Transactions JIM **38** (1997) 220–225. [DOI](https://doi.org/10.2320/matertrans1989.38.220)，[出版社原PDF](https://www.jstage.jst.go.jp/article/matertrans1989/38/3/38_3_220/_pdf) | p220 Experimental；p221 Table1；p222 Fig3、Fig4；p223 Fig6、Fig7；p224 Table3 | 基玻璃0.5PbO·0.5SiO₂+xFe₃O₄。x=.002、.01、.05等；室温 Shimadzu UV-365，4000–40000 cm⁻¹，切磨厚度0.002–0.2 cm（20–2000 μm）；不同厚度差分扣除表面反射；铁总量AAS、铁价态化学分光法。Fig3、4纵轴为作者α/cm⁻¹ | 原谱实测；Fig6–7拆峰与Table2–3为拟合 | 直接满足“高铅玻璃+α谱”。但名义PbO近73–79 wt%，远高于目标38%。Fig3/4的纸面图只覆盖约435/455 nm以长波一侧，蓝端α超出纵轴。未给数值全谱。 |
| 同上 A-4 与 B-4 | p221 Table1；p222 Fig4 | x=.05；A-4空气，Fe²⁺/Fe总=.07；B-4 Ar，Fe²⁺/Fe总=.28。相同铁总量而谱差很大；A-4采点见CSV | α图实测，采点为本次图像数字化 | 仅靠“总铁以Fe₂O₃表示1.14%”不能确定谱形；氧化还原比例重要。高铁时存在非线性混合价吸收，不能简单按浓度缩放。 |
| 同上 E 带 | p224 Table3、§IV.2；p225 Fig9、结论 | 拟合中心14200–14700 cm⁻¹，即约680–704 nm；A-2峰高.16、B-2 .50、A-3 .62、B-3 3.2、A-4 16、C-3 33 cm⁻¹。FWHM4250–5700 cm⁻¹ | 高斯拟合实测谱；Fe²⁺→Fe³⁺间价电荷转移是作者的归属/解释 | 不是“Fe³⁺只吸蓝光”的简单情况；红区额外吸收可能使红色更暗、更紫，需和蓝端尾一起算，不能只加单调黄色滤镜。 |
| W. Klysubun et al., *Understanding the blue color in antique mosaic mirrored glass from the Temple of the Emerald Buddha, Thailand*, X-Ray Spectrometry (2015), DOI [10.1002/xrs.2586](https://doi.org/10.1002/xrs.2586)，[NIST公开原PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=917140) | **公开PDF无印刷页码，以下均PDF页码**：p4 Table3和Optical spectroscopy；p5 Fe XANES；p6 Optical absorbance；p7 Fig8 | R5批料wt%：SiO₂58.50、PbO25.00、Na₂O6.60、CaO5.50、K₂O1.30、Al₂O₃1.50、Fe₂O₃1.00、MnO.24、ZnO.06、As₂O₃.08、SnO₂.10、Sb₂O₃.04、BaO.11。R5为light yellow；厚.4 mm；Agilent Cary300透射，190–900 nm，A=log₁₀(1/T)。 | 配方为批料名义值；谱实测；本次按Fig8采点 | 铁浓度接近1.14%，铅25%处于目标38%附近但Ca/Na较高。R5含Mn及还原剂，不能等同纯铁谱；作者未明确做Fresnel反射扣除。 |
| 同上铁价态、吸收特征 | p5 Fe XANES；p6–7正文、Fig8 | R5 Fe²⁺/Fe³⁺=.25±.08；换算Fe²⁺/Fe总≈.20（推算）。约380 nm弱肩，435/555 nm弱带未观测到。原古玻璃B1铁主要Fe³⁺，PbO27.6±1.2 wt%、总铁按FeO .7±.1 wt%（p3 Table1），但B1有Co，不能用作纯铁谱。 | XANES边位移经价态线性标定得到红氧比；380nm肩为光谱观察 | 含铁铅玻璃增加紫光吸收、表现淡黄色的实验支持；本次未证明该效应足以把金红色相从7°推到22–29°。 |

## 本次图谱数字化：数字可复用，但不能把换算伪装为测量

### R5：380–780 nm，含铁+锰的铅玻璃

- 文件：[Klysubun_2015_Fig8_R5_digitized.csv](Klysubun_2015_Fig8_R5_digitized.csv)，原图：[Fig8裁图](Klysubun_2015_Fig8.png)。
- 图像坐标校准：裁图x=98→300 nm，x=971→850 nm；y=43→A1.0，y=693→A0。本次每20 nm选取R5实线中心，估读不确定度约 **±0.01 A**，不是论文给出的仪器误差。
- 附列α_app=ln(10)A/(0.04 cm)，是**由测得透过率吸光度换算的表观自然对数衰减系数**，包含反射/基玻璃/锰等贡献，**不是实测纯铁吸收系数**。在无色基体R2、相同厚度与反射条件下，A_R5−A_R2的差谱会更适合拟合着色增量，但仍不能分离Mn。

| λ/nm | A_R5（实测图数字化） | α_app/cm⁻¹（本次计算） |
|---:|---:|---:|
| 380 | .386 | 22.22 |
| 400 | .301 | 17.33 |
| 420 | .265 | 15.25 |
| 440 | .244 | 14.05 |
| 460 | .227 | 13.07 |
| 480 | .213 | 12.26 |
| 500 | .202 | 11.63 |
| 520 | .194 | 11.17 |
| 540 | .187 | 10.76 |
| 560 | .179 | 10.30 |
| 580 | .173 | 9.96 |
| 600 | .170 | 9.79 |
| 620 | .166 | 9.56 |
| 640 | .161 | 9.27 |
| 660 | .158 | 9.10 |
| 680 | .156 | 8.98 |
| 700 | .154 | 8.87 |
| 720 | .152 | 8.75 |
| 740 | .149 | 8.58 |
| 760 | .147 | 8.46 |
| 780 | .145 | 8.35 |

### Ookawa A-4：已有反射修正的作者α谱，520–780 nm

- 文件：[Ookawa_1997_Fig4_A4_digitized.csv](Ookawa_1997_Fig4_A4_digitized.csv)，原图：[Fig4裁图](Ookawa_1997_Fig4.png)；p222 Fig4最下方A-4曲线。
- 图像坐标：x253→20000 cm⁻¹，x741→10000 cm⁻¹；y710→α0，y56→α200；横轴是波数，先按ν=10⁷/λ转换再读图。估读不确定度约 **±2 cm⁻¹**，不是仪器误差。520、540、560、580、600、620、640、660、680、700、720、740、760、780 nm分别约 **121.9、83.6、60.7、46.6、37.9、32.9、29.2、26.9、25.2、23.5、22.0、21.1、19.9、19.1 cm⁻¹**。
- A-4名义配方0.5PbO·0.5SiO₂+.05Fe₃O₄，按批料分子量折算 **PbO≈72.84 wt%、总铁折Fe₂O₃≈7.82 wt%**。这些是本次名义批料换算；论文没有逐项实测Pb/Si的质量分数。最低铁x=.002时换算PbO≈78.54 wt%、总铁折Fe₂O₃≈.337 wt%；x=.01时约77.53 wt%、1.664 wt%。
- **重要单位限制**：p221–222以α=(A₁−A₂)/(l₂−l₁)定义，A称absorbance，未明说对数底；保留“作者α/cm⁻¹”，不得未经核查视为自然指数中的μₐ。论文Fig5虽然对作者α取ln，仍不能据此判定α最初的对数约定。
- Fig3 x=.002与.01的红段接近坐标轴，分线不稳，因此本次保留清晰图，不硬做低浓度全谱数字化。380–500 nm未恢复，不外推。

## 进一步文献线索与没找到的项目

| 项目 | 结果/限制 |
|---|---|
| Morsi, Ibrahim & Morsi 2017，*Characterization of sodium lead silicate glasses containing low and high levels of Fe₂O₃ and effect of its replacement for Na₂O*, J. Mater. Sci.: Mater. Electron.28:9566–9574，[DOI](https://doi.org/10.1007/s10854-017-6704-1) | 摘要可核实配方(mol%)(25−x)Na₂O−xFe₂O₃−25PbO−50SiO₂，x=0,.25,.5,1,3,5,7,10,15,16,20；存在UV/可见/NIR谱。未取得可核查全文，出版社PDF返回406，因此不提供其厚度、图号或系数数字，也不把它算作已交付数据。 |
| Khalil et al.2010 Silicon2:49–60，[DOI](https://doi.org/10.1007/s12633-009-9029-8) | 摘要给PbO75%、SiO₂25%、约.1%过渡金属掺杂和UV-Vis图；未取得全文，且照射研究需区分未照射样，不作定量依据。 |
| 低温铅黄釉：侯佳钰等2022 *The origins of imperial yellow glazed porcelain in the Ming Dynasty…*, Archaeometry64:59–70，[DOI](https://doi.org/10.1111/arcm.12692) | 是明代样品，非清代。能检索到Fig4色度/反射相关数据、Pb与Fe成分、厚度观察，Wiley PDF下载403；没有核实到可直接代入模型的“清代浇黄/素三彩黄、成分+厚度+完整透反射谱”的一整套数据。此处不凭摘要给清代数据。 |
| 与目标≈38 wt% PbO玻璃匹配的Fe³⁺、Fe²⁺各自摩尔消光系数 ε(λ)，380–780 nm全数表 | **没找到。** 普通钠钙硅玻璃的Glebov/Boulos1998等虽然有分离谱，但基体不是高铅；未作为高铅系数交付。 |

## 本地原文和数据清单

- `Ookawa_1997_lead_silicate_iron.pdf`：出版社6页原文；`Ookawa_1997_p1.png`至`p6.png`逐页渲染；`Ookawa_1997_Fig3.png`、`Ookawa_1997_Fig4.png`裁图；`Ookawa_1997_Fig4_A4_digitized.csv`数字化；`Ookawa_1997_Table3_band_E.csv`拟合表转录；`.txt`为提取文本（扫描PDF几乎无文字）。
- `Klysubun_2015_antique_blue_lead_glass.pdf`：NIST公开8页原文；`Klysubun_2015_p4.png`、`Klysubun_2015_p7.png`；`Klysubun_2015_Fig8.png`裁图；`Klysubun_2015_Fig8_R5_digitized.csv`数字化与表观α换算；同名`.txt`提取文本。


