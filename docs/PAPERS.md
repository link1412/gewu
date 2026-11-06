# 论文索引

**先说清楚:这不是我们读过的论文清单。** 项目没有记录过谁读过哪篇,所以这里只写能核验的事。

| 口径 | 数量 |
|---|---|
| 仓库里出现过的 DOI 和 arXiv 编号 | 414 |
| 手上有全文的文档(去重后的 PDF,混有图录和学位论文,都不公开) | 183 |
| 其中能按首页编号对上上面那 414 条的 | 72 |
| 读不出编号的 PDF(可能是老论文、中文期刊、图录,没有逐份辨认) | 99 |
| v1 进了代码的文献(实现、取数、校验) | 113,其中确认有全文 17 |
| v2 进了代码的文献(实现、取数) | 32,其中确认有全文 0 |
| 读过的篇数 | 没有记录,上限是有全文的那些 |

**进片的 v2 基本不是读论文做出来的。** 方法多凭记忆写,脚本自己写明了,比如 `v2/stills/s69_crack.py` 的「all known from memory, not re-read」,关键常数大多是估的。v1 下过功夫读论文、从图上读数,但 v1 的片子没有用上。

## 怎么看

- **链接:** ✓ Crossref、DataCite 或 arXiv 的接口返回了这个标题;◐ DOI 存在,接口没有元数据;○ 不是 DOI,链接没有经过接口核对;— 没找到链接,不猜。**✓ 只说明这篇论文存在、标题对得上,不说明有人读过。**
- **全文:** 「有」表示手上的 PDF 首页能读到这个编号,或按文件名认出。空着不等于没有。全文不在这个仓库里。
- **关系:** 实现,代码用了这个方法;取数,用了里面的数值;校验,拿它对结果;转引,数值来自调研报告,我们没读原文;提到,只是提到;背景,只在文档或调研里出现。
- **v2 的「实现」要小心读:** 有些条目代码里只写了方法名(如 SSP-RK3、2/3 去混叠、Naka-Rushton),文献是 2026-11 整理这份索引时才配上的,写代码时没有参考它。说明一栏写了的以说明为准。

## v2:进片的方案

### 进片镜头用到的

