# 珍珠层／薄螺钿的光学与渲染调研笔记

供主报告整合；截至 2026-11-02。这里的现代贝壳、珍珠和化石样品都不是目标古盘的取样结果，不能用来鉴定古盘贝种。标签：**实测**＝论文实际显微／光谱测量；**文献模型**＝论文采用或反演的参数；**推断**＝为本项目提出的工程解释。下载与图像出处见 `papers/optics_sources.json`、`img/optics_manifest.json`。

## 1. 可以直接引用的结构数值

| 样品与出处 | 数值与测量性质 | 位置、适用边界 |
|---|---|---|
| 新西兰虹鲍 **Haliotis iris**，Song, Soh & Bai (2003) | **实测：**文石层 **450–550 nm**；有机基质层 **21–31 nm**。样品去除角质／棱柱层，清洗、风干，SEM/TEM观察。 | §2 Experimental method；§3.1，Fig.1a,b。来源原文 [DOI](https://doi.org/10.1016/S0142-9612(03)00215-1)；出版社有完整相关段落，全文PDF未获取。[出版社](https://www.sciencedirect.com/science/article/pii/S0142961203002151) |
| 红鲍 **H. rufescens**，Salman et al. (2021) | **实测：**一处断面文石层厚度近似高斯分布，均值约 **420 nm**、标准差约 **50 nm**。**文献概述：**平面晶板直径约 **5–10 µm**，并非裁切后嵌片的尺寸。 | 下载预印本PDF pp.20–21 / SI §4 Fig.S4；正文p.2的5–10µm为转引范围。[论文](https://doi.org/10.1073/pnas.2023623118)；[下载预印本，包含SI](papers/hit_2021_preprint.pdf) |
| 杂色鲍（期刊中文摘要写明），唐利妹、张刚生 (2015) | **实测：**边缘生长端文石层 **499±35 nm**；成熟中心区 **371±36 nm**；SEM＋光纤反射谱。边缘综合色为蓝＋黄，中心为红＋蓝。 | 只获取到原刊摘要；不可补写其未核对的峰位、入射角或制样厚度。[原刊摘要](https://jogg.cug.edu.cn/cn/article/id/5515d970-5f17-4f0c-b811-8e487545ebc6) |
| 虹鲍 **H. iris**，Hizukuri et al. (2025) | **实测：**蓝区文石 **245±38 nm**；绿区 **293±27 nm**；FIB-TEM间层 **11±3 nm**，EDS显示其中存在有机膜。 | Fig.5d,e（各100次SEM板厚测量）；Fig.6a,d及Experimental。与2003样品的21–31nm不同，应保留样品差异。[论文PDF](papers/nacre_nanogaps_2025.pdf)；[DOI](https://doi.org/10.1038/s41598-025-21872-z) |
| 鹦鹉螺 **Nautilus pompilius**，同上 | **实测：**文石板厚 **276±70 nm**。 | Fig.5g，菲律宾样品；仅适合作同类珍珠层比较。[DOI](https://doi.org/10.1038/s41598-025-21872-z) |
| 一颗近无色大溪地珍珠，Fan et al. (2021) | **实测：**珍珠层总厚约 **0.5 mm**，SEM周期约 **330 nm**；**反演：**扣去**假设**的25nm有机层，得到文石约 **305 nm**，与颜色图反演300–325nm一致。 | Fig.4、Results；本论文明确说SEM不能分辨有机层实际厚度，25nm不是该样品测量结果。[论文](https://doi.org/10.1038/s41598-021-99327-4)；[PDF](papers/nacre_structural_color_2021.pdf) |

**层数口径要写清。** Salman 的SI用超过3300层的实测断面模型测试探测深度；正式论文估计H. rufescens的光学取样深度约350层、H. iris约150层。这是光谱拟合的有效深度，不是所有贝片的固定层数。另其公开代码 `layers=201` 逐项交替文石／有机，实际为101文石＋100有机单层；不能把“200 layers”擅自写成200对周期。[论文Methods与SI§3](https://doi.org/10.1073/pnas.2023623118)；[作者代码](https://github.com/katsgroup/PNAS_Nacre/blob/main/HTC_spectral_fit_ppol_example_PNAS.m)

## 2. 折射率、角度与实测光谱

- **文献参数，非古盘实测：**Salman 引用文石在589nm的三主折射率 **1.681、1.686、1.530**，模拟取各向同性 **1.63**、有机层 **1.43**、有机厚度 **25nm**；忽略色散、吸收。其文石层搜索区间150–600nm、无序度σ=5–70nm都是拟合网格，不应当作实测分布。[Methods](https://doi.org/10.1073/pnas.2023623118)
- **实测测量几何：**Salman 的HIT采400–1000nm、204波段；H. rufescens现场点使用 **14° p偏振、30° p/s偏振**，相机接收角约±9°。SI Fig.S1有两种鲍壳由近正入射转向掠射时红黄转绿蓝紫的照片；正文/代码给出测量谱与TMM拟合。其拟合把谱峰归一到1，**不能把归一化谱当绝对反射率BRDF**。[Methods；SI§1](https://doi.org/10.1073/pnas.2023623118)；[角度照片裁图](img/optics_HIT_2021_S1_angle_photos.png)
- **独立角分辨实测：**Finnemore et al. (2012)对天然 **Haliotis tuberculata** 与人工7双层材料作 **15–75°**、3mm²光斑的镜向反射测量。Fig.4a,b直接给“波长×镜向角”热图，第二、第三级反射带随角向短波移动；人工薄膜以±15nm无序模拟更接近实测。人工样品是CaCO₃/PVP（含方解石），不可称天然文石的精确参数验证。[论文](https://doi.org/10.1038/ncomms1970)，Fig.4及Methods；[谱图](img/optics_Finnemore_2012_F4_angle_spectra.png)；[正式PDF](papers/artificial_nacre_2012_published.pdf)
- **具体实测峰位：**Ozaki et al. (2021)的三颗Akoya珍珠橙／粉绿／绿样本，其第二级**实测**反射带中心约 **560、620、700nm**。用**假设** `n文石=1.68, n有机=1.5, d有机=10nm` 反演为 **324、360、408nm** 文石层；这不是SEM直接读数。其Fig.3/4中的0°、20°、40°、60°曲线是**计算角谱**，不要误称角分辨实测。[论文pp.3–5 Fig.2、3](https://doi.org/10.1038/s41598-021-94737-w)；[实测谱图](img/optics_Ozaki_2021_F2_measured_spectra.png)

**简单理论作检查，不作唯一着色器。** 对平行双层、给定干涉级次m，近似峰位为 `m λ = 2[n_a d_a cosθ_a + n_o d_o cosθ_o]`，内角由Snell定律求；增大入射角会缩短同一干涉级次峰波长。多个级次同时落在可见区时，综合色并不遵循单一“厚→红、薄→蓝”的色相轴。[Fan2021 Eq.1](https://doi.org/10.1038/s41598-021-99327-4)

作者仓库示例实测数据已保存为 [MAT](sources/optics_code/test_reflectances_iq.mat) 和无改值转换的 [CSV](sources/optics_code/test_reflectances_iq.csv)：204×2，波长397.32–1003.58nm；脚本称它为Specim IQ示例反射谱。**仓库没有为此示例标明贝种／位置／入射角／校准口径，不能把它当特定古器物或具名样本的绝对反射谱。** [数据原件](https://github.com/katsgroup/PNAS_Nacre/blob/main/test_reflectances_iq.mat)；[读取脚本](https://github.com/katsgroup/PNAS_Nacre/blob/main/HTC_spectral_fit_ppol_example_PNAS.m)

## 3. “磨薄以后颜色怎么变”应分成三个问题

1. **总片厚减小，保留的文石单层厚度未变：推断。** 减少的是重复周期数N，未必改变主要Bragg峰位；会改变反射强度、谱带宽、透射量与衬底贡献。把工艺嵌片厚0.05mm直接作为“干涉薄膜厚50,000nm”输入单层虹彩节点，在物理含义上不成立。依据为TMM对逐层厚度及边界条件的定义，而非针对古盘打磨的实验。[Byrnes2016](https://arxiv.org/abs/1603.02720)；[HIT的层数测试](https://doi.org/10.1073/pnas.2023623118)
2. **磨到不同生长深度，露出的周期本来不同：文献实测与推断分开。** Hizukuri2025正文p.6记载Ammolite磨后由红变绿（SI Fig.S13），解释为随深度层周期不均匀。**这是化石菊石，不是软螺钿减薄实验。** 对现代贝壳的类比只可写为推断；磨薄不会把所有埋藏晶板机械地均匀压薄。[DOI](https://doi.org/10.1038/s41598-025-21872-z)
3. **磨光改变表面阶梯／划痕，可能改变衍射：实测的特殊样本。** Liu, Shigley & Hurwit1999报告法属波利尼西亚 **Pinctada margaritifera**，抛光前虹彩很弱、抛光后增强；SEM表面沟距约 **3.38µm（296线/mm）**，另一面约 **11.5µm（87线/mm）**，激光实验有离散衍射级次。它支持“表面衍射可以很重要”，不能推翻不同物种/制样的多层干涉证据，亦不能概括为所有抛光贝片必然同样变化。[原文DOI](https://doi.org/10.1364/OE.4.000177)，pp.178–180；[作者论文全文转载入口](https://www.researchgate.net/publication/24361894_Iridescence_color_of_a_shell_of_the_mollusk_Pinctada_Margaritifera_caused_by_diffraction)（未获取有效PDF）

**缺口：**本次未找到针对元明薄螺钿嵌片、控制总厚度连续磨薄同时记录角分辨反射谱的公开实验。可证伪方案是现代同种贝料同一位置留楔形厚度，逐点记录总厚、SEM周期/层数、粗糙度和角谱；固定背衬重复黑漆／白底／金属箔对照。这里是建议实验，不是本次已做工作。

## 4. 现成模型、代码与本镜头的选择

| 模型／实现 | 已核实内容 | 用于圆盘的适配与限制 |
|---|---|---|
| **Salman et al. 2021 HIT，TMM＋Monte Carlo** | 作者 [MATLAB仓库](https://github.com/katsgroup/PNAS_Nacre) 含两偏振TMM、随机层厚与实测拟合；已下少量源码至 `sources/optics_code/`。 | **首选物理依据。** 能保留晶板平均厚度、无序、层数和角度意义；应自己输出未归一化 `R(λ,θ)` 供渲染，不能把原拟合谱当现成BSDF。仓库未见LICENSE，不把公开可读等同于已授商业再分发权。 |
| **Byrnes《Multilayer optical calculations》＋Python tmm** | 作者 [代码](https://github.com/sbyrnes321/tmm) 明确MIT；支持相干/非相干多层、斜入射、吸收、s/p偏振及颜色计算。[论文](https://arxiv.org/abs/1603.02720) | 适合重建文石／有机随机堆栈、加入有限片厚和吸收衬底，预计算角度×层厚×无序度的谱LUT；它是平面光学求解器，仍需微表面BSDF和可见性／采样。 |
| **Ozaki et al.《Structural colors of pearls》2021** | TMM＋Kubelka–Munk散射；GLSL渲染与实拍对比（Fig.5），已下论文；未找到论文附带开放源代码。[DOI](https://doi.org/10.1038/s41598-021-94737-w) | 对珍珠白体、内透射与互补色有价值；黑漆背衬薄片没有白色珠核，不应照搬其核心散射halo。[对比图](img/optics_Ozaki_2021_F5_render_vs_real.png) |
| **Belcour & Barla SIGGRAPH 2017** | [作者页](https://belcour.github.io/blog/research/publication/2017/05/01/brdf-thin-film.html)提供论文、BRDFExplorer GLSL与旧Mitsuba C++；已下 `papers/belcour_2017.pdf`、`belcour_2017_code.zip`。反射Airy项分析积分减少RGB谱混叠。 | 是**单薄膜夹层**微表面虹彩，不是天然珍珠层随机多层模型；可作快速艺术近似、清漆／薄层研究。随附readme限定反射、说明Mitsuba白点问题；包内未见独立许可证。 |
| **KHR_materials_iridescence** | [Khronos正式扩展](https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_materials_iridescence)含GLSL近似和参数定义，基于Belcour/Barla。 | 现成实时路径，但只处理两界面薄膜；“螺钿总片厚”不能直接当该薄膜厚度。 |
| **Kang 2025，UE5 Substrate韩国螺钿** | 原论文元数据/摘要：四种螺钿材质，专家定性评价与运行性能，DOI **10.9728/dcs.2025.26.6.1699**。[期刊索引](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003217168) | 直接相关制作案例，但未获取全文／代码，不能引用节点数、光学数值或声称通过角谱测量验证。 |

**推荐方向（推断）：**用每块嵌片的固定“晶板平均厚度＋无序＋局部层法线”驱动随机多层TMM谱LUT，配透明介质表面高光和黑漆吸收衬底。若制作为RGB实时引擎，先按实际灯光谱与CIE响应离线积分再存LUT，别仅在RGB三个波长求解；Belcour2017讨论了离散RGB取样造成的谱混叠。[Belcour2017](https://doi.org/10.1145/3072959.3073620)；[Byrnes2016](https://arxiv.org/abs/1603.02720)

**旋转镜头关键推断：**纯绕平盘法线自转，若入射／观看几何不变、照明在各对应位置均匀、层平行盘面且各向同性，则每个材料点的局部入射角不因自转改变，整盘不应统一循环色相。希望转盘出现真实变彩，应让各嵌片局部层法线有贝料来源造成的倾斜／波动，或让盘倾转、照明形成非轴对称空间变化；有表面光栅的片还能因切线方向随旋转而改变衍射。微表面反射需按光源与视线的半向量对应局部微面，不能仅用相机对盘法线夹角查色。此结论是各向同性平面层模型的对称性推导，不是古盘旋转实测。[TMM斜入射定义](https://arxiv.org/abs/1603.02720)；[微表面薄膜理论](https://doi.org/10.1145/3072959.3073620)

完成判据建议（未实施）：同一片角谱随倾角峰位合理移动；不同切片的色块在物体坐标固定；改变灯位可改变彩色反射；仅绕法线转动的均匀平层对照不产生虚假的全局hue动画；不同N但相同周期的对照不能被误当成单层厚度扫描。