| 引用 | 文献 | 链接 | 全文 | 关系 | 镜头和说明 | 位置 |
|---|---|---|---|---|---|---|
| Kirchhoff plate | [Über das Gleichgewicht und die Bewegung einer elastischen Scheibe.](https://doi.org/10.1515/crll.1850.40.51) | ✓ |  | 实现 | `s24_jianzhi` 薄板方程。代码只写方法名。Crossref 这条元数据没有作者字段,按题名和年份确认。 | `v2/stills/s24_wind.py:8` |
| Planck | [Ueber das Gesetz der Energieverteilung im Normalspectrum](https://doi.org/10.1002/andp.19013090310) | ✓ |  | 实现 | `s14_datiehua` s42、s67 积分 Planck 到 RGB;s14 只取色相,亮度是替代。 | `v2/stills/s42_fire.py:13`<br>`v2/stills/s67_mutan.py:14` |
| Bragg-like shift | [The reflection of X-rays by crystals](https://doi.org/10.1098/rspa.1913.0040) | ✓ |  | 实现 | `s45_kongque` lam_eff 的角度偏移是 Bragg 样公式,代码明说是替代品,不是真实结构。 | `v2/stills/s45_shader.py:5`<br>`v2/stills/s45_shader.py:48` |
| Lucas-Washburn (Lucas) | [Ueber das Zeitgesetz des kapillaren Aufstiegs von Flüssigkeiten](https://doi.org/10.1007/bf01461107) | ✓ |  | 实现 | `s01_moyun,s38_richu` 走墨按 sqrt(t) 读到达时间场。 | `v2/stills/s38_richu.py:14` |
| Lucas-Washburn (Washburn) | [The Dynamics of Capillary Flow](https://doi.org/10.1103/physrev.17.273) | ✓ |  | 实现 | `s01_moyun,s38_richu` 同上。 | `v2/stills/s38_richu.py:14` |
| Henyey-Greenstein | [Diffuse radiation in the Galaxy](https://doi.org/10.1086/144246) | ✓ |  | 实现 | `s54_zoumadeng` 逐顶点算灯纸的前向散射。 | `v2/stills/s54_zoumadeng.py:510` |
| Orchard | [On surface levelling in viscous liquids and gels](https://doi.org/10.1007/bf03184629) | ✓ |  | 实现 | `s06_junyao` 毛细流平速率 h^3 k^4。代码只写姓,这篇是按题名匹配的。 | `v2/stills/s06_flow.py:5` |
| Naka-Rushton | [S-potentials from colour units in the retina of fish (Cyprinidae)](https://doi.org/10.1113/jphysiol.1966.sp008001) | ✓ |  | 实现 | `全片` 显影的色调曲线 x^c/(x^c+m)。代码只写方法名,选的是这篇。 | `v2/darkroom.py:25` |
| 2/3 dealiasing | [On the Elimination of Aliasing in Finite-Difference Schemes by Filtering High-Wavenumber Components](https://doi.org/10.1175/1520-0469%281971%29028<1074:oteoai>2.0.co;2) | ✓ |  | 实现 | `s76_yidi` 伪谱去混叠。代码只写方法名,文献是按该规则的通用引用选的。 | `v2/stills/s68_flow.py:6` |
| Zhang-Suen | [A fast parallel algorithm for thinning digital patterns](https://doi.org/10.1145/357994.358023) | ✓ |  | 实现 | `s69_mutan_raw` 裂纹中线的 GPU 细化。 | `v2/stills/s69_crack.py:201` |
| SSP-RK3 | [Efficient implementation of essentially non-oscillatory shock-capturing schemes](https://doi.org/10.1016/0021-9991%2888%2990177-5) | ✓ |  | 实现 | `s76_yidi` 时间推进。代码只写方法名,文献是按该格式的通用引用选的。 | `v2/stills/s68_flow.py:6` |
| Schlick | [An Inexpensive BRDF Model for Physically-based Rendering](https://doi.org/10.1111/1467-8659.1330233) | ✓ |  | 实现 | `s09_yinxing` 节点手写 Schlick,因为 Fresnel 节点用网格朝向。Schlick 近似公式通常引这篇,代码只写姓。 | `v2/stills/s09_shader.py:58` |
| surface nets | [Constrained elastic surface nets: Generating smooth surfaces from binary segmented data](https://doi.org/10.1007/bfb0056277) | ✓ |  | 实现 | `s69_mutan_raw` 隐函数网格化,torch。代码只写方法名,自写实现是否带 Gibson 的约束松弛没细查。 | `v2/stills/s69_shell.py:1`<br>`v2/studio_bpy.py:47` |
| GGX(pearl_shader、s62_shader 设分布) | [Microfacet Models for Refraction through Rough Surfaces](https://www.cs.cornell.edu/~srm/publications/EGSR07-btdf.html) | ○ |  | 实现 | `s36_nanzhu` 只设了 Cycles 节点的 distribution=GGX,实现在 Cycles 里。Crossref 没命中,页面可打开。 | `v2/stills/pearl_shader.py:94`<br>`v2/stills/s62_shader.py:32` |
| Pham, Amor, Marigo, Maurini 2011 | [Gradient Damage Models and Their Use to Approximate Brittle Fracture](https://doi.org/10.1177/1056789510386852) | ✓ |  | 实现 | `s69_mutan_raw` AT1 泛函,s69_crack.py 的相场裂纹按它写,profile d=(1−/x//2l)²;代码注明凭记忆,没重读。Crossref 的 issued 年是 2010(在线),代码写 2011。 | `v2/stills/s69_crack.py:7` |
| Wyman, Sloan, Shirley 2013 | [Simple Analytic Approximations to the CIE XYZ Color Matching Functions](https://jcgt.org/published/0002/02/01/) | ○ |  | 实现 | `s36_nanzhu` 多瓣高斯拟合 CIE,系数凭记忆输入,代码注明没对照原文。s36 进片。Crossref 无此刊;页面可打开,JCGT 链接未逐字核对。 | `v2/stills/s36_nanzhu.py:12`<br>`v2/stills/s27_float.py:69` |
| DIS | [Fast Optical Flow Using Dense Inverse Search](https://doi.org/10.1007/978-3-319-46493-0_29) | ✓ |  | 实现 | `全片(慢放镜头)` OpenCV DISOpticalFlow。代码只写方法名;arXiv 1603.03590 也对得上。 | `v2/tween.py:1` |
| Oklab | [A perceptual color space for image processing](https://bottosson.github.io/posts/oklab/) | ○ |  | 实现 | `全片` print_look 的色度压缩在 Oklab 里做。代码没写出处,按函数名对应;不是学术论文。 | `v2/darkroom.py:128`<br>`v2/darkroom.py:133` |

### 进片镜头转引和提到的

| 引用 | 文献 | 链接 | 全文 | 关系 | 镜头和说明 | 位置 |
|---|---|---|---|---|---|---|
| Jeffreys | [The Draining of a Vertical Plate](https://doi.org/10.1017/s0305004100015437) | ✓ |  | 提到 | `s06_junyao` 说明解算自然给出 h~sqrt(v) 的口沿薄釉,不是显式写入。代码只写姓。 | `v2/stills/s06_flow.py:6` |
| Yoshioka 2002 | [Effect of Macroscopic Structure in Iridescent Color of the Peacock Feathers](https://forma.katachi-jp.com/abstract/1702/17020169.html) | ○ |  | 提到 | `s45_kongque` 同 Zi 2003,只作为真实结构的引用。页面可打开,题名和作者已核对;没有 DOI。 | `v2/stills/s45_shader.py:4` |
| Zi 2003 | [Coloration strategies in peacock feathers](https://doi.org/10.1073/pnas.2133313100) | ✓ | 有 | 提到 | `s45_kongque` 说明真实结构色是 2-D 光子晶体,s45 没有实现,只用彩色镜面替代。 | `v2/stills/s45_shader.py:4` |
| Sicsic, Marigo, Maurini 2014 | [Initiation of a periodic array of cracks in the thermal shock problem: A gradient damage modeling](https://doi.org/10.1016/j.jmps.2013.09.003) | ✓ |  | 提到 | `s69_mutan_raw` 收缩与热震开裂的相场依据,代码注明凭记忆。 | `v2/stills/s69_crack.py:7` |
| Bourdin et al., PRL 2014 | [Morphogenesis and Propagation of Complex Cracks Induced by Thermal Shocks](https://doi.org/10.1103/physrevlett.112.014301) | ✓ |  | 提到 | `s69_mutan_raw` 同上,作为热震裂纹的依据,代码注明凭记忆。 | `v2/stills/s69_crack.py:7` |
| Baroudi et al. 2017 (arXiv 1604.01249) | [A thermo-mechanical explanation for the topology of crack patterns observed on the surface of charred wood and particle fibreboard](https://arxiv.org/abs/1604.01249) | ✓ |  | 提到 | `s69_mutan_raw` 两代裂纹(粗的先跑,冻进细的)的依据。代码写 2017,arXiv 首发是 2016-04-04;2017 这个年份没查到来源。 | `v2/stills/s69_crack.py:11` |
| Freyer 2020 | [Biophotonics of diversely coloured peacock tail feathers](https://doi.org/10.1039/d0fd00033g) | ✓ | 有 | 提到 | `s45_kongque` 同 Zi 2003,只作为真实结构的引用。 | `v2/stills/s45_shader.py:4` |
| Fukushima | [Nano-Hybrids of Clay Minerals with Water and Organic Polymers](https://www.jstage.jst.go.jp/article/jcssjclayscience/26/3-4/26_MS-22-5/_article/-char/en) | ○ |  | 提到 | `s02_yaobian` 同 Feng。代码只写姓;J-STAGE 页面的作者、年份、关键词 Yohen Tenmoku bowl 对得上。Crossref 检索和按 DOI(10.11362/jcssjclayscience.MS-22-5)查都没命中,DOI 取自页面元数据。 | `v2/stills/yohen.py:9` |
| Feng | [Phase-separated Tenmoku “Blue” glaze: Microstructure and coloring mechanism](https://doi.org/10.1016/j.jeurceramsoc.2023.05.051) | ✓ |  | 提到 | `s02_yaobian` 说明真实的蓝有弱角度依赖的散射部分,s02 用替代品。代码只写姓,年份来自 links。 | `v2/stills/yohen.py:9` |
| Stavenga 2011 | [Kingfisher feathers – colouration by pigments, spongy nanostructures and thin films](https://doi.org/10.1242/jeb.062620) | ✓ |  | 转引 | `s55_diancui` 蓝色在羽枝的海绵角蛋白而非羽小枝,决定了 s55 的颜色放在羽枝上。 | `v2/stills/s55_diancui.py:16` |
| 李媛 2013(s06_flow、s06_junyao) | [古代钧台窑钧釉“蚯蚓走泥纹”的成因探析](https://www.dpm.org.cn/Uploads/File/2020/02/16/u5e492452ec088.pdf) | ○ |  | 转引 | `s06_junyao` 蚯蚓走泥纹宽 1.0–1.6 mm,定解算痕宽的目标。链接来自调研报告,本次请求没连上。 | `v2/stills/s06_flow.py:10`<br>`v2/stills/s06_junyao.py:12` |
| Lu 2016 | [明宣德官窑祭红瓷器的呈色机制](https://html.rhhz.net/ZGKXYDXXB/20160320.htm) | ○ |  | 转引 | `s11_jiangdou` 总釉厚 513–674 µm,作 .5–.7 mm 釉壳的代理。 | `v2/stills/s11_jiangdou.py:9` |
| Gu 2021 | [Analytical investigation of the feather decoration technique of a seventeenth to eighteenth century Chinese imperial hanging screen](https://doi.org/10.1186/s40494-021-00555-8) | ✓ |  | 转引 | `s55_diancui` 点翠羽枝宽度约 40 µm 的依据。代码把它和谷岸 2021 写在一起,实是两篇。 | `v2/stills/s55_diancui.py:16`<br>`v2/stills/s55_diancui.py:295` |
| 谷岸 et al.(代码写作 Gu 2021, 谷岸 et al.) | [从微观尺度看清代宫廷的点翠技法与色彩表现](https://img.dpm.org.cn/Uploads/File/2022/03/09/u62282bfb2f0be.pdf) | ○ |  | 转引 | `s55_diancui` 羽枝宽 40–70 µm。链接来自调研报告,本次请求没连上(000)。 | `v2/stills/s55_diancui.py:16` |
| Lee 2021 | [Microstructures in Blue Feathers of the Common Kingfisher](https://doi.org/10.22920/pnie.2021.2.1.21) | ✓ |  | 转引 | `s55_diancui` 题名和期号来自调研报告,DOI 只解析到 handle,元数据没查到。同样支持蓝色在羽枝。 | `v2/stills/s55_diancui.py:16` |
| Wang 2024 | [Wang 2024](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005) | ✓ | 有 | 转引 | `s06_junyao` 钧釉气泡小于 100 µm 的依据。DOI 只解析到 handle,题名和作者没查到。 | `v2/stills/s06_junyao.py:14` |
| Kang 2025 | [Elucidating and Biomimicking the Coloration Mechanisms Responsible for the Vibrant Blue Hues of the Common Kingfisher](https://doi.org/10.1002/adom.202402936) | ✓ |  | 转引 | `s55_diancui` 翠鸟羽峰值 471–500 nm,来自 调研,定 s55 色带的目标。 | `v2/stills/s55_diancui.py:17` |
| Meier 2026 | [Investigating Structurally and Pigmentary Colored Featherworks via Noninvasive Methodologies](https://doi.org/10.1021/acsomega.6c02770) | ✓ |  | 转引 | `s55_diancui` 523 nm@15° 的反射数据,来自 调研。 | `v2/stills/s55_diancui.py:17` |

### 没进片的镜头和其他

| 引用 | 文献 | 链接 | 全文 | 关系 | 镜头和说明 | 位置 |
|---|---|---|---|---|---|---|
| Johnson & Christy 1972 | [Optical Constants of the Noble Metals](https://doi.org/10.1103/physrevb.6.4370) | ✓ |  | 取数 | 金 n、k 表(经 refractiveindex.info),s27_float 用 Airy 算透射。s27_float 没进片。 | `v2/stills/s27_float.py:15`<br>`v2/stills/s27_float.py:57` |
| Shi 2020 | [Study on the coloring mechanism of the Ru celadon glaze in the Northern Song Dynasty](https://doi.org/10.1016/j.ceramint.2020.06.139) | ✓ |  | 取数 | 拟合 sigma_s' 给汝瓷介质;s29、s52 没进片。 | `v2/stills/s29_ruyao.py:6`<br>`v2/stills/s52_cand.py:8` |
| Bashforth-Adams | An attempt to test the theories of capillary action | — |  | 实现 | 从冠顶积分 Young-Laplace。Crossref 没有原书,只有一篇 2026 的数字化表格。这几镜没进片。 | `v2/stills/s43_heye.py:89`<br>`v2/stills/s58_heye.py:163` |
| MacCormack | [The effect of viscosity in hypervelocity impact cratering](https://doi.org/10.2514/6.1969-354) | ✓ |  | 实现 | s42 限幅 MacCormack 平流。代码只写方法名。s42 没进片。 | `v2/stills/s42_fire.py:10`<br>`v2/stills/s42_fire.py:218` |
| Catmull-Rom | [A class of local interpolating splines](https://doi.org/10.1016/b978-0-12-079050-0.50020-5) | ✓ |  | 实现 | 笔画样条。s26 没进片。 | `v2/stills/s26_qinghua.py:70` |
| L-BFGS-B | [A Limited Memory Algorithm for Bound Constrained Optimization](https://doi.org/10.1137/0916069) | ✓ |  | 实现 | scipy 的 minimize(L-BFGS-B)。s27_float 没进片。 | `v2/stills/s27_float.py:11`<br>`v2/stills/s27_float.py:257` |
| Angot, Bruneau, Fabrie 1999 | [A penalization method to take into account obstacles in incompressible viscous flows](https://doi.org/10.1007/s002110050401) | ✓ |  | 实现 | Brinkman 罚函数,s70 取无穷阻力极限(每步乘掩膜再投影)。s70 没进片。 | `v2/stills/s70_flow.py:7` |
| vorticity confinement(s42_fire) | [Visual simulation of smoke](https://doi.org/10.1145/383259.383260) | ✓ |  | 实现 | 弱涡量约束。代码只写方法名,图形学里常引这篇。s42 没进片。 | `v2/stills/s42_fire.py:10` |
| Kolomenskiy and Schneider 2009 | [A Fourier spectral method for the Navier–Stokes equations with volume penalization for moving solid obstacles](https://doi.org/10.1016/j.jcp.2009.04.026) | ✓ |  | 实现 | 同上,谱方法版本。s70 没进片。 | `v2/stills/s70_flow.py:7` |
| Einstein 1926 | [Die Ursache der Mäanderbildung der Flußläufe und des sogenannten Baerschen Gesetzes](https://doi.org/10.1007/bf01510300) | ✓ |  | 提到 | 茶叶向碗心聚集的边界层解释,代码只是引用。 | `v2/stills/s70_flow.py:7` |
| Huppert 1982 | [Flow and instability of a viscous current down a slope](https://doi.org/10.1038/300427a0) | ✓ |  | 提到 | 代码说明本解算没有 Huppert 意义上的接触线指进。s74 没进片。 | `v2/stills/s74_flow.py:7` |
| Cheerios effect | [The “Cheerios effect”](https://doi.org/10.1119/1.1898523) | ✓ |  | 提到 | 说明气泡靠壁聚集。代码只写效应名。s70 没进片。 | `v2/stills/s70_chatang.py:337` |
| doi 10.1007/s00226-005-0062-5 | [Morphological characteristics of Quercus variabilis charcoal prepared at different temperatures](https://doi.org/10.1007/s00226-005-0062-5) | ✓ |  | 转引 | 白栎炭窑收缩 −26%/−15%,裂纹沿射线走;代码注明只读了搜索摘要。s67 没进片。 | `v2/stills/s67_mutan.py:13` |
| Srinivas et al. 2011 | [Binary diffusion coefficients of phenolic compounds in subcritical water using a chromatographic peak broadening technique](https://doi.org/10.1016/j.fluid.2010.12.003) | ✓ |  | 转引 | 儿茶素扩散系数约 2.2e-6 cm²/s(25 °C),调研报告读图。s70 没进片。 | `v2/stills/s70_flow.py:11` |
| Sentkowska & Pyrzynska 2022 | [Does the Type Matter? Verification of Different Tea Types’ Potential in the Synthesis of SeNPs](https://doi.org/10.3390/antiox11122489) | ✓ |  | 转引 | 红茶汤吸光度,读图,红端在误差内选。s68_tea 没进片。 | `v2/stills/s68_tea.py:3`<br>`v2/stills/s68_tea.py:11` |

### 经典定律,没有单一文献

代码用到,不配链接:Beer-Lambert、Airy 公式、Young-Laplace、Fresnel、Kirchhoff(发射率)。

## v1:放弃的方案

路径相对 `v1/`。v1 的片子没有用上这些。

### 水墨和宣纸

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Iwasaki 1937 | [Some Notes on Sand Filtration](https://doi.org/10.1002/j.1551-8833.1937.tb14014.x) | ✓ |  | 实现 | 第 1/38 镜 sim.py 的深床过滤方程,λ 是假设值 | `v1/shots/01-38-ink/sim.py:12`<br>`v1/docs/shots/01-38-ink.md:35` |
| Yamauchi & Usami 2005 | [Characteristic Mechanical Properties of Washi Papers](https://doi.org/10.2524/jtappij.59.1546) | ✓ |  | 取数 | 和纸 KM 散射系数 S=31 m²/kg,作宣纸的替代值 | `v1/shots/01-38-ink/optics.json:5`<br>`v1/docs/shots/01-38-ink.md:29` |
| Bond & Bergstrom 2006 | [Light Absorption by Carbonaceous Particles: An Investigative Review](https://doi.org/10.1080/02786820500421521) | ✓ | 有 | 取数 | 炭的 MAC 7.5 m²/g 和粗粒级 AAE≈1 | `v1/shots/01-38-ink/optics.json:14`<br>`v1/docs/shots/01-38-ink.md:37` |
| Lu et al. 2023 | [Effect of Bone Glue Concentration on the Physical Properties of Xuan Paper under Traditional Drag-dye Sizing Technology](https://doi.org/10.3969/j.issn.0253-2417.2023.03.008) | ◐ |  | 取数 | 生宣定量 26.9 g/m²、厚 69.6 µm | `v1/shots/01-38-ink/params.json:7`<br>`v1/docs/shots/01-38-ink.md:29` |
| Lekner & Dorf 1988 | [Why some things are darker when wet](https://doi.org/10.1364/ao.27.001278) | ✓ | 有 | 背景 | DESIGN 记为湿纸变暗的机理;湿纸 S 系数是我们推的 | `v1/DESIGN.md:333` |
| Modeling in Computer Graphics | [Modeling in Computer Graphics](https://doi.org/10.1007/978-4-431-68147-2) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:116` |
| Curtis et al. 1997 | [Computer-generated watercolor](https://doi.org/10.1145/258734.258896) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:113` |
| Lee 1999 | [Simulating oriental black-ink painting](https://doi.org/10.1109/38.761553) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:117` |
| Jensen et al. 1999 | [Rendering of Wet Materials](https://doi.org/10.2312/egwr/egwr99/273-282) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:184` |
| Lee 2001 | [Diffusion rendering of black ink paintings using new paper and ink models](https://doi.org/10.1016/s0097-8493%2800%2900132-1) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:118` |
| Swider et al. 2003 | [Characterization of Chinese ink in size and surface](https://doi.org/10.1016/s1296-2074%2803%2900044-x) | ✓ |  | 背景 | 镜头文档记了墨团簇粒径 232、212 nm 作参考,没有进代码 | `v1/docs/shots/01-38-ink.md:35` |
| Chu et al. 2005 | [MoXi](https://doi.org/10.1145/1073204.1073221) | ✓ |  | 背景 | 第 1/38 镜用自写 sim.py,没有用 MoXi;DESIGN 列入 guofeng 引擎的计划 | `v1/DESIGN.md:229`<br>`v1/docs/layers.md:36` |
| PRESSURE BASED INK DIFFUSION MODEL FOR REAL-TIME SIMULATION OF CHINESE CALLIGRAPHY | [PRESSURE BASED INK DIFFUSION MODEL FOR REAL-TIME SIMULATION OF CHINESE CALLIGRAPHY](https://doi.org/10.5220/0002071902710276) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:120` |
| Xie et al. 2010 | [IR2s](https://doi.org/10.1145/1809939.1809947) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:121` |
| Ning et al. 2011 | [Contour-driven Sumi-e rendering of real photos](https://doi.org/10.1016/j.cag.2010.11.017) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:122` |
| Wu et al. 2016 | [Ink Dispersion on Qianlong Xuan Paper with Improved Ink Expression](https://doi.org/10.1016/j.jmst.2015.12.014) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:47`<br>`v1/docs/research/ink-xuan.md:189` |
| Walji et al. 2016 | [Influence of Geometry and Surrounding Conditions on Fluid Flow in Paper-Based Devices](https://doi.org/10.3390/mi7050073) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:191` |
| Xie et al. 2018 | [Web-based SBLR method of multimedia tools for computer-aided drawing](https://doi.org/10.1007/s11042-018-5949-x) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:123` |
| Das et al. 2019 | [Paper Stacks for Uniform Rehydration of Dried Reagents in Paper Microfluidic Devices](https://doi.org/10.1038/s41598-019-52202-9) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:190` |
| Shao et al. 2019 | [A new kind of nanocomposite Xuan paper comprising ultralong hydroxyapatite nanowires and cellulose fibers with a unique ink wetting performance](https://doi.org/10.1039/c9ra08349a) | ✓ |  | 背景 | 镜头文档记了孔隙率 75.5% 和水墨同行的定性观察,代码里没查到 | `v1/docs/shots/01-38-ink.md:29` |
| Patari et al. 2020 | [Liquid Wicking in a Paper Strip: An Experimental and Numerical Study](https://doi.org/10.1021/acsomega.0c02407) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:192` |
| Hu et al. 2020 | [Disposable Paper-on-CMOS Platform for Real-Time Simultaneous Detection of Metabolites](https://doi.org/10.1109/tbme.2019.2962239) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:182` |
| Yan et al. 2021 | [Chinese ink-facilitated fabrication of paper-based composites as electrodes for supercapacitors](https://doi.org/10.1080/19475411.2021.1959463) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:195` |
| Liu et al. 2022 | [Reproducing ancient Chinese ink depending on gelatin/chitosan and modern experimental methodology](https://doi.org/10.1186/s40494-022-00739-w) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:197` |
| Zhu et al. 2022 | [Fluorescent carbon nanoparticles from Chinese ink](https://doi.org/10.1360/ssc-2022-0085) | ✓ |  | 背景 |  | `v1/docs/research/ink-xuan.md:194` |
| Sipkens et al. 2023 | [Overview of methods to characterize the mass, size, and morphology of soot](https://doi.org/10.1016/j.jaerosci.2023.106211) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:97` |
| Nicasy et al. 2024 | [Increasing particle concentration enhances particle penetration depth but slows down liquid imbibition in thin fibrous filters](https://doi.org/10.1016/j.colsurfa.2024.133146) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:126` |
| Qi et al. 2025 | [Study of Ink stick unearthed from the tomb of Fan Xiaochong in Shaanxi Province](https://doi.org/10.1038/s40494-025-01976-5) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:196` |
| Dong et al. 2025 | [Comparison of Aging Performances and Mechanisms: Super-Durable Fire-Resistant “Xuan Paper” Versus Chinese Traditional Xuan Paper](https://doi.org/10.3390/molecules30020263) | ✓ | 有 | 背景 |  | `v1/docs/research/ink-xuan.md:50` |

### 银杏和植物

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Stokes 1862 | [IV. On the intensity of the light reflected from or transmitted through a pile of plates](https://doi.org/10.1098/rspl.1860.0119) | ✓ |  | 实现 | prospect.py 多层板叠加的递推 | `v1/materials/yinxing/prospect.py:7`<br>`v1/tests/yinxing/test_prospect.py:7` |
| Stern 1964 | [Transmission of Isotropic Radiation Across an Interface Between Two Dielectrics](https://doi.org/10.1364/ao.3.000111) | ✓ |  | 实现 | prospect.py 里介电面透射的闭式 | `v1/materials/yinxing/prospect.py:12`<br>`v1/tests/yinxing/test_prospect.py:5` |
| Allen 1969 | [Interaction of Isotropic Light with a Compact Plant Leaf*](https://doi.org/10.1364/josa.59.001376) | ✓ |  | 实现 | prospect.py 里 N 层板的写法 | `v1/materials/yinxing/prospect.py:7` |
| Allen 1973 | [Transmission of isotropic light across a dielectric surface in two and three dimensions*](https://doi.org/10.1364/josa.63.000664) | ✓ |  | 实现 | prospect.py 里介电面按入射角范围平均的透射率 | `v1/materials/yinxing/prospect.py:13` |
| Jacquemoud & Baret 1990 | [PROSPECT: A model of leaf optical properties spectra](https://doi.org/10.1016/0034-4257%2890%2990100-z) | ✓ |  | 实现 | prospect.py 的 N 层板叶片模型 | `v1/materials/yinxing/prospect.py:6`<br>`v1/materials/lychee/material.json:22` |
| Jensen, Marschner, Levoy & Hanrahan 2001 | [A practical model for subsurface light transport](https://doi.org/10.1145/383259.383319) | ✓ |  | 实现 | 荔枝的层模型用偶极 R_d;测试物体的大理石取其参数 | `v1/materials/lychee/optics.py:125`<br>`v1/tests/optics/check_backlit.py:37` |
| Féret et al. 2017 | [PROSPECT-D: Towards modeling leaf optical properties through a complete lifecycle](https://doi.org/10.1016/j.rse.2017.03.004) | ✓ |  | 实现 | prospect.py 实现 PROSPECT-D 并用其比吸收;荔枝花青素吸收的形状也来自它 | `v1/materials/lychee/optics.py:58`<br>`v1/materials/yinxing/fit.py:9` |
| Critchfield 1970 | [Shoot Growth and Heterophylly in Ginkgo biloba](https://doi.org/10.1086/336526) | ✓ |  | 取数 | 晚生长枝叶缺刻可到叶长三分之一 | `v1/objects/yinxing/leaf.py:639`<br>`v1/objects/yinxing/notched.json:69` |
| Segelstein 1981 | Segelstein 1981 | — |  | 取数 | 纯水复折射率,Pope & Fry 范围之外 | `v1/materials/lychee/optics.py:46`<br>`v1/materials/lychee/material.json:17` |
| Pope & Fry 1997 | [Absorption spectrum (380–700 nm) of pure water II Integrating cavity measurements](https://doi.org/10.1364/ao.36.008710) | ✓ |  | 取数 | 纯水吸收 380–727.5 nm | `v1/materials/lychee/optics.py:46`<br>`v1/materials/lychee/material.json:16` |
| Nacif et al. 2001 | Nacif et al. 2001 | — |  | 取数 | 荔枝果实尺寸和果皮结构 | `v1/materials/lychee/material.json:11`<br>`v1/docs/materials/lychee.md:30` |
| Saeys et al. 2008 | [Optical properties of apple skin and flesh in the wavelength range from 350 to 2200 nm](https://doi.org/10.1364/ao.47.000908) | ✓ |  | 取数 | 苹果组织 g 0.6–0.8,作荔枝替代 | `v1/materials/lychee/material.json:19`<br>`v1/docs/materials/lychee.md:39` |
| Qin & Lu 2008 | [Measurement of the optical properties of fruits and vegetables using spatially resolved hyperspectral diffuse reflectance imaging technique](https://doi.org/10.1016/j.postharvbio.2008.03.010) | ✓ |  | 取数 | μs' 随波长下降的形状 | `v1/materials/lychee/material.json:61` |
| Leigh et al. 2011 | [Structural and hydraulic correlates of heterophylly in Ginkgo biloba](https://doi.org/10.1111/j.1469-8137.2010.03476.x) | ✓ |  | 取数 | 叶片厚度和叶脉间距 0.69 mm | `v1/materials/yinxing/measure_var.py:7`<br>`v1/materials/yinxing/material.json:23` |
| Klimko et al. 2015 | Klimko et al. 2015 | — | 有 | 取数 | 银杏叶厚 316–626 µm,进叶片参数和叶脉谱族假设 | `v1/materials/yinxing/material.json:24`<br>`v1/objects/yinxing/lamp.json:83` |
| Fang et al. 2016 | [Investigation of absorption and scattering characteristics of kiwifruit tissue using a single integrating sphere system](https://doi.org/10.1631/jzus.b1500086) | ✓ |  | 取数 | 猕猴桃 μs' 0.120–0.946 /mm,作荔枝果肉的替代范围 | `v1/materials/lychee/material.json:20` |
| Carvalho et al. 2017 | [The hydraulic architecture of Ginkgo leaves](https://doi.org/10.3732/ajb.1700277) | ✓ |  | 取数 | 叶柄两维管束,各供一半叶片 | `v1/objects/yinxing/leaf.py:35`<br>`v1/docs/materials/yinxing.md:35` |
| Carvalho et al. 2018 | [Phloem networks in leaves](https://doi.org/10.1016/j.pbi.2017.12.007) | ✓ |  | 取数 | 二歧分叉角 22°±2°(综述引述,原测没核) | `v1/objects/yinxing/lamp.json:27`<br>`v1/docs/materials/yinxing.md:36` |
| Baresch et al. 2019 | [Competition for epidermal space in the evolution of leaves with high physiological rates](https://doi.org/10.1111/nph.15476) | ✓ |  | 取数 | 叶脉宽 136 µm 的参考 | `v1/objects/yinxing/lamp.json:63` |
| Li et al. 2020 | [Physiological and Transcriptomic Changes During Autumn Coloration and Senescence in Ginkgo biloba Leaves](https://doi.org/10.1016/j.hpj.2020.11.002) | ✓ |  | 取数 | 叶绿素和类胡萝卜素的季节变化,senescence 取用 | `v1/materials/yinxing/material.json:21` |
| Morimoto et al. 2022 | [Spectral measurement of daylights and surface properties of natural objects in Japan](https://doi.org/10.1364/oe.441063) | ✓ |  | 取数 | 黄银杏叶实测谱,fit_spectra.py 的拟合目标 | `v1/materials/yinxing/fit_spectra.py:1`<br>`v1/materials/yinxing/material.json:14` |
| 中国农学通报 2023 | [中国农学通报 2023](https://doi.org/10.11924/j.issn.1000-6850.casb2022-0833) | ◐ |  | 取数 | 桂味荔枝的单果重和 TSS 19.27%(只看了摘要) | `v1/materials/lychee/material.json:15`<br>`v1/objects/lychee/guiwei.json:9` |
| Xu & Ye 2023 | [Light scattering in stacked mesophyll cells results in similarity characteristic of solar spectral reflectance and transmittance of natural leaves](https://doi.org/10.1038/s41598-023-31718-1) | ✓ |  | 取数 | 绿银杏叶 Cab 42.1 µg/cm² | `v1/materials/yinxing/material.json:19`<br>`v1/docs/materials/yinxing.md:27` |
| Lichtenthaler 2023 | [Strong increase of photosynthetic pigments and leaf size in a pruned Ginkgo biloba tree](https://doi.org/10.32615/ps.2023.020) | ✓ | 有 | 取数 | 绿叶 Cab 47.1、Car 10.3 µg/cm²(经调研报告转述) | `v1/materials/yinxing/material.json:20`<br>`v1/docs/materials/yinxing.md:28` |
| Jurcevic Sangut & Samec 2024 | Jurcevic Sangut & Samec 2024 | — |  | 取数 | Cab 从 7 月 2.07 降到 11 月 0.15 mg/g | `v1/materials/yinxing/material.json:22` |
| Peters et al. 2022 | [Leaf Optical Traits collected at the University of Saskatchewan (LOTUS)](https://doi.org/10.20383/103.0606) | ✓ |  | 校验 | lotus_rt.py 用其 OAK01、CCAN2 叶片检验 PROSPECT 的 R→T | `v1/materials/yinxing/lotus_rt.py:1`<br>`v1/docs/materials/yinxing.md:15` |
| 高飞飞 等 2000 | [荔枝果皮叶绿素、类胡萝卜素、花青苷合成规律及其对着色的影响](https://doi.org/10.7671/j.issn.1001-411x.2000.01.005) | ◐ |  | 背景 | 只取摘要的定性结论(果皮色素变化),没有取数值 | `v1/materials/lychee/material.json:23` |

### 汝窑和官窑

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Appen (经 EP3013762B1 转引) | [EP3013762B1(转引 Appen 系数的专利)](https://patents.google.com/patent/EP3013762B1) | ○ |  | 实现 | 汝釉和胭脂水玻璃的折射率加和法,系数经专利转引,原文(Stekla 1974)没核对 | `v1/materials/ru_glaze/card.py:4`<br>`v1/materials/ru_glaze/glaze.py:5` |
| Cotterell & Rice 1980 | [Slightly curved or kinked cracks](https://doi.org/10.1007/bf00012619) | ✓ |  | 实现 | crackle.py 的裂尖转向规则 | `v1/crafts/crackle/crackle.py:28`<br>`v1/shots/06-guan/crackle.py:207` |
| Hapke 1981 | [Bidirectional reflectance spectroscopy: 1. Theory](https://doi.org/10.1029/jb086ib04p03039) | ✓ |  | 实现 | 裂缝沉积物光谱的紧密混合公式 | `v1/crafts/deposition/deposit.py:5`<br>`v1/crafts/deposition/deposition.json:26` |
| Hutchinson & Suo 1992 | [Mixed Mode Cracking in Layered Materials](https://doi.org/10.1016/s0065-2156%2808%2970164-9) | ✓ |  | 实现 | crackle.py 的通道裂能量释放率 G=Zσ²e/E' | `v1/crafts/crackle/crackle.py:13`<br>`v1/shots/06-guan/crackle.py:13` |
| Bohn et al. 2005 | [Hierarchical crack pattern as formed by successive domain divisions. II. From disordered to deterministic behavior](https://doi.org/10.1103/physreve.71.046215) | ✓ | 有 | 实现 | crackle.py 逐条开裂的层次网模型 | `v1/crafts/crackle/crackle.py:7`<br>`v1/shots/06-guan/crackle.py:7` |
| Medenbach & Shannon 1997 | [Refractive indices and optical dispersion of 103 synthetic and mineral oxides and silicates measured by a small-prism technique](https://doi.org/10.1364/josab.14.003299) | ✓ |  | 取数 | 钙长石三轴折射率,577 nm 平均 1.582 | `v1/materials/ru_glaze/material.json:20` |
| Li, Deng & Xu 2001 | [Technical Studies and Replication of Guan Ware, an Ancient Chinese Ceramic](https://doi.org/10.1557/mrs2001.16) | ✓ | 有 | 取数 | 官釉厚 0.5–2 mm 和热膨胀系数,开片模拟取用;金丝铁线两代的说法 | `v1/crafts/crackle/crackle.py:4`<br>`v1/shots/06-guan/crackle.py:4` |
| Li et al. 2005 | [Study on Ru ware glaze of the Northern Song dynasty: One of the earliest crystalline-phase separated glazes in ancient China](https://doi.org/10.1016/j.ceramint.2004.07.002) | ✓ |  | 取数 | 釉厚和钙长石针的显微尺寸;宽度 800 nm 仍是假设 | `v1/materials/ru_glaze/material.json:15`<br>`v1/docs/materials/ru_glaze.md:71` |
| Volotinen 2008 | Volotinen 2008 | — |  | 取数 | Fe²⁺、Fe³⁺ 吸收的分峰参数 | `v1/materials/ru_glaze/glaze.py:7`<br>`v1/materials/ru_glaze/hue.py:3` |
| Klement, Kraxner & Liska 2009 | Klement, Kraxner & Liska 2009 | — |  | 取数 | ε(Fe²⁺,1000 nm)=15.99;与 Bamford 的 30 差一倍,按 a* 选用 | `v1/materials/ru_glaze/material.json:17`<br>`v1/docs/materials/ru_glaze.md:45` |
| Yang 2012 | [Using Optical Coherence Tomography to Characterize the Crack Morphology of Ceramic Glaze and Jade](https://doi.org/10.5772/31213) | ✓ | 有 | 取数 | 读四条裂缝的倾角 10–19°,裂面网格 faces.py 取用 | `v1/crafts/crackle/faces.py:19`<br>`v1/materials/guan_glaze/linetest.py:36` |
| Kokaly et al. 2017 | [USGS Spectral Library Version 7](https://doi.org/10.3133/ds1035) | ✓ |  | 取数 | USGS 矿物谱,作开片沉积物的替代谱 | `v1/shots/06-guan/scene.py:67`<br>`v1/crafts/deposition/deposition.json:124` |
| Duminis et al. 2018 | [Predicting refractive index of fluoride containing glasses for aesthetic dental restorations](https://doi.org/10.1016/j.dental.2018.01.024) | ✓ |  | 取数 | Appen 加和法缺的 P₂O₅ 系数 | `v1/materials/ru_glaze/glaze.py:43`<br>`v1/materials/ru_glaze/material.json:19` |
| Chen et al. 2020 | [Analysis of structural effects on coloring mechanism of Ru celadon porcelain](https://doi.org/10.1002/ces2.10058) | ✓ |  | 取数 | 汝釉卡取液滴和钙长石的结构数据 | `v1/materials/ru_glaze/material.json:14` |
| Shi et al. 2020 | [Study on the coloring mechanism of the Ru celadon glaze in the Northern Song Dynasty](https://doi.org/10.1016/j.ceramint.2020.06.139) | ✓ |  | 取数 | 两片汝瓷 R1、R2 的成分和 Lab,作为 slab 拟合目标 | `v1/materials/ru_glaze/material.json:12` |
| Yu et al. 2021 | Yu et al. 2021 | — |  | 取数 | 官釉 J2 片的反射谱,glaze_fit.py 反解吸收散射;光泽 46.7 GU | `v1/shots/06-guan/glaze_fit.py:8`<br>`v1/materials/guan_glaze/material.json:157` |
| Li et al. 2022 (Microsc. Microanal.) | Li et al. 2022 (Microsc. Microanal.) | — |  | 取数 | SEM 截面的裂缝通道形状,faces.py 取用 | `v1/crafts/crackle/faces.py:169`<br>`v1/docs/materials/guan_glaze.md:140` |
| Zhou et al. 2023 | [Corrosion Research on Ru Porcelain Glazes Excavated at Qingliangsi, Baofeng, China](https://doi.org/10.3390/coatings13061011) | ✓ |  | 取数 | 清凉寺釉两相 EDS 成分 | `v1/materials/ru_glaze/material.json:13` |
| Wu et al. 2025 | Wu et al. 2025 | — | 有 | 取数 | 金丝铁线的物相,决定选哪种 USGS 替代谱 | `v1/crafts/deposition/deposit.py:3`<br>`v1/shots/06-guan/scene.py:65` |
| Lahlil et al. 2013 | Lahlil et al. 2013 | — |  | 校验 | 官窑胞径 1.7–14.1 mm,对比模拟的 5.7 mm | v1 |
| 贾翠 2016 | 贾翠 2016 | — |  | 背景 |  | `v1/docs/materials/ru_glaze.md:144` |

### 渲染算法

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Wertheim 1963 | [Exact Solution of the Percus-Yevick Integral Equation for Hard Spheres](https://doi.org/10.1103/physrevlett.10.321) | ✓ |  | 实现 | mie.py 的 Percus-Yevick 硬球结构因子 | `v1/tools/mie.py:239`<br>`v1/docs/mie.md:67` |
| Thiele 1963 | [Equation of State for Hard Spheres](https://doi.org/10.1063/1.1734272) | ✓ |  | 实现 | mie.py 的 Percus-Yevick 硬球结构因子 | `v1/tools/mie.py:239`<br>`v1/docs/mie.md:67` |
| Ashcroft & Lekner 1966 | [Structure and Resistivity of Liquid Metals](https://doi.org/10.1103/physrev.145.83) | ✓ |  | 实现 | mie.py 的结构因子闭式 | `v1/tools/mie.py:248`<br>`v1/docs/mie.md:68` |
| Lentz 1976 | [Generating Bessel functions in Mie scattering calculations using continued fractions](https://doi.org/10.1364/ao.15.000668) | ✓ |  | 实现 | mie.py 用改进 Lentz 连分式算对数导数起点 | `v1/tools/mie.py:11`<br>`v1/docs/mie.md:17` |
| Wiscombe 1980 | [Improved Mie scattering algorithms](https://doi.org/10.1364/ao.19.001505) | ✓ |  | 实现 | tools/mie.py 的项数和数值稳定做法;MIEV0 测试例也来自这里 | `v1/tools/mie.py:14`<br>`v1/docs/mie.md:51` |
| Bohren & Huffman 1983 | [Absorption and Scattering of Light by Small Particles](https://doi.org/10.1002/9783527618156) | ✓ |  | 实现 | tools/mie.py 的 BHMIE 递推和测试样例按这本书 | `v1/materials/yanzhi/enamel.py:18`<br>`v1/tests/mie/test_mie.py:5` |
| Kinning & Thomas 1984 | [Hard-sphere interactions between spherical domains in diblock copolymers](https://doi.org/10.1021/ma00139a013) | ✓ |  | 实现 | mie.py 结构因子闭式按它的式 7–8 写 | `v1/tools/mie.py:249`<br>`v1/docs/mie.md:68` |
| Thompson & Barnett 1986 | [Coulomb and Bessel functions of complex arguments and order](https://doi.org/10.1016/0021-9991%2886%2990046-x) | ✓ |  | 实现 | mie.py 连分式的改进 Lentz 写法 | `v1/tools/mie.py:55`<br>`v1/docs/mie.md:52` |
| Wang, Jacques & Zheng 1995 | [MCML—Monte Carlo modeling of light transport in multi-layered tissues](https://doi.org/10.1016/0169-2607%2895%2901640-f) | ✓ |  | 实现 | tools/slab.py 的 MCML 风格分层蒙特卡罗参照 | `v1/tools/slab.py:14`<br>`v1/docs/slab.md:20` |
| Magkiriadou et al. 2014 | [Absence of red structural color in photonic glasses, bird feathers, and certain beetles](https://doi.org/10.1103/physreve.90.062302) | ✓ |  | 实现 | mie.py 里结构因子和 Mie 相乘算有序粒子散射的公式 | `v1/tools/mie.py:22`<br>`v1/docs/mie.md:61` |
| Heitz 2018 | [Sampling the GGX Distribution of Visible Normals](https://jcgt.org/published/0007/04/01/) | ○ |  | 实现 | tools/slab.py 里按 GGX 可见法线采样 | `v1/tests/yohen/pbrt_checks.py:84`<br>`v1/tools/slab.py:79` |
| Vynck et al. 2021 | [Light in correlated disordered media](https://arxiv.org/abs/2106.13892) | ✓ |  | 实现 | mie.py 按综述式 110–111 算相关无序介质的结构因子修正 | `v1/tools/mie.py:23`<br>`v1/docs/mie.md:62` |
| van de Hulst 1957 | van de Hulst 1957 | — |  | 校验 | mie.py 用 Rayleigh-Gans-Debye 极限校验 | `v1/tools/mie.py:405`<br>`v1/docs/mie.md:86` |
| Chandrasekhar 1960 | Chandrasekhar 1960 | — |  | 校验 | slab.py 对半无限漫射解校验 | `v1/tools/slab.py:444`<br>`v1/docs/slab.md:31` |
| Stucki et al. 2024 | [Physically-based Path Tracer using WebGPU and OpenPBR](https://arxiv.org/abs/2407.19977) | ✓ |  | 背景 |  | `v1/docs/research/webgpu-vs-cycles.md:65`<br>`v1/docs/research/webgpu-vs-cycles.md:94` |
| Eschmann et al. 2026 | [HyperDrone: Simulation-to-Reality Transfer at Millions of Frames per Second](https://arxiv.org/abs/2610.28950) | ✓ |  | 背景 |  | `v1/docs/research/webgpu-vs-cycles.md:11`<br>`v1/docs/research/webgpu-vs-cycles.md:130` |

### 螺钿

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Liu et al. 1999 | [Iridescent Color of a Shell of the Mollusk Pinctada Margaritifera Caused by Diffraction](https://doi.org/10.1364/oe.4.000177) | ✓ |  | 取数 | 抛光面 3.38 µm 光栅,推断层倾角 RMS 6.8°(推断值,无实测) | `v1/shots/19-luodian/pattern.py:13`<br>`v1/docs/shots/19-dianluo.md:49` |
| Song et al. 2003 | [Structural and mechanical properties of the organic matrix layers of nacre](https://doi.org/10.1016/s0142-9612%2803%2900215-1) | ✓ |  | 取数 | 有机层厚 21–31 nm 的范围,见 nacre.json | `v1/shots/19-luodian/nacre.json:36` |
| Tan, Wong & Lee 2004 | [Iridescence of a shell of mollusk Haliotis Glabra](https://doi.org/10.1364/opex.12.004847) | ✓ |  | 取数 | 有机层 25±5 nm 的模型输入;抛光面 4.3 µm 细槽 | `v1/docs/shots/19-dianluo.md:71` |
| Tang & Zhang 2015 | Tang & Zhang 2015 | — |  | 取数 | 瓣边和中心片厚 499、371 nm,用于设生长纹幅度假设 | `v1/shots/19-luodian/pattern.py:31`<br>`v1/docs/shots/19-luodian.md:38` |
| Aoki & Iai 2019 | Aoki & Iai 2019 | — |  | 取数 | 漆的 n≈1.57,由 SCI−SCE 反推 | `v1/shots/19-luodian/scene.py:58`<br>`v1/docs/shots/19-dianluo.md:75` |
| Salman et al. 2021 | [Hyperspectral interference tomography of nacre](https://doi.org/10.1073/pnas.2023623118) | ✓ |  | 取数 | nacre.json 的片厚分布 σ 50 nm 和有机层模型值;TMM 是自写 | `v1/shots/19-luodian/pattern.py:10`<br>`v1/shots/19-luodian/nacre.json:2` |
| Lee et al. 2023 | [Relationship between Sensitivity Evaluation and Light Reflection Characteristics of Urushi (Asian Lacquer) Coatings with Black Roiro (Polished Black Color) Finish](https://doi.org/10.5057/jjske.tjske-d-23-00028) | ✓ |  | 取数 | 漆的 n≈1.53,由 SCI−SCE 反推 | `v1/shots/19-luodian/scene.py:58`<br>`v1/docs/shots/19-dianluo.md:75` |
| Carskaddan 2025 | [Nacre microstructure records spatiotemporal variation in temperature in the modern ocean](https://doi.org/10.3389/fmars.2025.1517327) | ✓ |  | 取数 | 皱纹盘鲍片厚中位数范围 360–460 nm | `v1/docs/shots/19-dianluo.md:48` |
| Finnemore et al. 2012 | [Biomimetic layer-by-layer assembly of artificial nacre](https://doi.org/10.1038/ncomms1970) | ✓ | 有 | 校验 | nacre_check 对其图 4 做趋势检验,不是拟合曲线 | `v1/shots/19-luodian/nacre_check.py:9`<br>`v1/docs/shots/19-luodian.md:34` |
| Fan et al. 2021 | [investigation of nacre nanostructure by analyzing its structural color pattern](https://doi.org/10.1038/s41598-021-99327-4) | ✓ | 有 | 校验 | 用其式 1 两层 Bragg 算峰位,与 TMM 趋势对比 | `v1/docs/shots/19-luodian.md:34` |
| Byrnes 2016 | [Multilayer optical calculations](https://arxiv.org/abs/1603.02720) | ✓ | 有 | 背景 | 调研里提到的 tmm 包;tools/tmm.py 和 nacre.py 是自写,没用它的代码 | `v1/docs/research/luodian.md:104`<br>`v1/docs/research/luodian.md:115` |
| Belcour et al. 2017 | [A practical extension to microfacet theory for the modeling of varying iridescence](https://doi.org/10.1145/3072959.3073620) | ✓ | 有 | 背景 |  | `v1/docs/research/luodian.md:121`<br>`v1/docs/research/luodian.md:123` |
| Ozaki et al. 2021 | [Structural colors of pearls](https://doi.org/10.1038/s41598-021-94737-w) | ✓ | 有 | 背景 |  | `v1/docs/research/luodian.md:96`<br>`v1/docs/research/luodian.md:116` |
| Hizukuri et al. 2025 | [Brilliant structural colors originating from reflection by nanogaps of nacreous layers in fossilized ammonite shells](https://doi.org/10.1038/s41598-025-21872-z) | ✓ | 有 | 背景 |  | `v1/docs/research/luodian.md:85`<br>`v1/docs/research/luodian.md:86` |
| Kang 2025 | [A Study on Real-time Rendering Techniques for Korean Traditional Nacre Material based on Unreal Engine Substrate](https://doi.org/10.9728/dcs.2025.26.6.1699) | ✓ |  | 背景 |  | `v1/docs/research/luodian.md:119` |

### 胭脂水

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Kreibig & von Fragstein 1969 | [The limitation of electron mean free path in small silver particles](https://doi.org/10.1007/bf01393059) | ✓ |  | 实现 | enamel.py 对金介电函数的粒径修正 | `v1/materials/yanzhi/enamel.py:85` |
| Kreibig & Vollmer 1995 | [Optical Properties of Metal Clusters](https://doi.org/10.1007/978-3-662-09109-8) | ✓ |  | 实现 | enamel.py 粒径修正的公式出处 | `v1/materials/yanzhi/enamel.py:85` |
| Johnson & Christy 1972 | [Optical Constants of the Noble Metals](https://doi.org/10.1103/physrevb.6.4370) | ✓ |  | 取数 | 金 n,k 表,作为 McPeak 的对照 | `v1/materials/yanzhi/enamel.py:4`<br>`v1/materials/yanzhi/material.json:4` |
| Kingery & Vandiver 1986 | Kingery & Vandiver 1986 | — |  | 取数 | 粉彩透明粉红的金粒 20–60 nm,转引,原图没见到 | `v1/materials/yanzhi/material.json:63`<br>`v1/docs/materials/yanzhi.md:21` |
| Barber & Freestone 1990 | [AN INVESTIGATION OF THE ORIGIN OF THE COLOUR OF THE LYCURGUS CUP BY ANALYTICAL TRANSMISSION ELECTRON MICROSCOPY](https://doi.org/10.1111/j.1475-4754.1990.tb01079.x) | ✓ |  | 取数 | 转引 Kingery & Vandiver 的金粒尺寸的来源 | `v1/materials/yanzhi/material.json:63`<br>`v1/docs/materials/yanzhi.md:21` |
| Sugiyama, Horiuchi & Osaki 1996 | [Measurement of Translucency of Porcelain Bodies](https://doi.org/10.2109/jcersj.104.877) | ✓ |  | 取数 | 瓷胎 1 mm 透光 10–27%,推胎的传输长度 | `v1/materials/qinghua/material.json:97` |
| Berciaud et al. 2005 | [Observation of Intrinsic Size Effects in the Optical Response of Individual Gold Nanoparticles](https://doi.org/10.1021/nl050062t) | ✓ | 有 | 取数 | Kreibig 尺寸修正 A 0.25 和 v_F | `v1/materials/yanzhi/material.json:4`<br>`v1/docs/materials/yanzhi.md:32` |
| Mehdikhani & Borhani 2013 | [Optical spectroscopy of sodium silicate glasses prepared with nano- and micro-sized iron oxide particles](https://doi.org/10.2298/pac1303117m) | ✓ |  | 取数 | Fe³⁺ 紫区吸收带的形状,伴生吸收的替身用 | `v1/materials/qinghua/optics.py:70`<br>`v1/materials/qinghua/material.json:200` |
| McPeak et al. 2015 | [Plasmonic Films Can Easily Be Better: Rules and Recipes](https://doi.org/10.1021/ph5004237) | ✓ |  | 取数 | 金的 n,k 表;对金红玻璃比 Johnson & Christy 贴合 | `v1/materials/yanzhi/enamel.py:4`<br>`v1/materials/yanzhi/material.json:4` |
| Ceglia et al. 2015 | [Iron speciation in soda-lime-silica glass: a comparison of XANES and UV-vis-NIR spectroscopy](https://doi.org/10.1039/c5ja00046g) | ✓ |  | 取数 | Fe²⁺ 峰位和 1100 nm 摩尔吸收 27.5,用于排除铁 | `v1/materials/qinghua/optics.py:68`<br>`v1/materials/qinghua/material.json:200` |
| Takebe et al. 2021 | [Fabrication of gold ruby glasses using solar panel glass cullet](https://doi.org/10.2109/jcersj2.21087) | ✓ | 有 | 校验 | validate.py 对其实测金红玻璃吸收谱检验 κ(λ) | `v1/materials/yanzhi/digitize.py:1`<br>`v1/materials/yanzhi/lightfit/diag.py:11` |
| Palomar 2025 | [Non-Destructive Ellipsometric Analysis of the Refractive Index of Historical Enamels](https://doi.org/10.3390/ma18051137) | ✓ | 有 | 校验 | 复原珐琅椭偏 n 1.604±0.006,对照 Appen 算出的 1.59 | `v1/materials/yanzhi/material.json:31`<br>`v1/docs/materials/yanzhi.md:64` |

### 钧窑

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Hendy 2002 | [Light Scattering in Transparent Glass Ceramics](https://arxiv.org/abs/cond-mat/0207591) | ✓ |  | 背景 |  | `v1/docs/research/jun.md:183` |
| Hendy 2002 | [Light scattering in transparent glass ceramics](https://doi.org/10.1063/1.1499989) | ✓ |  | 背景 |  | `v1/docs/research/jun.md:194`<br>`v1/docs/research/jun.md:195` |
| Shi et al. 2018 | [Amorphous photonic crystals and structural colors in the phase separation glaze](https://doi.org/10.1016/j.jeurceramsoc.2017.10.036) | ✓ | 有 | 背景 |  | `v1/docs/research/jun.md:83`<br>`v1/docs/research/jun.md:88` |
| Hou et al. 2018 | [Jun ware glazes: Chemistry, nanostructure and optical properties](https://doi.org/10.1016/j.jeurceramsoc.2018.05.010) | ✓ | 有 | 背景 |  | `v1/docs/research/jun.md:3`<br>`v1/docs/research/jun.md:9` |
| Yuan et al. 2022 | [Jun ware glaze colours: An X-ray absorption spectroscopy study](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016) | ✓ | 有 | 背景 |  | `v1/docs/research/jun.md:67`<br>`v1/docs/research/jun.md:73` |
| Yuan et al. 2024 | [Changsha ware glaze color: Composition, nanostructure, and copper and iron speciation](https://doi.org/10.1111/jace.20025) | ✓ | 有 | 背景 |  | `v1/docs/research/jun.md:82`<br>`v1/docs/research/jun.md:214` |
| Wang 等 2024 | [Wang 等 2024](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005) | ◐ | 有 | 背景 |  | `v1/docs/research/jun.md:67`<br>`v1/docs/research/jun.md:106` |
| Shi et al. 2025 | [Composition and microstructure of Yuan Dynasty Jun glazed stoneware from Yanjialiang site, Inner Mongolia, China](https://doi.org/10.1038/s40494-025-01711-0) | ✓ | 有 | 背景 |  | `v1/docs/research/jun.md:84`<br>`v1/docs/research/jun.md:86` |

### 金属和鎏金

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Ribbing & Roos 1991 (Palik II) | [Copper Oxides (Cu2O, CuO)](https://doi.org/10.1016/b978-012544415-6.50085-6) | ✓ |  | 取数 | Cu₂O 的 n,k,取公开转录;手册表格不进 git | `v1/materials/gilt_copper/material.json:178` |
| Chang et al. 2017 | [Analysis of Historic Copper Patinas. Influence of Inclusions on Patina Uniformity](https://doi.org/10.3390/ma10030298) | ✓ |  | 取数 | 历史屋面腐蚀膜 1–10 µm 的范围 | `v1/materials/gilt_copper/material.json:172` |
| Leygraf et al. 2019 | [The origin and evolution of copper patina colour](https://doi.org/10.1016/j.corsci.2019.05.025) | ✓ |  | 取数 | 约 0.8 µm 已棕黑的范围记录 | `v1/materials/gilt_copper/material.json:172`<br>`v1/docs/materials/gilt_copper.md:79` |
| Joshi et al. 2022 | [Comparative Study of Fire-Gilded and Electroplated Gold Films on Copper Substrates](https://doi.org/10.3126/jnphyssoc.v8i3.50717) | ✓ |  | 取数 | 现代火镀金层厚约 2 µm 和成分,光学没用 | `v1/materials/gilt_copper/material.json:33`<br>`v1/docs/materials/gilt_copper.md:41` |
| Margreiter et al. 2022 | [Investigations on fire‐gilding](https://doi.org/10.1111/arcm.12797) | ✓ |  | 取数 | 鎏金含汞量范围,光学没用 | `v1/materials/gilt_copper/material.json:43`<br>`v1/docs/materials/gilt_copper.md:42` |
| Kosec et al. 2024 | [The impact of urban rain on the changes of bare and artificially patinated bronze during 9-year exposure](https://doi.org/10.1007/s11356-024-33369-9) | ✓ |  | 取数 | 铜腐蚀膜厚 5–10 µm 的范围,演示帧用的是假设值 | `v1/materials/gilt_copper/material.json:172` |
| Ma et al. 2025 | [Microstructural characteristics and formation of the gilded artifacts excavated from Han Tomb situated in Qufu, Shandong, China](https://doi.org/10.1038/s40494-025-01657-3) | ✓ |  | 取数 | 汉代鎏金层厚和含汞量范围,只记范围,不进光学 | `v1/materials/gilt_copper/material.json:33` |

### 漆

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Oyabu et al. 1987 | [Effects of Curing Condition on Transparency of Urushi Films](https://doi.org/10.4011/shikizai1937.60.94) | ✓ |  | 取数 | 透明漆吸收谱 a漆,进朱漆的 K/S | `v1/materials/cinnabar_lacquer/material.json:254`<br>`v1/docs/materials/cinnabar_lacquer.md:23` |
| Reichert et al. 2025 | [Database of diffuse reflectance infrared Fourier transform spectroscopy (DRIFTS) and hyperspectral imaging (HSI) spectra of pigments and dyes for historical document analysis](https://doi.org/10.1007/s00216-025-05948-3) | ✓ |  | 取数 | 朱砂反射谱,derive.py 读补充数据后减黑 | `v1/materials/cinnabar_lacquer/derive.py:2`<br>`v1/materials/cinnabar_lacquer/material.json:59` |
| Hou et al. 2025 | [The Effects of Repeated Kurome Treatment on Chinese Lacquer and Its Film Properties](https://doi.org/10.3390/polym17111481) | ✓ |  | 取数 | 朱漆光泽 90 GU,gloss.py 反推 α 0.0054 | `v1/materials/cinnabar_lacquer/material.json:31`<br>`v1/docs/materials/cinnabar_lacquer.md:35` |
| Reichert et al. 2025 | [Supplementary Information - Database of diffuse reflectance infrared Fourier transform spectroscopy (DRIFTS) and hyperspectral imaging (HSI) spectra of pigments and dyes for historical document analysis. Anal Bioanal Chem (2025). https://doi.org/10.1007/s00216-025-05948-3Preprint: Database of pigments and dyes in historical manuscripts using Diffuse Reflectance Infrared Fourier Transform Spectroscopy (DRIFTS) and Hyperspectral Imaging (HSI)](https://doi.org/10.6084/m9.figshare.28639103) | ✓ |  | 取数 | 朱砂反射谱的补充数据文件,derive.py 读取 | `v1/materials/cinnabar_lacquer/derive.py:2`<br>`v1/materials/cinnabar_lacquer/material.json:59` |
| Han et al. 2023 | [Surface appearance and morphology changes of Asian lacquer due to artificial aging: Impacts of traditional additives](https://doi.org/10.1016/j.culher.2023.08.010) | ✓ |  | 背景 | weathering 引其摘要作定性依据,skin_alpha 是拟合值,没有取它的数 | `v1/crafts/duanwen/duanwen.py:2`<br>`v1/crafts/weathering/weathering.py:3` |
| Liu et al. 2025 | [The Influence of Natural Light Aging on the Surface Properties of Colored Chinese Lacquer Coatings](https://doi.org/10.3390/coatings15101229) | ✓ |  | 背景 | 材质卡记了现代实验的颜料比 10 wt% 作旁证,不是模型参数 | `v1/materials/cinnabar_lacquer/material.json:82` |

### 青花

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Chen, Guo & Zhang 1978 | Chen, Guo & Zhang 1978 | — |  | 取数 | 清青花 MnO/CoO 5–7、Fe₂O₃/CoO 0.4–1 | `v1/materials/qinghua/optics.py:63`<br>`v1/materials/qinghua/material.json:196` |
| Miao & Yu 1996 | Miao & Yu 1996 | — |  | 取数 | 景德镇釉厚 0.2–0.5 mm(引述) | `v1/materials/qinghua/material.json:64` |
| Thiemsorn et al. 2007 | [Effects of Glass Structure on the Optical Absorption of Transition Ions in Industrial Soda-Lime-Silica Glasses](https://doi.org/10.1299/jmmp.1.508) | ✓ | 有 | 取数 | 钠钙玻璃 Co5 吸收谱,矢量读图得 κ(λ),595 nm 为 0.588 per g/m² | `v1/materials/qinghua/digitize.py:6`<br>`v1/materials/qinghua/optics.py:50` |
| Sun et al. 2026 | [Effect of Luanbai Glaze on the Coloration of Cobalt Pigment in Yuan Dynasty Jingdezhen Porcelains: An Experimental Study](https://doi.org/10.3390/ma19112254) | ✓ |  | 取数 | 元青花釉成分和 OCT 釉厚 0.18–0.22 mm | `v1/materials/qinghua/material.json:54` |
| Hsieh et al. 2023 | [The atypical hues of the Santa Cruz blue-and-white cargo: non-invasive analysis of glaze defects and color variations in mid-Ming porcelain](https://doi.org/10.1186/s40494-023-00953-0) | ✓ | 有 | 校验 | check_spectrum 对其 FORS 谱做弱检验 | `v1/materials/qinghua/digitize.py:14`<br>`v1/tests/qinghua/check_spectrum.py:1` |

### 豇豆红

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| 10.7538/yzk.2011.45.11.1399 | [10.7538/yzk.2011.45.11.1399](https://doi.org/10.7538/yzk.2011.45.11.1399) | ◐ |  | 背景 |  | `v1/docs/research/jiangdouhong.md:155` |
| Cuvelier et al. 2011 | [Copper red glazes: a coating with two families of particles](https://doi.org/10.1007/s00339-011-6707-3) | ✓ |  | 背景 |  | `v1/docs/research/jiangdouhong.md:7`<br>`v1/docs/research/jiangdouhong.md:82` |
| Cuvelier et al. 2013 | [Copper red glazes: a coating with two families of particles](https://arxiv.org/abs/1302.2302) | ✓ |  | 背景 |  | `v1/docs/research/jiangdouhong.md:74`<br>`v1/docs/research/jiangdouhong.md:83` |
| Li et al. 2022 | [The computational simulation of the reflection spectra of copper red glaze](https://arxiv.org/abs/2208.08043) | ✓ |  | 背景 |  | `v1/docs/research/jiangdouhong.md:101`<br>`v1/docs/research/jiangdouhong.md:122` |
| Li et al. 2022 | [The computational simulation of the reflection spectra of copper red glaze](https://doi.org/10.1063/5.0095570) | ✓ |  | 背景 |  | `v1/docs/research/jiangdouhong.md:122`<br>`v1/docs/research/jiangdouhong.md:169` |

### 点翠和孔雀

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Freyer et al. 2020 | [Biophotonics of diversely coloured peacock tail feathers](https://doi.org/10.1039/d0fd00033g) | ✓ | 有 | 实现 | barbule.py 按其有效介质多层模型算羽小枝反射,参数取其六色区 | `v1/shots/17-peacock/barbule.py:1`<br>`v1/shots/17-peacock/scene.py:12` |
| Yoshioka & Kinoshita 2002 | [Effect of Macroscopic Structure in Iridescent Color of the Peacock Feathers](https://forma.katachi-jp.com/abstract/1702/17020169.html) | ○ |  | 取数 | 羽小枝多层倾角分布 θ0 15° | `v1/shots/17-peacock/scene.py:19`<br>`v1/shots/17-peacock/barbule.json:7` |
| Leertouwer et al. 2011 | [Refractive index and dispersion of butterfly chitin and bird keratin measured by polarizing interference microscopy](https://doi.org/10.1364/oe.19.024061) | ✓ | 有 | 取数 | 角蛋白色散,经 Freyer 转引 | `v1/shots/17-peacock/barbule.json:5` |
| Stavenga et al. 2015 | [High refractive index of melanin in shiny occipital feathers of a bird of paradise](https://doi.org/10.1038/lsa.2015.16) | ✓ | 有 | 取数 | 黑色素 n,k,经 Freyer 转引 | `v1/shots/17-peacock/barbule.json:5` |

### 其他

| 引用 | 文献 | 链接 | 全文 | 关系 | 说明 | 位置 |
|---|---|---|---|---|---|---|
| Saunderson | [Calculation of the Color of Pigmented Plastics*](https://doi.org/10.1364/josa.32.000727) | ✓ |  | 实现 | 清漆层和果皮界面的修正,年份文件里没写 | `v1/materials/cinnabar_lacquer/derive.py:15`<br>`v1/materials/cinnabar_lacquer/material.json:11` |
| Schwartz & Weidner 1995 | [Modeling of coating flows on curved surfaces](https://doi.org/10.1007/bf00046385) | ✓ |  | 实现 | crafts/glazeflow/flow.py 的曲面润滑方程;TODO 记检查没过,没用上 | `v1/crafts/glazeflow/flow.py:9` |
| Sharma, Wu & Dalal 2005 | [The CIEDE2000 color-difference formula: Implementation notes, supplementary test data, and mathematical observations](https://doi.org/10.1002/col.20070) | ✓ |  | 实现 | 胭脂水材质卡按它算 CIEDE2000 | `v1/materials/yanzhi/card.py:255`<br>`v1/materials/yanzhi/lightfit/diag.py:30` |
| Claff, Photons to Photos | [Photons to Photos(Bill Claff 的传感器数据,不是论文)](https://www.photonstophotos.net/) | ○ |  | 取数 | 5D IV 满阱 67871 e⁻、ISO 100 读出 11.5 e⁻ | `v1/tools/sensors/canon_eos_5d_mkiv.json:54`<br>`v1/DESIGN.md:289` |
| Kortüm 1969 | [Reflectance Spectroscopy](https://doi.org/10.1007/978-3-642-88071-1) | ✓ |  | 取数 | KM 里 K 对吸收系数的比 2.0 | `v1/docs/materials/cinnabar_lacquer.md:42` |
| Jin Yueping 2020 | Jin Yueping 2020 | — |  | 取数 | 故宫文物摄影的灯位,museum_flat 灯组照它布 | `v1/optics/rigs/museum_flat.json:4` |
| Shaw et al. 2023 | Shaw et al. 2023 | — |  | 取数 | 剔红切口露出深色标记层的说法,决定朱漆卡加黑层 | `v1/materials/cinnabar_lacquer/card.py:85` |

## 调研报告里出现的全部文献

调研报告引用的。**几乎都只是被提到**,引用没有逐条核对,大多数和代码无关。按题目分组,报告在 `research/`。「⬛」表示手上有全文。

<details><summary><code>carved-lacquer</code>(9 条)</summary>

- ✓ [Effects of Curing Condition on Transparency of Urushi Films](https://doi.org/10.4011/shikizai1937.60.94)  OYABU 等,1987,Journal of the Japan Society of Colour Material
- ✓ [Prepolymerization of Lacquer Sap under Pure Oxygen Atmosphere and Its Effects on the Properties of Lacquer Film](https://doi.org/10.1155/2015/517202)  Yang 等,2015,International Journal of Polymer Science
- ✓ [Biobased Polymer Coating Using Catechol Derivative Urushiol](https://doi.org/10.1021/acs.langmuir.6b00484)  Watanabe 等,2016,Langmuir
- ✓ [The technical investigation of an eighteenth-century Chinese imperial carved lacquer screen and its role in developing an appropriate conservation treatment](https://doi.org/10.1080/00393630.2016.1227117)  Pitthard 等,2016,Studies in Conservation
- ✓ [Analytical investigation into materials and technique: Carved lacquer decorated panel from Fuwangge in the Forbidden City of Qianlong Period, Qing Dynasty](https://doi.org/10.1016/j.jasrep.2017.12.023)  Wang 等,2018,Journal of Archaeological Science: Reports
- ✓ [Use of THM-PY-GC/MS technique to characterize complex, multilayered Chinese lacquer](https://doi.org/10.1016/j.jaap.2019.04.011)  Hao 等,2019,Journal of Analytical and Applied Pyrolysis
- ✓ [The Influence of Natural Light Aging on the Surface Properties of Colored Chinese Lacquer Coatings](https://doi.org/10.3390/coatings15101229)  Liu 等,2025,Coatings
- ✓ [Preparation and Properties of Composite Coatings Fabricated from Carved Lacquer Waste and Waterborne Acrylic Resin](https://doi.org/10.3390/coatings15101230)  Du 等,2025,Coatings
- ✓ [Multi-Analytical Characterization of the Materials and Manufacturing Technology of a Southern Song Dynasty Tixi Lacquer Plate from the Nanhai No. 1 Shipwreck](https://doi.org/10.3390/coatings16091034)  Zhang 等,2026,Coatings

</details>

<details><summary><code>chengni</code>(4 条)</summary>

- ✓ [Spectral Library of Impervious Urban Materials](https://doi.org/10.5281/zenodo.4263842)  Kotthaus 等,2013,Zenodo
- ✓ ⬛ [Derivation of an urban materials spectral library through emittance and reflectance spectroscopy](https://doi.org/10.1016/j.isprsjprs.2014.05.005)  Kotthaus 等,2014,ISPRS Journal of Photogrammetry and Remote Sensing
- ✓ [Reading ceramic surfaces: Characterisation of surface treatments towards functional identification of vases](https://doi.org/10.1016/j.jasrep.2021.103021)  Rueff 等,2021,Journal of Archaeological Science: Reports
- ✓ ⬛ [Enhancement of Surface Characteristics of Sculpting Clay Ceramics Using Mechanical Polishing](https://doi.org/10.7736/jkspe.026.00056)  Hur 等,2026,Journal of the Korean Society for Precision Engineering

</details>

<details><summary><code>crackle-s3b</code>(14 条)</summary>

- ✓ [Development and geometry of isotropic and directional shrinkage crack patterns](https://arxiv.org/abs/patt-sol/9911003)  Shorlin 等,1999,arXiv
- ✓ [Development and geometry of isotropic and directional shrinkage-crack patterns](https://doi.org/10.1103/physreve.61.6950)  Shorlin 等,2000,Physical Review E
- ✓ [Hierarchical crack pattern as formed by successive domain divisions.](https://doi.org/10.1103/physreve.71.046214)  Bohn 等,2005,Physical Review E
- ✓ [Evolution of mud-crack patterns during repeated drying cycles](https://doi.org/10.1039/b922206e)  Goehring 等,2010,Soft Matter
- ✓ [Using optical coherence tomography to characterize thick-glaze structure: Chinese Southern Song Guan glaze case study](https://doi.org/10.1179/2047058411y.0000000007)  Yang 等,2012,Studies in Conservation
- ✓ ⬛ [Using Optical Coherence Tomography to Characterize the Crack Morphology of Ceramic Glaze and Jade](https://doi.org/10.5772/31213)  Yang 等,2012,Selected Topics in Optical Coherence Tomography
- ✓ [Crack patterns morphology of ancient Chinese wares](https://doi.org/10.11588/opa.2013.1.11773)  Lahlil, Sophia 等,2013,The Old Potter's Almanack
- ✓ [Stress modulation in desiccating crack networks for producing effective templates for patterning metal network based transparent conductors](https://doi.org/10.1063/1.4991534)  Kumar 等,2017,Applied Physics Letters
- ✓ [Morphometric analysis of polygonal cracking patterns in desiccated starch slurries](https://doi.org/10.1103/physreve.96.023003)  Akiba 等,2017,Physical Review E
- ✓ [Morphometric analysis of polygonal cracking patterns in desiccated starch slurries](https://arxiv.org/abs/1707.07768)  Akiba 等,2017,arXiv
- ✓ [Universal Scaling of Polygonal Desiccation Crack Patterns](https://arxiv.org/abs/1807.06126)  Ma 等,2018,arXiv
- ✓ [Universal scaling of polygonal desiccation crack patterns](https://doi.org/10.1103/physreve.99.012802)  Ma 等,2019,Physical Review E
- ✓ [Craquelure as a Graph: Application of Image Processing and Graph Neural Networks to the Description of Fracture Patterns](https://arxiv.org/abs/1905.05010)  Sidorov 等,2019,arXiv
- ✓ [Scalable Crackle‐Lithography for Multifunctional Enclosed Plastic Nanofluidic Devices](https://doi.org/10.1002/advs.76980)  Dumpala 等,2026,Advanced Science

</details>

<details><summary><code>dianluo</code>(5 条)</summary>

- ✓ [Iridescence of a shell of mollusk Haliotis Glabra](https://doi.org/10.1364/opex.12.004847)  Tan 等,2004,Optics Express
- ✓ [Nacre tablet thickness records formation temperature in modern and fossil shells](https://doi.org/10.1016/j.epsl.2016.11.012)  Gilbert 等,2017,Earth and Planetary Science Letters
- ✓ [Twinning and homoepitaxy cooperation in the already rich growth morphology of CaCO3 polymorphs. I. Aragonite](https://doi.org/10.1107/s1600576723008208)  Aquilano 等,2023,Journal of Applied Crystallography
- ✓ [Relationship between Sensitivity Evaluation and Light Reflection Characteristics of Urushi (Asian Lacquer) Coatings with Black Roiro (Polished Black Color) Finish](https://doi.org/10.5057/jjske.tjske-d-23-00028)  LEE 等,2023,Transactions of Japan Society of Kansei Engineering
- ✓ [Nacre microstructure records spatiotemporal variation in temperature in the modern ocean](https://doi.org/10.3389/fmars.2025.1517327)  Carskaddan 等,2025,Frontiers in Marine Science

</details>

<details><summary><code>falang</code>(5 条)</summary>

- ✓ [Natural and Synthetic Indigo Color in Silk and Cotton Cloth](https://doi.org/10.2115/fiber.62.1)  Kawahito,2006,Sen'i Gakkaishi
- ✓ [Authenticity screening of stained glass windows using optical spectroscopy](https://doi.org/10.1038/srep37726)  Meulebroeck 等,2016,Scientific Reports
- ✓ [A fast non-invasive method for preliminary authentication of mediaeval glass enamels using UV–visible–NIR diffuse reflectance spectrophotometry](https://doi.org/10.1016/j.culher.2020.05.003)  Aceto 等,2020,Journal of Cultural Heritage
- ✓ [The Technology Transfer from Europe to China in the 17th–18th Centuries: Non-Invasive On-Site XRF and Raman Analyses of Chinese Qing Dynasty Enameled Masterpieces Made Using European Ingredients/Recipes](https://doi.org/10.3390/ma14237434)  Colomban 等,2021,Materials
- ✓ [Study of modern Chinese cloisonné by means of small-spot energy dispersive X-ray fluorescence spectrometry and Raman spectroscopy](https://doi.org/10.1016/j.sab.2022.106594)  Queralt 等,2023,Spectrochimica Acta Part B: Atomic Spectroscopy

</details>

<details><summary><code>fiber</code>(9 条)</summary>

- ◐ [10.12477/xdfzjs.20240507](https://doi.org/10.12477/xdfzjs.20240507)
- — [10.3724/sp.j.1089.2018.16471](https://doi.org/10.3724/sp.j.1089.2018.16471)
- ✓ [Specular reflection from woven cloth](https://doi.org/10.1145/2077341.2077352)  Irawan 等,2012,ACM Transactions on Graphics
- ✓ [A practical microcylinder appearance model for cloth rendering](https://doi.org/10.1145/2451236.2451240)  Sadeghi 等,2013,ACM Transactions on Graphics
- ✓ [Paint with stitches: a style definition and image-based rendering method for random-needle embroidery](https://doi.org/10.1007/s11042-017-4882-8)  Yang 等,2017,Multimedia Tools and Applications
- ✓ [Fiber‐Level On‐the‐Fly Procedural Textiles](https://doi.org/10.1111/cgf.13230)  Luan 等,2017,Computer Graphics Forum
- ✓ [Computer Aided DIY Design of Stylized Generation of Random Needle Embroidery](https://doi.org/10.3724/sp.j.1089.2022.18962)  Zhu 等,2022,Journal of Computer-Aided Design & Computer Graphics
- ✓ [Neural inverse procedural modeling of knitting yarns from images](https://doi.org/10.1016/j.cag.2023.12.013)  Trunz 等,2024,Computers & Graphics
- ✓ [A Multi-scale Yarn Appearance Model with Fiber Details](https://arxiv.org/abs/2401.12724)  Khattar 等,2024,arXiv

</details>

<details><summary><code>guan-aging</code>(15 条)</summary>

- ◐ [10.13543/j.bhxbzr.2025.05.014](https://doi.org/10.13543/j.bhxbzr.2025.05.014)
- ◐ ⬛ [10.13957/j.cnki.tcxb.2021.06.022](https://doi.org/10.13957/j.cnki.tcxb.2021.06.022)
- ✓ ⬛ [Technical Studies and Replication of Guan Ware, an Ancient Chinese Ceramic](https://doi.org/10.1557/mrs2001.16)  Jiazhi 等,2001,MRS Bulletin
- ✓ [Silicate Glass Alteration Enhanced by Iron: Origin and Long-Term Implications](https://doi.org/10.1021/es304057y)  Michelin 等,2012,Environmental Science & Technology
- ✓ [Influence of manufacturing parameters on the crackling process of ancient Chinese glazed ceramics](https://doi.org/10.1016/j.culher.2014.10.003)  Lahlil 等,2015,Journal of Cultural Heritage
- ✓ [Corrosion of Longquan celadons in the marine environment: study on the celadons from the Dalian Island shipwreck of the Yuan Dynasty](https://doi.org/10.1186/s40494-021-00583-4)  He 等,2021,Heritage Science
- ✓ [The Polyhedral and Elusive Nature of Geyao](https://doi.org/10.30687/annor/2385-3042/2021/01/022)  Rastelli,2021,Annali di Ca’ Foscari. Serie orientale
- ✓ [Insights into the Residue Trapped in Glaze Cracks of Archaeological Ceramics Using Microchemical Analysis](https://doi.org/10.1017/s1431927622012375)  Li 等,2022,Microscopy and Microanalysis
- ✓ [Research on the degradation of ancient Longquan celadons in the Dalian Island shipwreck](https://doi.org/10.1038/s41529-022-00217-5)  He 等,2022,npj Materials Degradation
- ✓ [Corrosion Research on Ru Porcelain Glazes Excavated at Qingliangsi, Baofeng, China](https://doi.org/10.3390/coatings13061011)  Zhou 等,2023,Coatings
- ✓ [Laboratory and synchrotron x‐ray micro–computed tomography to shed light on degradation features of corroded Roman glass](https://doi.org/10.1111/jace.20241)  Zanini 等,2024,Journal of the American Ceramic Society
- ✓ [Corrosion mechanisms of a bluish-white porcelain of Hutian kiln excavated from Nanhai No. 1 shipwreck](https://doi.org/10.1038/s40494-025-01945-y)  Wang 等,2025,npj Heritage Science
- ✓ [Insights into long term glass corrosion mechanisms from the Ballidon experiment](https://doi.org/10.1038/s41529-025-00571-0)  Thorpe 等,2025,npj Materials Degradation
- ✓ [Does Water Cleaning Mitigate Atmospheric Degradation of Unstable Heritage Glass? An Experimental Study on Glass Models](https://doi.org/10.3390/heritage8070276)  Law 等,2025,Heritage
- ✓ [The mechanisms of color, opacifying, and cracks in celadon glazes from the Southern Song Guan Kiln](https://doi.org/10.1038/s40494-026-02383-0)  Ren 等,2026,npj Heritage Science

</details>

<details><summary><code>huanghuali</code>(11 条)</summary>

- ◐ [10.11833/j.issn.2095-0756.2015.04.005](https://doi.org/10.11833/j.issn.2095-0756.2015.04.005)
- ◐ [10.15886/j.cnki.hdxbzkb.2018.0018](https://doi.org/10.15886/j.cnki.hdxbzkb.2018.0018)
- ✓ [Effect of growth on wood traits in seed-raised plantations of Dalbergia sissoo Roxb.](https://doi.org/10.1007/s11676-014-0002-z)  Pande 等,2015,Journal of Forestry Research
- ✓ ⬛ [Procedural wood textures](https://arxiv.org/abs/1511.04224)  Liu 等,2015,arXiv
- ✓ ⬛ [Procedural texturing of solid wood with knots](https://doi.org/10.1145/3528223.3530081)  Larsson 等,2022,ACM Transactions on Graphics
- ✓ ⬛ [Colour and Surface Chemistry Changes of Wood Surfaces Coated with Two Types of Waxes after Seven Years Exposure to Natural Light in Indoor Conditions](https://doi.org/10.3390/coatings12111689)  Liu 等,2022,Coatings
- ✓ ⬛ [Correlation between Colour Traits and Intrinsic Quality of Dalbergiae Odoriferae Lignum](https://doi.org/10.3390/molecules28227635)  He 等,2023,Molecules
- ✓ ⬛ [Chromophores’ Contribution to Color Changes of Thermally Modified Tropical Wood Species](https://doi.org/10.3390/polym15194000)  Jurczyková 等,2023,Polymers
- ✓ [Automatic inference of a anatomically meaningful solid wood texture from a single photograph](https://arxiv.org/abs/2302.01820)  Nindel 等,2023,arXiv
- ✓ ⬛ [Visible/near-infrared hyperspectral imaging combined with machine learning for identification of ten Dalbergia species](https://doi.org/10.3389/fpls.2024.1413215)  Chen 等,2024,Frontiers in Plant Science
- ✓ ⬛ [Study on the Surface Properties of Hot-Waxed Wood with MCC Filled Fischer-Tropsch Synthetic Wax](https://doi.org/10.3390/f15122262)  Zhang 等,2024,Forests

</details>

<details><summary><code>ink-xuan</code>(27 条)</summary>

- ◐ [10.3969/j.issn.0253-2417.2023.03.008](https://doi.org/10.3969/j.issn.0253-2417.2023.03.008)
- ✓ [Some Notes on Sand Filtration](https://doi.org/10.1002/j.1551-8833.1937.tb14014.x)  Iwasaki,1937,Journal AWWA
- ✓ ⬛ [Why some things are darker when wet](https://doi.org/10.1364/ao.27.001278)  Lekner 等,1988,Applied Optics
- ✓ [Modeling in Computer Graphics](https://doi.org/10.1007/978-4-431-68147-2)  1991
- ✓ [Simulating oriental black-ink painting](https://doi.org/10.1109/38.761553)  Lee,1999,IEEE Computer Graphics and Applications
- ✓ [Rendering of Wet Materials](https://doi.org/10.2312/egwr/egwr99/273-282)  Jensen 等,1999,The Eurographics Association
- ✓ [Diffusion rendering of black ink paintings using new paper and ink models](https://doi.org/10.1016/s0097-8493%2800%2900132-1)  Lee,2001,Computers & Graphics
- ✓ [Characterization of Chinese ink in size and surface](https://doi.org/10.1016/s1296-2074%2803%2900044-x)  Swider 等,2003,Journal of Cultural Heritage
- ✓ [Characteristic Mechanical Properties of Washi Papers](https://doi.org/10.2524/jtappij.59.1546)  Yamauchi 等,2005,JAPAN TAPPI JOURNAL
- ✓ ⬛ [Light Absorption by Carbonaceous Particles: An Investigative Review](https://doi.org/10.1080/02786820500421521)  Bond 等,2006,Aerosol Science and Technology
- ✓ ⬛ [PRESSURE BASED INK DIFFUSION MODEL FOR REAL-TIME SIMULATION OF CHINESE CALLIGRAPHY](https://doi.org/10.5220/0002071902710276)  2007,Proceedings of the Second International Conference on Computer Graphics Theory and Applications
- ✓ [IR2s](https://doi.org/10.1145/1809939.1809947)  Xie 等,2010,Proceedings of the 8th International Symposium on Non-Photorealistic Animation and Rendering - NPAR 10
- ✓ [Contour-driven Sumi-e rendering of real photos](https://doi.org/10.1016/j.cag.2010.11.017)  Ning 等,2011,Computers & Graphics
- ✓ ⬛ [Ink Dispersion on Qianlong Xuan Paper with Improved Ink Expression](https://doi.org/10.1016/j.jmst.2015.12.014)  Wu 等,2016,Journal of Materials Science & Technology
- ✓ ⬛ [Influence of Geometry and Surrounding Conditions on Fluid Flow in Paper-Based Devices](https://doi.org/10.3390/mi7050073)  Walji 等,2016,Micromachines
- ✓ [Web-based SBLR method of multimedia tools for computer-aided drawing](https://doi.org/10.1007/s11042-018-5949-x)  Xie 等,2018,Multimedia Tools and Applications
- ✓ ⬛ [Paper Stacks for Uniform Rehydration of Dried Reagents in Paper Microfluidic Devices](https://doi.org/10.1038/s41598-019-52202-9)  Das 等,2019,Scientific Reports
- ✓ [A new kind of nanocomposite Xuan paper comprising ultralong hydroxyapatite nanowires and cellulose fibers with a unique ink wetting performance](https://doi.org/10.1039/c9ra08349a)  Shao 等,2019,RSC Advances
- ✓ [Liquid Wicking in a Paper Strip: An Experimental and Numerical Study](https://doi.org/10.1021/acsomega.0c02407)  Patari 等,2020,ACS Omega
- ✓ ⬛ [Disposable Paper-on-CMOS Platform for Real-Time Simultaneous Detection of Metabolites](https://doi.org/10.1109/tbme.2019.2962239)  Hu 等,2020,IEEE Transactions on Biomedical Engineering
- ✓ [Chinese ink-facilitated fabrication of paper-based composites as electrodes for supercapacitors](https://doi.org/10.1080/19475411.2021.1959463)  Yan 等,2021,International Journal of Smart and Nano Materials
- ✓ ⬛ [Reproducing ancient Chinese ink depending on gelatin/chitosan and modern experimental methodology](https://doi.org/10.1186/s40494-022-00739-w)  Liu 等,2022,Heritage Science
- ✓ [Fluorescent carbon nanoparticles from Chinese ink](https://doi.org/10.1360/ssc-2022-0085)  Zhu 等,2022,SCIENTIA SINICA Chimica
- ✓ ⬛ [Overview of methods to characterize the mass, size, and morphology of soot](https://doi.org/10.1016/j.jaerosci.2023.106211)  Sipkens 等,2023,Journal of Aerosol Science
- ✓ ⬛ [Increasing particle concentration enhances particle penetration depth but slows down liquid imbibition in thin fibrous filters](https://doi.org/10.1016/j.colsurfa.2024.133146)  Nicasy 等,2024,Colloids and Surfaces A: Physicochemical and Engineering Aspects
- ✓ ⬛ [Study of Ink stick unearthed from the tomb of Fan Xiaochong in Shaanxi Province](https://doi.org/10.1038/s40494-025-01976-5)  Qi 等,2025,npj Heritage Science
- ✓ ⬛ [Comparison of Aging Performances and Mechanisms: Super-Durable Fire-Resistant “Xuan Paper” Versus Chinese Traditional Xuan Paper](https://doi.org/10.3390/molecules30020263)  Dong 等,2025,Molecules

</details>

<details><summary><code>jiangdouhong</code>(6 条)</summary>

- ◐ [10.7538/yzk.2011.45.11.1399](https://doi.org/10.7538/yzk.2011.45.11.1399)
- ✓ [Copper red glazes: a coating with two families of particles](https://doi.org/10.1007/s00339-011-6707-3)  Cuvelier 等,2011,Applied Physics A
- ✓ [Copper red glazes: a coating with two families of particles](https://arxiv.org/abs/1302.2302)  Cuvelier 等,2013,arXiv
- ✓ [The computational simulation of the reflection spectra of copper red glaze](https://doi.org/10.1063/5.0095570)  Li 等,2022,AIP Advances
- ✓ [The computational simulation of the reflection spectra of copper red glaze](https://arxiv.org/abs/2208.08043)  Li 等,2022,arXiv
- ✓ [MICROSTRUCTURE-VALENCE-OPTICAL COUPLING COLOURATION MECHANISM OF LANG RED GLAZE UNDER CRYSTAL NUCLEI INDUCTION](https://doi.org/10.13168/cs.2025.0040)  Lai,2025,Ceramics - Silikaty

</details>

<details><summary><code>jun</code>(5 条)</summary>

- ◐ ⬛ [10.13957/j.cnki.tcxb.2024.02.005](https://doi.org/10.13957/j.cnki.tcxb.2024.02.005)
- ✓ [Light scattering in transparent glass ceramics](https://doi.org/10.1063/1.1499989)  Hendy,2002,Applied Physics Letters
- ✓ [Light Scattering in Transparent Glass Ceramics](https://arxiv.org/abs/cond-mat/0207591)  Hendy,2002,arXiv
- ✓ ⬛ [Changsha ware glaze color: Composition, nanostructure, and copper and iron speciation](https://doi.org/10.1111/jace.20025)  Yuan 等,2024,Journal of the American Ceramic Society
- ✓ ⬛ [Composition and microstructure of Yuan Dynasty Jun glazed stoneware from Yanjialiang site, Inner Mongolia, China](https://doi.org/10.1038/s40494-025-01711-0)  Shi 等,2025,npj Heritage Science

</details>

<details><summary><code>kingfisher_macro</code>(7 条)</summary>

- ◐ [10.22920/pnie.2021.2.1.21](https://doi.org/10.22920/pnie.2021.2.1.21)
- ✓ [Kingfisher feathers – colouration by pigments, spongy nanostructures and thin films](https://doi.org/10.1242/jeb.062620)  Stavenga 等,2011,Journal of Experimental Biology
- ✓ [Interspecific variation in the structural properties of flight feathers in birds indicates adaptation to flight requirements and habitat](https://doi.org/10.1111/1365-2435.12419)  Pap 等,2015,Functional Ecology
- ✓ [Data from: Interspecific variation in the structural properties of flight feathers in birds indicates adaptation to flight requirements and habitat](https://doi.org/10.5061/dryad.1538t)  Pap 等,2016,Dryad
- ✓ [Analytical investigation of the feather decoration technique of a seventeenth to eighteenth century Chinese imperial hanging screen](https://doi.org/10.1186/s40494-021-00555-8)  Gu 等,2021,Heritage Science
- ✓ [Elucidating and Biomimicking the Coloration Mechanisms Responsible for the Vibrant Blue Hues of the Common Kingfisher](https://doi.org/10.1002/adom.202402936)  Kang 等,2025,Advanced Optical Materials
- ✓ [Investigating Structurally and Pigmentary Colored Featherworks via Noninvasive Methodologies](https://doi.org/10.1021/acsomega.6c02770)  Meier 等,2026,ACS Omega

</details>

<details><summary><code>luodian</code>(9 条)</summary>

- ✓ [Structural and mechanical properties of the organic matrix layers of nacre](https://doi.org/10.1016/s0142-9612%2803%2900215-1)  Song 等,2003,Biomaterials
- ✓ ⬛ [Biomimetic layer-by-layer assembly of artificial nacre](https://doi.org/10.1038/ncomms1970)  Finnemore 等,2012,Nature Communications
- ✓ [Polarimetry of nacre in iridescent shells](https://doi.org/10.1117/12.2061196)  Metzler 等,2014,SPIE Proceedings
- ✓ [Multilayer optical calculations](https://doi.org/10.48550/arxiv.1603.02720)  Byrnes,2016,arXiv
- ✓ ⬛ [Multilayer optical calculations](https://arxiv.org/abs/1603.02720)  Byrnes,2016,arXiv
- ✓ ⬛ [Structural colors of pearls](https://doi.org/10.1038/s41598-021-94737-w)  Ozaki 等,2021,Scientific Reports
- ✓ ⬛ [investigation of nacre nanostructure by analyzing its structural color pattern](https://doi.org/10.1038/s41598-021-99327-4)  Fan 等,2021,Scientific Reports
- ✓ ⬛ [Brilliant structural colors originating from reflection by nanogaps of nacreous layers in fossilized ammonite shells](https://doi.org/10.1038/s41598-025-21872-z)  Hizukuri 等,2025,Scientific Reports
- ✓ [A Study on Real-time Rendering Techniques for Korean Traditional Nacre Material based on Unreal Engine Substrate](https://doi.org/10.9728/dcs.2025.26.6.1699)  Kang,2025,Journal of Digital Contents Society

</details>

<details><summary><code>metals</code>(26 条)</summary>

- ✓ [RENDERING OF BINARY ALLOYS Example and Validation with Bronze](https://doi.org/10.1007/1-4020-4179-9_67)  Callet 等,Computational Imaging and Vision
- ✓ [The Reflectivity of Speculum Metal](https://doi.org/10.1088/0950-7671/24/9/308)  Tolansky 等,1947,Journal of Scientific Instruments
- ✓ [Optical properties and electronic structure of dilute Cu-Au, Cu-Zn, Cu-Al, Cu-Ga, Cu-Si, Cu-Ge, Cu-Sn, and Cu-As alloys](https://doi.org/10.1103/physrevb.16.4314)  Nastasi-Andrews 等,1977,Physical Review B
- ✓ [Optical Properties of Some Metal Oxides in Solar Absorbers](https://doi.org/10.1088/0031-8949/25/6a/044)  Karlsson 等,1982,Physica Scripta
- ✓ [Copper Oxides (Cu2O, CuO)](https://doi.org/10.1016/b978-0-08-055630-7.50054-7)  RIBBING 等,1998,Handbook of Optical Constants of Solids
- ✓ [Optical Properties of Cu2O Studied by Spectroscopic Ellipsometry](https://doi.org/10.1143/jpsj.67.2125)  Ito 等,1998,Journal of the Physical Society of Japan
- ✓ [Dielectric function and magneto-optical Voigt constant of Cu 2 O: A combined spectroscopic ellipsometry and polar magneto-optical Kerr spectroscopy study](https://doi.org/10.1103/physrevb.84.195203)  Haidu 等,2011,Physical Review B
- ✓ [Electronic and optical properties of Cu, CuO and Cu 2 O studied by electron spectroscopy](https://doi.org/10.1088/0953-8984/24/17/175002)  Tahir 等,2012,Journal of Physics: Condensed Matter
- ✓ [An Analytic Model for the Dielectric Function of Au, Ag, and their Alloys](https://doi.org/10.1002/adom.201300457)  Rioux 等,2013,Advanced Optical Materials
- ✓ [Optical and microstructural characterisation of Au–Sn and Cu–Sn diffusive layers](https://doi.org/10.1016/j.apsusc.2013.01.115)  Wronkowska 等,2013,Applied Surface Science
- ✓ [The Cu–Sn phase diagram, Part I: New experimental results](https://doi.org/10.1016/j.intermet.2012.10.004)  Fürtauer 等,2013,Intermetallics
- ✓ [Optical properties of Au-Ag alloys: An ellipsometric study](https://doi.org/10.1364/ome.4.000403)  Peña-Rodríguez 等,2014,Optical Materials Express
- ✓ [Refractive Index Obtained From Thin Films Of Au-Ag Alloys](https://doi.org/10.5281/zenodo.50484)  Peña-Rodríguez 等,2014,Zenodo
- ✓ [Analysis of Historic Copper Patinas. Influence of Inclusions on Patina Uniformity](https://doi.org/10.3390/ma10030298)  Chang 等,2017,Materials
- ✓ [Real time study of amalgam formation and mercury adsorption on thin gold film by total internal reflection ellipsometry](https://doi.org/10.1016/j.apsusc.2017.08.236)  Paulauskas 等,2018,Applied Surface Science
- ✓ [On the nature of thin films of speculum metal](https://doi.org/10.1016/j.mtcomm.2018.07.005)  E.A. 等,2018,Materials Today Communications
- ✓ [Hybrid Tamm-surface plasmon polaritons mode for detection of mercury adsorption on 1D photonic crystal/gold nanostructures by total internal reflection ellipsometry](https://doi.org/10.1364/oe.26.030400)  Paulauskas 等,2018,Optics Express
- ✓ [The origin and evolution of copper patina colour](https://doi.org/10.1016/j.corsci.2019.05.025)  Leygraf 等,2019,Corrosion Science
- ✓ [Chemical Engineering of Cu–Sn Disordered Network Metamaterials](https://doi.org/10.1021/acs.nanolett.1c03545)  Wohlwend 等,2021,Nano Letters
- ✓ [Investigations on fire‐gilding](https://doi.org/10.1111/arcm.12797)  Margreiter 等,2022,Archaeometry
- ✓ [Comparative Study of Fire-Gilded and Electroplated Gold Films on Copper Substrates](https://doi.org/10.3126/jnphyssoc.v8i3.50717)  Joshi 等,2022,Journal of Nepal Physical Society
- ✓ [Characterization of Gold Thin Films Deposited by Centuries-old Fire-gilding Method](https://doi.org/10.56042/ijpap.v60i2.57063)  2022,Indian Journal of Pure & Applied Physics
- ✓ [Effects of high energy electron and X-ray irradiation on the morphology, microstructure and reflectivity of cast speculum metal mirror](https://doi.org/10.1016/j.radphyschem.2022.110503)  Nazimudeen 等,2023,Radiation Physics and Chemistry
- ✓ [Optical data for Cu2O, CuO and Cu in the 1 eV to ~ 100 eV energy range.](https://doi.org/10.5281/zenodo.7669849)  , Tahir 等,2023,Zenodo
- ✓ [The impact of urban rain on the changes of bare and artificially patinated bronze during 9-year exposure](https://doi.org/10.1007/s11356-024-33369-9)  Kosec 等,2024,Environmental Science and Pollution Research
- ✓ [Microstructural characteristics and formation of the gilded artifacts excavated from Han Tomb situated in Qufu, Shandong, China](https://doi.org/10.1038/s40494-025-01657-3)  Ma 等,2025,npj Heritage Science

</details>

<details><summary><code>peacock</code>(13 条)</summary>

- ✓ ⬛ [Coloration strategies in peacock feathers](https://doi.org/10.1073/pnas.2133313100)  Zi 等,2003,Proceedings of the National Academy of Sciences
- ✓ [Structural origin of the brown color of barbules in male peacock tail feathers](https://doi.org/10.1103/physreve.72.010902)  Li 等,2005,Physical Review E
- ✓ ⬛ [Refractive index and dispersion of butterfly chitin and bird keratin measured by polarizing interference microscopy](https://doi.org/10.1364/oe.19.024061)  Leertouwer 等,2011,Optics Express
- ✓ ⬛ [Eye for an eyespot: how iridescent plumage ocelli influence peacock mating success](https://doi.org/10.1093/beheco/art045)  Dakin 等,2013,Behavioral Ecology
- ✓ [Data from: Deceptive copulation calls attract female visitors to peacock leks](https://doi.org/10.5061/dryad.vt562)  Dakin 等,2013,Dryad
- ✓ ⬛ [High refractive index of melanin in shiny occipital feathers of a bird of paradise](https://doi.org/10.1038/lsa.2015.16)  Stavenga 等,2015,Light: Science & Applications
- ✓ ⬛ [Biomechanics of the Peacock’s Display: How Feather Structure and Resonance Influence Multimodal Signaling](https://doi.org/10.1371/journal.pone.0152759)  Dakin 等,2016,PLOS ONE
- ✓ [Mechanochromic response of the barbules in peacock tail feather](https://doi.org/10.1016/j.optmat.2017.08.024)  Jiang 等,2018,Optical Materials
- ✓ ⬛ [Reflections on iridescent neck and breast feathers of the peacock, Pavo cristatus](https://doi.org/10.1098/rsfs.2018.0043)  Freyer 等,2018,Interface Focus
- ✓ [Reflectance Spectra of Peacock Feathers and the Turning Angles of Melanin Rods in Barbules](https://doi.org/10.2108/zs170091)  Okazaki,2018,Zoological Science
- ✓ ⬛ [How conspicuous are peacock eyespots and other colorful feathers in the eyes of mammalian predators?](https://doi.org/10.1371/journal.pone.0210924)  Kane 等,2019,PLOS ONE
- ✓ ⬛ [Biophotonics of diversely coloured peacock tail feathers](https://doi.org/10.1039/d0fd00033g)  Freyer 等,2020,Faraday Discussions
- ✓ ⬛ [Structural Color Expression Due to Specular Reflection from Bird Feathers](https://doi.org/10.55653/forma.2022.001.002)  Okazaki,2022,FORMA

</details>

<details><summary><code>qinghua-s3</code>(21 条)</summary>

- ◐ [10.36410/jcpr.2025.26.5.742](https://doi.org/10.36410/jcpr.2025.26.5.742)
- ✓ [The influence of water on the environment of transition metals in silicate glasses](https://doi.org/10.2138/am-1998-1-204)  Nowak 等,1998,American Mineralogist
- ✓ [Non-destructive analysis and appraisal of ancient Chinese porcelain by PIXE](https://doi.org/10.1016/s0168-583x%2801%2901280-0)  Cheng 等,2002,Nuclear Instruments and Methods in Physics Research Section B: Beam Interactions with Materials and Atoms
- ✓ ⬛ [Effects of Glass Structure on the Optical Absorption of Transition Ions in Industrial Soda-Lime-Silica Glasses](https://doi.org/10.1299/jmmp.1.508)  THIEMSORN 等,2007,Journal of Solid Mechanics and Materials Engineering
- ✓ [Microstructure characteristics of blue-and-white porcelain from the folk kiln of Ming and Qing Dynasties](https://doi.org/10.1016/j.ceramint.2014.01.100)  Qu 等,2014,Ceramics International
- ✓ [Microscopic analysis of “iron spot” on blue‐and‐white porcelain from Jingdezhen imperial kiln in early Ming dynasty (14th–15th century)](https://doi.org/10.1002/jemt.22766)  Wang 等,2016,Microscopy Research and Technique
- ✓ [Synchrotron radiation-based multi-analytical approach for studying underglaze color: The microstructure of Chinese Qinghua blue decors (Ming dynasty)](https://doi.org/10.1016/j.aca.2016.04.053)  Wang 等,2016,Analytica Chimica Acta
- ✓ [Export Chinese blue-and-white porcelain: compositional analysis and sourcing using non-invasive portable XRF and reflectance spectroscopy](https://doi.org/10.1016/j.jas.2017.01.016)  Fischer 等,2017,Journal of Archaeological Science
- ✓ [X‐ray absorption spectroscopy study of synthetic cobalt blue pigments similar to Kangxi blue and white porcelain](https://doi.org/10.1111/jace.15353)  Luo 等,2017,Journal of the American Ceramic Society
- ✓ [The role of different network modifying cations on the speciation of the Co2+ complex in silicates and implication in the investigation of historical glasses](https://doi.org/10.1016/j.saa.2017.07.031)  Fornacelli 等,2018,Spectrochimica Acta Part A: Molecular and Biomolecular Spectroscopy
- ✓ [Chromogenic mechanisms in blue-and-white porcelains](https://doi.org/10.1016/j.jeurceramsoc.2020.06.065)  Pinto 等,2020,Journal of the European Ceramic Society
- ✓ [Early globalized industrial chain revealed by residual submicron pigment particles in Chinese imperial blue-and-white porcelains](https://doi.org/10.1073/pnas.1916630117)  Jiang 等,2020,Proceedings of the National Academy of Sciences
- ✓ [Provenance of the cobalt pigment used for Jingdezhen minyao blue-and-white porcelain in the early Qing dynasty](https://doi.org/10.1016/j.ceramint.2021.05.303)  Zhang 等,2021,Ceramics International
- ✓ [Using UV-Vis-NIR absorption spectroscopy as a tool for the detection of iron and cobalt in glass: A case-study on HLLA material from the Low Countries](https://doi.org/10.1016/j.jasrep.2022.103517)  Patin 等,2022,Journal of Archaeological Science: Reports
- ✓ [Microstructure analysis of “iron spots” on Qinghua porcelain from Jingdezhen imperial kiln](https://doi.org/10.1016/j.jeurceramsoc.2022.09.056)  Wang 等,2023,Journal of the European Ceramic Society
- ✓ ⬛ [The atypical hues of the Santa Cruz blue-and-white cargo: non-invasive analysis of glaze defects and color variations in mid-Ming porcelain](https://doi.org/10.1186/s40494-023-00953-0)  Hsieh 等,2023,Heritage Science
- ✓ [Revisiting the bleeding effect in historical cobalt porcelain pigments: Mechanism, influence and technical responses](https://doi.org/10.1016/j.jas.2024.105987)  Jiang 等,2024,Journal of Archaeological Science
- ✓ [An Archaeometric Study of Twelve Porcelain Chinese Sherds Found at the Santana Convent in Lisbon – – 16th to 18th Centuries](https://doi.org/10.20944/preprints202505.2496.v1)  Vieira Ferreira 等,2025
- ✓ [An Archaeometric Study of Twelve Porcelain Chinese Sherds Found at the Santana Convent in Lisbon—16th to 18th Centuries](https://doi.org/10.3390/heritage8070253)  Ferreira 等,2025,Heritage
- ✓ [Interpreting the firing technology logic of the Jingdezhen egg-shaped kiln through experimental archaeology](https://doi.org/10.1038/s40494-026-02801-3)  Jiang 等,2026,npj Heritage Science
- ✓ [Effect of Luanbai Glaze on the Coloration of Cobalt Pigment in Yuan Dynasty Jingdezhen Porcelains: An Experimental Study](https://doi.org/10.3390/ma19112254)  Sun 等,2026,Materials

</details>

<details><summary><code>qinghua-spectra</code>(10 条)</summary>

- ✓ [Redox ratio and optical absorption of polyvalent ions in industrial glasses](https://doi.org/10.1007/s12034-007-0077-7)  Thiemsorn 等,2007,Bulletin of Materials Science
- ✓ [New insights into the role of Mn and Fe in coloring origin of blue decorations of blue-and-white porcelains by XANES spectroscopy](https://doi.org/10.1088/1742-6596/430/1/012066)  Zhu 等,2013,Journal of Physics: Conference Series
- ✓ [Optical spectroscopy of sodium silicate glasses prepared with nano- and micro-sized iron oxide particles](https://doi.org/10.2298/pac1303117m)  Mehdikhani 等,2013,Processing and Application of Ceramics
- ✓ [Diluted Fe3+ in silicate glasses: Structural effects of Fe-redox state and matrix composition. An optical absorption and X-band/Q-band EPR study](https://doi.org/10.1016/j.jnoncrysol.2015.08.010)  Vercamer 等,2015,Journal of Non-Crystalline Solids
- ✓ [Iron speciation in soda-lime-silica glass: a comparison of XANES and UV-vis-NIR spectroscopy](https://doi.org/10.1039/c5ja00046g)  Ceglia 等,2015,Journal of Analytical Atomic Spectrometry
- ✓ [Synchrotron XAS study of Mn and Fe in Chinese blue-and-white Ming porcelains from the second half of the 15th century](https://doi.org/10.1016/j.ceramint.2020.09.123)  Roqué-Rosell 等,2021,Ceramics International
- ✓ [Research on blue and white porcelain from different ages based on hyperspectral technology](https://doi.org/10.1016/j.culher.2023.05.025)  Zhao 等,2023,Journal of Cultural Heritage
- ✓ [Dating of Jingdezhen blue and white porcelain based on transfer learning and imaging spectroscopy techniques](https://doi.org/10.1038/s40494-025-01652-8)  Zhao 等,2025,npj Heritage Science
- ✓ [An Archaeometric Study of the Porcelain Chinese Sherds Found at the Santana Convent in Lisbon – Part 2 – A Comparison with Coeval Chinese Samples of Well-Known Provenance](https://doi.org/10.20944/preprints202605.1370.v1)  Vieira Ferreira 等,2026
- ✓ [An Archaeometric Study of Chinese Porcelain Sherds Found at the Santana Convent in Lisbon—Part 2: A Comparison with Coeval Chinese Samples of Well-Known Provenance](https://doi.org/10.3390/coatings16070765)  Vieira Ferreira 等,2026,Coatings

</details>

<details><summary><code>qinghua-stack</code>(7 条)</summary>

- ◐ [10.13957/j.cnki.tcxb.2017.02.005](https://doi.org/10.13957/j.cnki.tcxb.2017.02.005)
- ◐ [10.13957/j.cnki.tcxb.2026.01.019](https://doi.org/10.13957/j.cnki.tcxb.2026.01.019)
- ✓ [The exploration of Sr isotopic analysis applied to Chinese glazes: part one](https://doi.org/10.1016/j.jas.2013.08.015)  Ma 等,2014,Journal of Archaeological Science
- ✓ [Aging study on the modern imitation glaze and ancient glaze of the Ming and Qing dynasties based on FTIR decomposition spectra](https://doi.org/10.1016/j.jnoncrysol.2018.10.024)  Li 等,2019,Journal of Non-Crystalline Solids
- ✓ [Cost-effective and eco-friendly transparent ceramic glazes for porcelain bodies](https://doi.org/10.1007/s41779-023-00906-7)  Koroglu 等,2023,Journal of the Australian Ceramic Society
- ✓ [Maximization of the blue-white contrast of ancient porcelain decorations from Jingdezhen imperial kiln by Co-spinel formation](https://doi.org/10.1016/j.jeurceramsoc.2024.04.003)  Li 等,2024,Journal of the European Ceramic Society
- ✓ [Influence of cobalt specialization state on color mechanism and ‘color dispersion’ behavior of blue-and-white porcelain](https://doi.org/10.1016/j.jeurceramsoc.2024.117128)  Li 等,2025,Journal of the European Ceramic Society

</details>

<details><summary><code>reds-s3</code>(38 条)</summary>

- — [10.15964/j.cnki.027jgg.2019.s1.019](https://doi.org/10.15964/j.cnki.027jgg.2019.s1.019)
- ◐ [10.16490/j.cnki.issn.1001-3660.2017.02.003](https://doi.org/10.16490/j.cnki.issn.1001-3660.2017.02.003)
- ◐ [10.82019/jaic.2606](https://doi.org/10.82019/jaic.2606)
- ✓ [X. The Bakerian Lecture. —Experimental relations of gold (and other metals) to light](https://doi.org/10.1098/rstl.1857.0011)  Faraday,1857,Philosophical Transactions of the Royal Society of London
- ✓ [Chicken-Blood Stone from China](https://doi.org/10.5741/gems.25.3.168)  Fuquan 等,1989,Gems & Gemology
- ✓ [Role of protolytic interactions in photo-aging processes of carminic acid and carminic lake in solution and painted layers](https://doi.org/10.1039/b104595b)  2001,Journal of the Chemical Society, Perkin Transactions 2
- ✓ [An absorption spectroscopic investigation of the interaction of lac dyes with metal ions](https://doi.org/10.1016/j.dyepig.2004.02.006)  Chairat 等,2004,Dyes and Pigments
- ✓ [Formation of gold nanoparticles in gold ruby glass: The influence of tin](https://doi.org/10.1007/s10751-006-9246-0)  Haslbeck 等,2005,Hyperfine Interactions
- ✓ [Optical Properties of Hydrothermally Synthesized Hematite Particulate Pigments](https://doi.org/10.1111/j.1551-2916.2005.00643.x)  Wang 等,2005,Journal of the American Ceramic Society
- ✓ [Determination of Size and Concentration of Gold Nanoparticles from UV−Vis Spectra](https://doi.org/10.1021/ac0702084)  Haiss 等,2007,Analytical Chemistry
- ✓ [The pH Dependence of Absorption Spectra of Carthamin in Aqueous Solution](https://doi.org/10.2115/fiber.63.185)  Otsu 等,2007,Sen'i Gakkaishi
- ✓ [Gold nanoparticles in ancient and contemporary ruby glass](https://doi.org/10.1016/j.culher.2008.08.003)  Ruivo 等,2008,Journal of Cultural Heritage
- ✓ [Identification of anthraquinone markers for distinguishing Rubia species in madder-dyed textiles by HPLC](https://doi.org/10.1007/s00604-012-0868-4)  Mouri 等,2012,Microchimica Acta
- ✓ [Micro‐analysis on Chinese over‐glaze red decoration of Linshui Kiln from Jin dynasty (1115–1234 ad)](https://doi.org/10.1002/jrs.4447)  Hao 等,2014,Journal of Raman Spectroscopy
- ✓ [Colouration mechanism of underglaze copper-red decoration porcelain (AD 13th–14th century), China](https://doi.org/10.1107/s1600577514009382)  Zhu 等,2014,Journal of Synchrotron Radiation
- ✓ [Raman Investigations to Identify Corallium rubrum in Iron Age Jewelry and Ornaments](https://doi.org/10.3390/min6020056)  Fürst 等,2016,Minerals
- ✓ [Characterization of Hematite Red Pigment for Porcelain Surface Coating](https://doi.org/10.3740/mrsk.2017.27.4.206)  Kim 等,2017,Korean Journal of Materials Research
- ✓ [Screen Printed Pb3O4 Films and Their Application to Photoresponsive and Photoelectrochemical Devices](https://doi.org/10.3390/ma11071189)  Panetta 等,2018,Materials
- ✓ [Weathering behavior of cinnabar-based tempera paints upon natural and accelerated aging](https://doi.org/10.1016/j.saa.2019.03.027)  Elert 等,2019,Spectrochimica Acta Part A: Molecular and Biomolecular Spectroscopy
- ✓ [Seeing red: towards an improved protocol for the identification of madder- and cochineal-based pigments by fiber optics reflectance spectroscopy (FORS)](https://doi.org/10.1186/s40494-019-0335-1)  Fonseca 等,2019,Heritage Science
- ✓ [A combined theoretical and experimental investigation of the electronic and vibrational properties of red lead pigment](https://doi.org/10.1016/j.culher.2020.04.014)  Amat 等,2020,Journal of Cultural Heritage
- ✓ [Hydrothermal Precipitation of Sanidine (Adularia) Having Full Al,Si Structural Disorder and Specular Hematite at Maunakea Volcano (Hawai'i) and at Gale Crater (Mars)](https://doi.org/10.1029/2019je006324)  Morris 等,2020,Journal of Geophysical Research: Planets
- ✓ [Color and molecular structure alterations of brazilein extracted from Caesalpinia sappan L. under different pH and heating conditions](https://doi.org/10.1038/s41598-020-69189-3)  Ngamwonglumlert 等,2020,Scientific Reports
- ✓ [Direct evidence for metallic mercury causing photo-induced darkening of red cinnabar tempera paints](https://doi.org/10.1038/s42004-021-00610-2)  Elert 等,2021,Communications Chemistry
- ✓ [Scientific Studies of Pigments in Chinese Paintings](https://doi.org/10.5479/10088/111861)  2021
- ✓ [Reconstruction of traditional safflower (Carthamus tinctorius L.) dyeing and red colors in the Qing Dynasty (17th-19th century)](https://doi.org/10.1016/j.dyepig.2022.110697)  Jin 等,2022,Dyes and Pigments
- ✓ ⬛ [Jun ware glaze colours: An X-ray absorption spectroscopy study](https://doi.org/10.1016/j.jeurceramsoc.2022.02.016)  Yuan 等,2022,Journal of the European Ceramic Society
- ✓ [Surface treatment of red painted and slipped wares in the middle Yangtze River valley of Late Neolithic China: multi-analytical case analysis](https://doi.org/10.1186/s40494-022-00824-0)  Li 等,2022,Heritage Science
- ✓ [The Analysis of Red Lead Endsheets in Rare Books from the Fung Ping Shan Library at the University of Hong Kong](https://doi.org/10.3390/heritage5030125)  Querner 等,2022,Heritage
- ✓ [Transient absorption study on Red Vermilion darkening in presence of chlorine ions and after UV exposure](https://doi.org/10.1016/j.jphotochem.2022.114291)  Pisu 等,2023,Journal of Photochemistry and Photobiology A: Chemistry
- ✓ [Surface-enhanced Raman spectroscopy for madder lake detection in painting layers](https://doi.org/10.1140/epjp/s13360-023-03964-9)  Innocenti 等,2023,The European Physical Journal Plus
- ✓ [A Non-Invasive and Sustainable Characterization of Pigments in Wall Paintings: A Library of Apulian Colors](https://doi.org/10.3390/heritage6020084)  Fioretti 等,2023,Heritage
- ✓ [Non-destructive identification of iron oxide crystals in 15th century A.D. Chinese imperial red overglaze decoration](https://doi.org/10.1016/j.jasrep.2024.104733)  Duan 等,2024,Journal of Archaeological Science: Reports
- ✓ [Database of diffuse reflectance infrared Fourier transform spectroscopy (DRIFTS) and hyperspectral imaging (HSI) spectra of pigments and dyes for historical document analysis](https://doi.org/10.1007/s00216-025-05948-3)  Reichert 等,2025,Analytical and Bioanalytical Chemistry
- ✓ [Study on the coloration mechanism of Jingdezhen ox-hair pattern copper-red glaze](https://doi.org/10.2109/jcersj2.25097)  Yang 等,2025,Journal of the Ceramic Society of Japan
- ✓ [Supplementary Information - Database of pigments and dyes in historical manuscripts using Diffuse Reflectance Infrared Fourier Transform Spectroscopy (DRIFTS) and Hyperspectral Imaging (HSI)](https://doi.org/10.6084/m9.figshare.28639103.v1)  Reichert 等,2025,figshare
- ✓ [Compositional Characterization and Color Genesis of Precious Coral Based on Multi-Spectroscopic Techniques](https://doi.org/10.3390/cryst16060374)  Yang 等,2026,Crystals
- ✓ [Raw data for ‘Compositional Characterization and Color Genesis of Precious Coral Based on Multi-Spectroscopic Techniques’](https://doi.org/10.6084/m9.figshare.32404389)  Yang,2026,figshare

</details>

<details><summary><code>reuse</code>(17 条)</summary>

- ✓ [Refractive Indices of HgS (Cinnabar) between 0.62 and 11 μ](https://doi.org/10.1063/1.1709079)  Bond 等,1967,Journal of Applied Physics
- ✓ [Computer-generated watercolor](https://doi.org/10.1145/258734.258896)  Curtis 等,1997,Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97
- ✓ [Analysis of transitions between fluttering, tumbling and steady descent of falling cards](https://doi.org/10.1017/s0022112005005847)  ANDERSEN 等,2005,Journal of Fluid Mechanics
- ✓ [MoXi](https://doi.org/10.1145/1073204.1073221)  Chu 等,2005,ACM Transactions on Graphics
- ✓ [Optical Characterization of Japanese Papers for Application in the LED Lighting System with Human Sensitivity](https://doi.org/10.2150/jlve.32.218)  MOTOGAITO 等,2008,Journal of Light & Visual Environment
- ✓ [Monte Carlo Modeling of Light Scattering in Paper](https://doi.org/10.2352/j.imagingsci.technol.2009.53.2.020201)  Modrić 等,2009,Journal of Imaging Science and Technology
- ✓ [Electronic and phononic properties of cinnabar:Ab initiocalculations and some experimental results](https://doi.org/10.1103/physrevb.82.085210)  Cardona 等,2010,Physical Review B
- ✓ [Electronic and phononic properties of cinnabar: ab initio calculations and some experimental results](https://arxiv.org/abs/1007.2210)  Cardona 等,2010,arXiv
- ✓ [Foaming Property and Foam Diameter of Matcha Varies with Particle Size](https://doi.org/10.3136/nskkk.59.109)  Sawamura 等,2012,Nippon Shokuhin Kagaku Kogaku Kaishi
- ✓ [A revised Michel-Lévy interference colour chart based on first-principles calculations](https://doi.org/10.1127/0935-1221/2013/0025-2252)  Sørensen,2013,European Journal of Mineralogy
- ✓ ⬛ [A practical extension to microfacet theory for the modeling of varying iridescence](https://doi.org/10.1145/3072959.3073620)  Belcour 等,2017,ACM Transactions on Graphics
- ✓ [A non-invasive investigation of Limoges enamels using both Optical Coherence Tomography (OCT) and spectral imaging: a pilot study](https://doi.org/10.1117/12.2527092)  Read 等,2019,Optics for Arts, Architecture, and Archaeology VII
- ✓ [Improved methodology for performing the inverse Abel transform of flame images for color ratio pyrometry](https://doi.org/10.1364/ao.58.002662)  Dreyer 等,2019,Applied Optics
- ✓ [A non-invasive investigation of Limoges enamels using both Optical Coherence Tomography (OCT) and spectral imaging: a pilot study](https://arxiv.org/abs/2002.12132)  Read 等,2020,arXiv
- ✓ [Hyperspectral interference tomography of nacre](https://arxiv.org/abs/2010.08170)  Salman 等,2020,arXiv
- ✓ [Hyperspectral interference tomography of nacre](https://doi.org/10.1073/pnas.2023623118)  Salman 等,2021,Proceedings of the National Academy of Sciences
- ✓ [Numerical Analysis of Structural Coloration of Dark Color Pearls by Nacre Crystal Multilayers](https://doi.org/10.15748/jasse.12.152)  Wakabayashi 等,2025,Journal of Advanced Simulation in Science and Engineering

</details>

<details><summary><code>ru</code>(3 条)</summary>

- ◐ [10.16552/j.cnki.issn1001-1625.2024.1417](https://doi.org/10.16552/j.cnki.issn1001-1625.2024.1417)
- ✓ [Mössbauer spectroscopy and neutron activation analysis of ancient Chinese glazes](https://doi.org/10.1016/j.clay.2003.09.004)  Bin 等,2004,Applied Clay Science
- ✓ ⬛ [Amorphous photonic crystals and structural colors in the phase separation glaze](https://doi.org/10.1016/j.jeurceramsoc.2017.10.036)  Shi 等,2018,Journal of the European Ceramic Society

</details>

<details><summary><code>ru-crackle</code>(9 条)</summary>

- ◐ [10.11395/jjsem.8.59](https://doi.org/10.11395/jjsem.8.59)
- ✓ [Crack opening profiles of indentation cracks in normal and anomalous glasses](https://doi.org/10.1016/j.actamat.2003.09.014)  Burghard 等,2004,Acta Materialia
- ✓ [Hierarchical crack patterns: a comparison with two-dimensional soap foams](https://doi.org/10.1016/j.colsurfa.2004.11.013)  Bohn,2005,Colloids and Surfaces A: Physicochemical and Engineering Aspects
- ✓ [Roughness of glass surfaces formed by sub-critical crack growth](https://doi.org/10.1016/j.jnoncrysol.2007.01.029)  Wiederhorn 等,2007,Journal of Non-Crystalline Solids
- ✓ [A new method to demonstrate frustrated total internal reflection in the visible band](https://doi.org/10.1119/1.2825389)  You 等,2008,American Journal of Physics
- ✓ [USING OPTICAL COHERENCE TOMOGRAPHY TO EXAMINE THE SUBSURFACE MORPHOLOGY OF CHINESE GLAZES](https://doi.org/10.1111/j.1475-4754.2009.00451.x)  YANG 等,2009,Archaeometry
- ✓ [In-Situ Observation of Propagating-Crack Front Geometry in Thermal Stress Cleaving of Thin Glass Plates](https://doi.org/10.1299/kikaia.75.925)  MOTOMURA 等,2009,Transactions of the Japan Society of Mechanical Engineers Series A
- ✓ [Degradation mechanism of the Ru wares unearthed from the Qingliangsi site in Henan, China](https://doi.org/10.1016/j.ceramint.2022.02.269)  He 等,2022,Ceramics International
- ✓ [Comparative study on the Ru ware, Ru‐type ware of Qingliangsi kiln and celadon of Zhanggongxiang kiln](https://doi.org/10.1111/jmi.13239)  Tao 等,2023,Journal of Microscopy

</details>

<details><summary><code>ru2</code>(12 条)</summary>

- ✓ [The Density of Silicate Glasses as a Function of Composition*](https://doi.org/10.1364/josa.30.000420)  Huggins,1940,Journal of the Optical Society of America
- ✓ [The Refractive Index of Silicate Glasses as a Function of Composition*](https://doi.org/10.1364/josa.30.000495)  Huggins,1940,Journal of the Optical Society of America
- ✓ [The Dispersion of Silicate Glasses as a Function of Composition*](https://doi.org/10.1364/josa.30.000514)  Huggins,1940,Journal of the Optical Society of America
- ✓ [The Dispersion of Silicate Glasses as a Function of Composition II*](https://doi.org/10.1364/josa.32.000635)  Huggins 等,1942,Journal of the Optical Society of America
- ✓ [CALCULATION OF DENSITY AND OPTICAL CONSTANTS OF A GLASS FROM ITS COMPOSITION IN WEIGHT PERCENTAGE*](https://doi.org/10.1111/j.1151-2916.1943.tb15176.x)  Huggins 等,1943,Journal of the American Ceramic Society
- ✓ [Refractive index and spectral models for gradient-index materials](https://doi.org/10.1364/ao.22.000432)  Fantone,1983,Applied Optics
- ✓ [Refractive indices and optical dispersion of 103 synthetic and mineral oxides and silicates measured by a small-prism technique](https://doi.org/10.1364/josab.14.003299)  Medenbach 等,1997,Journal of the Optical Society of America B
- ✓ [Prediction of optical properties of commercial soda–lime-silicate glasses containing iron](https://doi.org/10.1016/s0022-3093%2899%2900617-1)  Uchino 等,2000,Journal of Non-Crystalline Solids
- ✓ [Study on Ru ware glaze of the Northern Song dynasty: One of the earliest crystalline-phase separated glazes in ancient China](https://doi.org/10.1016/j.ceramint.2004.07.002)  Li 等,2005,Ceramics International
- ✓ [Predicting refractive index of fluoride containing glasses for aesthetic dental restorations](https://doi.org/10.1016/j.dental.2018.01.024)  Duminis 等,2018,Dental Materials
- ✓ [Analysis of structural effects on coloring mechanism of Ru celadon porcelain](https://doi.org/10.1002/ces2.10058)  Chen 等,2020,International Journal of Ceramic Engineering & Science
- ✓ [Study on the coloring mechanism of the Ru celadon glaze in the Northern Song Dynasty](https://doi.org/10.1016/j.ceramint.2020.06.139)  Shi 等,2020,Ceramics International

</details>

<details><summary><code>silk</code>(16 条)</summary>

- ✓ [Laser-Induced Fluorescence and Optical Reflection Spectra of Japanese Natural Dyes on Silk](https://doi.org/10.1143/jjap.26.239)  Miyoshi 等,1987,Japanese Journal of Applied Physics
- ✓ [Microstructural Characterization of Bombyx mori Silk Fibers](https://doi.org/10.1021/ma980281j)  Shen 等,1998,Macromolecules
- ✓ ⬛ [Matching Real Fabrics with Micro-Appearance Models](https://doi.org/10.1145/2818648)  Khungurn 等,2015,ACM Transactions on Graphics
- ✓ ⬛ [Fitting procedural yarn models for realistic cloth rendering](https://doi.org/10.1145/2897824.2925932)  Zhao 等,2016,ACM Transactions on Graphics
- ✓ [The optical properties of regenerated silk fibroin films obtained from different sources](https://doi.org/10.1063/1.4998950)  Perotto 等,2017,Applied Physics Letters
- ✓ [An Appearance Model for Textile Fibers](https://doi.org/10.1111/cgf.13222)  Aliaga 等,2017,Computer Graphics Forum
- ✓ [An investigation of the dye palette in Chinese silk embroidery from Dunhuang (Tang dynasty)](https://doi.org/10.1007/s12520-017-0592-4)  Tamburini 等,2018,Archaeological and Anthropological Sciences
- ✓ [Simple multi-wavelength imaging of birefringence:case study of silk](https://doi.org/10.1038/s41598-018-36114-8)  Honda 等,2018,Scientific Reports
- ✓ ⬛ [Simple multi-wavelength imaging of birefringence: case study of silk](https://arxiv.org/abs/1809.09723)  Honda 等,2018,arXiv
- ✓ [Fibre optic reflectance spectroscopy and multispectral imaging for the non-invasive investigation of Asian colourants in Chinese textiles from Dunhuang (7th-10th century AD)](https://doi.org/10.1016/j.dyepig.2018.10.054)  Tamburini 等,2019,Dyes and Pigments
- ✓ [Nanoscale optical and structural characterisation of silk](https://doi.org/10.3762/bjnano.10.93)  Ryu 等,2019,Beilstein Journal of Nanotechnology
- ✓ [A practical ply-based appearance model of woven fabrics](https://doi.org/10.1145/3414685.3417777)  Montazeri 等,2020,ACM Transactions on Graphics
- ✓ [Non-invasive study of natural dyes in textiles of the Qing Dynasty using fiber optic reflectance spectroscopy](https://doi.org/10.1016/j.culher.2020.10.013)  Ding 等,2021,Journal of Cultural Heritage
- ✓ [Exploring elucidation of red dye mixtures on woolen historical textiles via non-destructive spectroscopic analysis and multivariate cluster analysis](https://doi.org/10.1186/s40494-023-01108-x)  Celani 等,2024,Heritage Science
- ✓ [Thermal study of Bombyx mori silk fibroin film obtained through degumming process for biomaterial application](https://doi.org/10.1007/s10973-025-15115-6)  Yaiphabi 等,2025,Journal of Thermal Analysis and Calorimetry
- ✓ [Inversion of optical constants of natural silk fibers based on FDTD-PSO and scattering experiments](https://doi.org/10.1016/j.jqsrt.2024.109314)  Tao 等,2025,Journal of Quantitative Spectroscopy and Radiative Transfer

</details>

<details><summary><code>speculum</code>(11 条)</summary>

- ✓ [Reflecting power of beryllium, chromium, and several other metals](https://doi.org/10.6028/jres.002.005)  Coblentz 等,1929,Bureau of Standards Journal of Research
- ✓ [Investigation and replication of the surface microstructure of early Chinese black bronze mirrors](https://doi.org/10.2172/10161385)  Brookhaven National Lab., Upton, NY (United States) 等,1994
- ✓ [AMALGAM TINNING OF CHINESE BRONZE ANTIQUITIES*](https://doi.org/10.1111/j.1475-4754.2000.tb00875.x)  ANHEUSER,2000,Archaeometry
- ✓ [Transformation of ancient Chinese and model two-phase bronze surfaces to smooth adherent patinas](https://doi.org/10.1080/01411590701514375)  Taube 等,2008,Phase Transitions
- ✓ ⬛ [A journey from ancient China: bronze mirrors to picometer-shaped interference coatings](https://doi.org/10.3788/col201008s1.0007)  Norbert Kaiser 等,2010,Chinese Optics Letters
- ✓ [Experimental design of the Cu-As-Sn ternary colour diagram](https://doi.org/10.1016/j.jas.2017.12.001)  Radivojević 等,2018,Journal of Archaeological Science
- ✓ ⬛ [Close up to the surface: reflections on a preliminary forensic study of four Chinese bronze mirrors](https://doi.org/10.1186/s40494-021-00496-2)  Liang 等,2021,Heritage Science
- ✓ ⬛ [EMPHASIS ON VISUAL AND TACTILE EXPERIENCES: MECHANICAL TREATMENTS OF BRONZES AND JADES IN ANCIENT CHINA](https://doi.org/10.1017/eac.2023.6)  Li,2023,Early China
- ✓ ⬛ [New insights on the analysis of the causes of glossy lustre on the surface of ancient Chinese bronze mirrors](https://doi.org/10.1186/s40494-024-01247-9)  Wang 等,2024,Heritage Science
- ✓ ⬛ [A mechanism study of type i corrosion on the surface of ancient tin rich bronzes](https://doi.org/10.1186/s40494-024-01472-2)  Jiang 等,2024,Heritage Science
- ✓ [Corrosion microstructure and coloration mechanism of ancient Chinese bronze mirrors](https://doi.org/10.1007/s12520-026-02474-w)  Wang 等,2026,Archaeological and Anthropological Sciences

</details>

<details><summary><code>stains</code>(3 条)</summary>

- ◐ [10.16521/j.cnki.issn.1001-9642.2026.05.012](https://doi.org/10.16521/j.cnki.issn.1001-9642.2026.05.012)
- ✓ [USGS Spectral Library Version 7](https://doi.org/10.3133/ds1035)  Kokaly 等,2017,Data Series
- ✓ [USGS Spectral Library Version 7 Data](https://doi.org/10.5066/f7rr1wdj)  Raymond Kokaly 等,2017,U.S. Geological Survey

</details>

<details><summary><code>studio</code>(3 条)</summary>

- ✓ [Relative spectral power distributions of illuminants representing typical LED lamps](https://doi.org/10.25039/cie.ds.vgssnyfg)  International Commission on Illumination (CIE),CIEdataTableDatabase
- ✓ [Characterization of the Reflectivity of Various Black Materials](https://arxiv.org/abs/1407.8265)  Marshall 等,2014,arXiv
- ✓ [How Dark is Dark? A Reflectance and Scattering Analysis of Black Materials](https://arxiv.org/abs/2601.05094)  Filip 等,2026,arXiv

</details>

<details><summary><code>tangyuan_look</code>(2 条)</summary>

- ✓ [Effects of temperature, shear rate and constituents on rheological properties of tahin (sesame paste)](https://doi.org/10.1002/jsfa.1945)  Lokumcu Altay 等,2004,Journal of the Science of Food and Agriculture
- ✓ [PHYSICOCHEMICAL AND RHEOLOGICAL PROPERTIES OF SESAME PASTES (TAHIN) PROCESSED FROM HULLED AND UNHULLED ROASTED SESAME SEEDS AND THEIR BLENDS AT VARIOUS LEVELS](https://doi.org/10.1111/j.1745-4530.2007.00162.x)  AKBULUT 等,2008,Journal of Food Process Engineering

</details>

<details><summary><code>tea_plume</code>(2 条)</summary>

- ✓ [Binary diffusion coefficients of phenolic compounds in subcritical water using a chromatographic peak broadening technique](https://doi.org/10.1016/j.fluid.2010.12.003)  Srinivas 等,2011,Fluid Phase Equilibria
- ✓ [Does the Type Matter? Verification of Different Tea Types’ Potential in the Synthesis of SeNPs](https://doi.org/10.3390/antiox11122489)  Sentkowska 等,2022,Antioxidants

</details>

<details><summary><code>v3nacre</code>(2 条)</summary>

- ◐ [10.15964/j.cnki.027jgg.2026.04.009](https://doi.org/10.15964/j.cnki.027jgg.2026.04.009)
- ✓ [Iridescent Color of a Shell of the Mollusk Pinctada Margaritifera Caused by Diffraction](https://doi.org/10.1364/oe.4.000177)  Liu 等,1999,Optics Express

</details>

<details><summary><code>webgpu-pt</code>(2 条)</summary>

- ✓ [Physically-based Path Tracer using WebGPU and OpenPBR](https://arxiv.org/abs/2407.19977)  Stucki 等,2024,arXiv
- ✓ [HyperDrone: Simulation-to-Reality Transfer at Millions of Frames per Second](https://arxiv.org/abs/2610.28950)  Eschmann 等,2026,arXiv

</details>

<details><summary><code>yanzhi</code>(10 条)</summary>

- ✓ [Optical Constants of the Noble Metals](https://doi.org/10.1103/physrevb.6.4370)  Johnson 等,1972,Physical Review B
- ✓ [Optical Properties of Metal Clusters](https://doi.org/10.1007/978-3-662-09109-8)  Kreibig 等,1995,Springer Series in Materials Science
- ✓ ⬛ [Observation of Intrinsic Size Effects in the Optical Response of Individual Gold Nanoparticles](https://doi.org/10.1021/nl050062t)  Berciaud 等,2005,Nano Letters
- ✓ [Plasmonic Films Can Easily Be Better: Rules and Recipes](https://doi.org/10.1021/ph5004237)  McPeak 等,2015,ACS Photonics
- ✓ [Plasmonic Films Can Easily Be Better: Rules and Recipes](https://arxiv.org/abs/1603.02132)  McPeak 等,2016,arXiv
- ✓ [Study of arsenic in Famille rose porcelain from the Imperial Palace of Qing Dynasty, Beijing, China](https://doi.org/10.1016/j.ceramint.2017.10.084)  Li 等,2018,Ceramics International
- ✓ [The composition and technology of polychrome enamels on Chinese ruby‐backed plates identified through nondestructive micro‐X‐ray fluorescence](https://doi.org/10.1002/xrs.3144)  Norris 等,2020,X-Ray Spectrometry
- ✓ ⬛ [Fabrication of gold ruby glasses using solar panel glass cullet](https://doi.org/10.2109/jcersj2.21087)  TAKEBE 等,2021,Journal of the Ceramic Society of Japan
- ✓ [Non-invasive analyze of boron and lithium in 18th century Chinese porcelain enamel and glaze: A PIXE/PIGE study](https://doi.org/10.1016/j.jeurceramsoc.2024.116746)  Burlot 等,2024,Journal of the European Ceramic Society
- ✓ ⬛ [Chinese Porcelains of the Early 18<sup>th</sup> Century from the Commander Islands, Northwest Pacific: Archaeometry Study](https://doi.org/10.4236/chnstd.2025.142011)  Zhushchikhovskaya 等,2025,Chinese Studies

</details>

<details><summary><code>yanzhi2</code>(11 条)</summary>

- ◐ [10.14062/j.issn.0454-5648.2011.11.022](https://doi.org/10.14062/j.issn.0454-5648.2011.11.022)
- ✓ [AN INVESTIGATION OF THE ORIGIN OF THE COLOUR OF THE LYCURGUS CUP BY ANALYTICAL TRANSMISSION ELECTRON MICROSCOPY](https://doi.org/10.1111/j.1475-4754.1990.tb01079.x)  BARBER 等,1990,Archaeometry
- ✓ [Optical Spectroscopic Study of Lead Silicate Glasses Doped Heavily with Iron Oxide](https://doi.org/10.2320/matertrans1989.38.220)  Ookawa 等,1997,Materials Transactions, JIM
- ✓ [A STUDY OF RUBY-PINK ENAMELS ON CHINESE PORCELAIN: WITH A COMPARISON OF CHINESE PINK GLASS, AND EUROPEAN PINK ENAMELS ON CERAMICS](https://doi.org/10.1179/sic.2000.45.s2.021)  Mills 等,2000,Studies in Conservation
- ✓ [UV-Visible and IR Spectroscopic Studies of Gamma Irradiated Transition Metal Doped Lead Silicate Glasses](https://doi.org/10.1007/s12633-009-9029-8)  Khalil 等,2010,Silicon
- ✓ ⬛ [Understanding the blue color in antique mosaic mirrored glass from the Temple of the Emerald Buddha, Thailand](https://doi.org/10.1002/xrs.2586)  Klysubun 等,2015,X-Ray Spectrometry
- ✓ [Characterization of sodium lead silicate glasses containing low and high levels of Fe2O3 and effect of its replacement for Na2O](https://doi.org/10.1007/s10854-017-6704-1)  Morsi 等,2017,Journal of Materials Science: Materials in Electronics
- ✓ [The origins of imperial yellow glazed porcelain in the Ming Dynasty (1,368 to 1,644) China: Technical comparison to low‐fired tile with yellow glaze](https://doi.org/10.1111/arcm.12692)  Hou 等,2021,Archaeometry
- ✓ ⬛ [Non-Invasive Study of Gold Nanoparticles in Famille rose and Ruby-Back Qing Porcelain by Luminescence, Low-Wavenumber Raman Scattering and pXRF](https://doi.org/10.3390/app152212265)  Colomban 等,2025,Applied Sciences
- ✓ ⬛ [Non-Destructive Ellipsometric Analysis of the Refractive Index of Historical Enamels](https://doi.org/10.3390/ma18051137)  Palomar 等,2025,Materials
- ✓ [Arsenic, gold and smalt: Color-forming mechanisms and manufacturing techniques of Qianlong-period famille-rose architectural tiles from Yuanmingyuan](https://doi.org/10.1016/j.jas.2026.106522)  Ping 等,2026,Journal of Archaeological Science

</details>

<details><summary><code>yanzhi3</code>(4 条)</summary>

- ✓ ⬛ [Investigation of the Pigments and Glassy Matrix of Painted Enamelled Qing Dynasty Chinese Porcelains by Noninvasive On-Site Raman Microspectrometry](https://doi.org/10.3390/heritage3030050)  Colomban 等,2020,Heritage
- ✓ ⬛ [Nanoscale engineering of gold particles in 18th century Böttger lusters and glazes](https://doi.org/10.1073/pnas.2120753119)  Chari 等,2022,Proceedings of the National Academy of Sciences
- ✓ ⬛ [Emulation and technological adaptation in late 18th‐century cloisonné‐style Chinese painted enamels](https://doi.org/10.1111/arcm.12757)  Norris 等,2022,Archaeometry
- ✓ [Persimmon and Peonies: Orange-Colored Glass and Enamels from the Qing Imperial Workshops](https://doi.org/10.1086/728880)  Bellemare 等,2023,Metropolitan Museum Journal

</details>

<details><summary><code>yanzhi4</code>(1 条)</summary>

- ✓ [Simulated reflection spectra of copper red glaze and gold ruby-pink enamel](https://doi.org/10.1140/epjp/s13360-025-06287-z)  Li 等,2025,The European Physical Journal Plus

</details>

<details><summary><code>yanzhi5</code>(7 条)</summary>

- ◐ [10.11896/cldb.20070163](https://doi.org/10.11896/cldb.20070163)
- ◐ [10.13957/j.cnki.tcxb.1994.02.003](https://doi.org/10.13957/j.cnki.tcxb.1994.02.003)
- — [10.13957/j.cnki.txcb.1994.02.003](https://doi.org/10.13957/j.cnki.txcb.1994.02.003)
- ✓ [Measurement of Translucency of Porcelain Bodies](https://doi.org/10.2109/jcersj.104.877)  SUGIYAMA 等,1996,Journal of the Ceramic Society of Japan
- ✓ [Transmittance Analysis for the Translucent White Porcelain of the Xing Kiln, China](https://doi.org/10.1111/arcm.12460)  Wang 等,2019,Archaeometry
- ✓ ⬛ [WHAT IS THE TRUE WIDTH AND HEIGHT OF THE SPECULAR PEAK ACCORDING THE LEVEL OF GLOSS?](https://doi.org/10.25039/x46.2019.op88)  Rabal 等,2019,PROCEEDINGS OF the 29th Quadrennial Session of the CIE
- ✓ ⬛ [Investigation of the effects on ink colour of lacquer coating applied to the printed substrate in the electrophotographic printing system](https://doi.org/10.2478/pjct-2021-0014)  Sönmez 等,2021,Polish Journal of Chemical Technology

</details>

<details><summary><code>yinxing</code>(24 条)</summary>

- ✓ [ANASTOMOSES IN THE VENATION OF GINKGO BILOBA](https://doi.org/10.1002/j.1537-2197.1959.tb07030.x)  Arnott,1959,American Journal of Botany
- ✓ [Shoot Growth and Heterophylly in Ginkgo biloba](https://doi.org/10.1086/336526)  Critchfield,1970,Botanical Gazette
- ✓ [Morphological study on early ontogeny of theGinkgo leaf](https://doi.org/10.1007/bf02489482)  Hara,1980,The Botanical Magazine Tokyo
- ✓ [Responses of leaf anatomy to light environment in the tree fern Cyathea caracasana (Cyatheaceae) and its application to some ancient seed ferns](https://doi.org/10.2307/3515296)  Arens,1997,PALAIOS
- ✓ [The origin of the diversity of leaf venation pattern](https://doi.org/10.1002/dvdy.20908)  Fujita 等,2006,Developmental Dynamics
- ✓ [PROSPECT-4 and 5: Advances in the leaf optical properties model separating photosynthetic pigments](https://doi.org/10.1016/j.rse.2008.02.012)  Feret 等,2008,Remote Sensing of Environment
- ✓ [Structural and hydraulic correlates of heterophylly in Ginkgo biloba](https://doi.org/10.1111/j.1469-8137.2010.03476.x)  Leigh 等,2010,New Phytologist
- ✓ [PROSPECT-D: Towards modeling leaf optical properties through a complete lifecycle](https://doi.org/10.1016/j.rse.2017.03.004)  Féret 等,2017,Remote Sensing of Environment
- ✓ [The hydraulic architecture of Ginkgo leaves](https://doi.org/10.3732/ajb.1700277)  Carvalho 等,2017,American Journal of Botany
- ✓ [Phloem networks in leaves](https://doi.org/10.1016/j.pbi.2017.12.007)  Carvalho 等,2018,Current Opinion in Plant Biology
- ✓ [Competition for epidermal space in the evolution of leaves with high physiological rates](https://doi.org/10.1111/nph.15476)  Baresch 等,2018,New Phytologist
- ✓ [Physiological and Transcriptomic Changes During Autumn Coloration and Senescence in Ginkgo biloba Leaves](https://doi.org/10.1016/j.hpj.2020.11.002)  Li 等,2020,Horticultural Plant Journal
- ✓ [PROSPECT-PRO for estimating content of nitrogen-containing leaf proteins and other carbon-based constituents](https://doi.org/10.1016/j.rse.2020.112173)  Féret 等,2021,Remote Sensing of Environment
- ✓ [Geometric and topological approaches to shape variation in Ginkgo leaves](https://doi.org/10.1098/rsos.210978)  Hang 等,2021,Royal Society Open Science
- ✓ [Light scattering in stacked mesophyll cells results in similarity characteristic of solar spectral reflectance and transmittance of natural leaves](https://doi.org/10.1038/s41598-023-31718-1)  Xu 等,2023,Scientific Reports
- ✓ [Red pigments in autumn leaves of Norway maple do not offer significant photoprotection but coincide with stress symptoms](https://doi.org/10.1093/treephys/tpad010)  Mattila 等,2023,Tree Physiology
- ✓ ⬛ [Strong increase of photosynthetic pigments and leaf size in a pruned Ginkgo biloba tree](https://doi.org/10.32615/ps.2023.020)  LICHTENTHALER 等,2023,Photosynthetica
- ✓ [Formation mechanism and regulation analysis of trumpet leaf in Ginkgo biloba L](https://doi.org/10.3389/fpls.2024.1367121)  Li 等,2024,Frontiers in Plant Science
- ✓ [Seasonal Variation of Polyphenols and Pigments in Ginkgo (Ginkgo biloba L.) Leaves: Focus on 3′,8″-Biflavones](https://doi.org/10.3390/plants13213044)  Jurčević Šangut 等,2024,Plants
- ✓ [Coupling PROSPECT with Prior Estimation of Leaf Structure to Improve the Retrieval of Leaf Nitrogen Content in Ginkgo from Bidirectional Reflectance Factor Spectra](https://doi.org/10.34133/plantphenomics.0282)  Zhou 等,2024,Plant Phenomics
- ✓ [A novel ChlF-free leaf spectra dataset and the PROSPECT-DP model code](https://doi.org/10.5281/zenodo.12564322)  Liu 等,2024,Zenodo
- ✓ [Large-scale non-destructive crown-level assessment of Ginkgo pigments via hyperspectral and machine learning techniques](https://doi.org/10.1186/s13007-025-01439-9)  Yang 等,2025,Plant Methods
- ✓ [Phenological, Physiological, and Ultrastructural Analyses of ‘Green Islands’ on Senescent Leaves of Norway Maple (Acer platanoides L.)](https://doi.org/10.3390/plants14060909)  Macioszek 等,2025,Plants
- ✓ [Phenology-Dependent Sex Identification in Mature Ginkgo biloba Using Hyperspectral Imaging](https://doi.org/10.3390/plants15152255)  Zhao 等,2026,Plants

</details>

<details><summary><code>yinxing2</code>(2 条)</summary>

- ✓ [Reflectance and transmittance spectra of leaves and shoots of 22 vascular plant species and reflectance spectra of trunks and branches of 12 tree species in Japan](https://doi.org/10.1007/s11284-013-1096-z)  Noda 等,2013,Ecological Research
- ✓ [Spectral measurement of daylights and surface properties of natural objects in Japan](https://doi.org/10.1364/oe.441063)  Morimoto 等,2022,Optics Express

</details>

<details><summary><code>yinxing3</code>(7 条)</summary>

- ✓ [Autumn Leaves of Ginkgo biloba L.: Optical Properties, Pigments and Optical Brighteners](https://doi.org/10.1111/j.1438-8677.1992.tb00261.x)  Matile 等,1992,Botanica Acta
- ✓ ⬛ [HyperART: non-invasive quantification of leaf traits using hyperspectral absorption-reflectance-transmittance imaging](https://doi.org/10.1186/s13007-015-0043-0)  Bergsträsser 等,2015,Plant Methods
- ✓ [Exploring the Optical Properties of Leaf Photosynthetic and Photo-Protective Pigments In Vivo Based on the Separation of Spectral Overlapping](https://doi.org/10.3390/rs12213615)  Zhang 等,2020,Remote Sensing
- ✓ [Living and fossil Ginkgo leaves](https://doi.org/10.5061/dryad.7h44j0zsj)  Mander 等,2021,Dryad
- ✓ [PROSPECT-PMP+: Simultaneous Retrievals of Chlorophyll a and b, Carotenoids and Anthocyanins in the Leaf Optical Properties Model](https://doi.org/10.3390/s22083025)  Zhang 等,2022,Sensors
- ✓ [New 3-D Fluorescence Spectral Indices for Multiple Pigment Inversions of Plant Leaves via 3-D Fluorescence Spectra](https://doi.org/10.3390/rs16111885)  Tian 等,2024,Remote Sensing
- ✓ [A machine-learning–powered spectral-dominant multimodal soft wearable system for long-term and early-stage diagnosis of plant stresses](https://doi.org/10.1126/sciadv.adw7279)  Jiang 等,2025,Science Advances

</details>

<details><summary><code>yinxing4</code>(5 条)</summary>

- ✓ [Leaf Optical Traits collected at the University of Saskatchewan (LOTUS)](https://doi.org/10.20383/103.0606)  Peters, Reisha D 等,2022,Federated Research Data Repository / dépôt fédéré de données de recherche
- ✓ [Machine learning-based spectral and spatial analysis of hyper- and multi-spectral leaf images for Dutch elm disease detection and resistance screening](https://doi.org/10.1016/j.aiia.2023.09.003)  Wei 等,2023,Artificial Intelligence in Agriculture
- ✓ [A new dataset of leaf optical traits to include biophysical parameters in addition to spectral and biochemical assessment](https://doi.org/10.1016/j.rse.2024.114424)  Peters 等,2024,Remote Sensing of Environment
- ✓ [A broadband hyperspectral image sensor with high spatio-temporal resolution](https://doi.org/10.1038/s41586-024-08109-1)  Bian 等,2024,Nature
- ✓ [Hyperspectral Dataset](https://doi.org/10.57760/sciencedb.18287)  Liheng Bian,2024,Science Data Bank

</details>

<details><summary><code>yohen</code>(10 条)</summary>

- ◐ ⬛ [10.11362/jcssjclayscience.ms-22-5](https://doi.org/10.11362/jcssjclayscience.ms-22-5)
- ◐ [10.34360/00007472](https://doi.org/10.34360/00007472)
- ✓ [Visible and ultraviolet optical properties of single-crystal and polycrystalline hematite measured by spectroscopic ellipsometry](https://doi.org/10.1364/josa.71.000932)  Chen 等,1981,Journal of the Optical Society of America
- ✓ [Learning from the past: Rare ε-Fe2O3 in the ancient black-glazed Jian (Tenmoku) wares](https://doi.org/10.1038/srep04941)  Dejoie 等,2014,Scientific Reports
- ✓ [Imitation of ancient black-glazed Jian bowls (Yohen Tenmoku): Fabrication and characterization](https://doi.org/10.1016/j.ceramint.2016.06.027)  Li 等,2016,Ceramics International
- ✓ ⬛ [Simple ALD process for ε-Fe2O3 thin films](https://doi.org/10.1063/1.4983038)  Tanskanen 等,2017,APL Materials
- ✓ ⬛ [Mechanisms of pattern and colour generation of Chinese Tianmu glaze](https://doi.org/10.1039/c9ra06870h)  Shi 等,2019,RSC Advances
- ✓ ⬛ [High‐Quality Magnetically Hard ε‐Fe2O3 Thin Films through Atomic Layer Deposition for Room‐Temperature Applications](https://doi.org/10.1002/adem.202201262)  Jussila 等,2022,Advanced Engineering Materials
- ✓ [Angle dependence of Jian bowl color and its coloring mechanism](https://doi.org/10.1016/j.jeurceramsoc.2021.10.057)  Chen 等,2022,Journal of the European Ceramic Society
- ✓ [Phase-separated Tenmoku “Blue” glaze: Microstructure and coloring mechanism](https://doi.org/10.1016/j.jeurceramsoc.2023.05.051)  Feng 等,2023,Journal of the European Ceramic Society

</details>
