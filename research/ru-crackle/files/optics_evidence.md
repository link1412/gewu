# 裂缝光学证据补充（2026-10-29）

本笔记供合并进 `report.md`。推荐建模方向是“窄开口的三维釉内裂面 + 随角度改变的反射 + 局部污染/腐蚀”，并将表面白带的**可见宽度**与裂缝的**法向开口**分开。完成标准：不把玻璃实验数值当汝窑实测；不把倾斜面、薄膜、微崩口、剥层四种不同结构画成同一个现象；每个机制能指出可观察的判别方式。

## 已核实的原始或第一方资料

| 文献与定位 | 实测/作者结论 | 对汝窑的意义与边界 |
|---|---|---|
| George D. Quinn, *Fractography of Ceramics and Glasses*, 2nd ed. (2016), NIST SP 960-16e2, §4.9, 印刷页 **4-28**。[NIST PDF](https://nvlpubs.nist.gov/nistpubs/specialpublications/NIST.SP.960-16e2.pdf)；[NIST全文入口](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=920070)。旧版同节为 **4-27**，不可混用页码。 | 作者总结：尚未使器物分离的裂缝，面间距离可能小于光波长，显微镜下也可能看不见；迅速重新闭合可封住空气袋，玻璃–空气界面的反射会使空气袋显现；某些彩色反光仅特定角度可见。**未给统一开口量值，也未把所有彩反光定为薄膜干涉。** | 说明“有裂面”不等于“永远可见的黑槽”；照片中断续的线也可能仍连续。这里是玻璃断口学总结，不能推出所有汝窑裂缝均亚微米。 |
| Burghard, Zimmermann, Rödel, Aldinger, Lawn, “Crack opening profiles of indentation cracks in normal and anomalous glasses,” *Acta Materialia* **52 (2004), 293–297**, DOI [10.1016/j.actamat.2003.09.014](https://doi.org/10.1016/j.actamat.2003.09.014)。[参与作者所属NIST条目](https://www.nist.gov/publications/crack-opening-profiles-indentation-cracks-normal-and-anomalous-glasses)；[全文镜像](https://citeseerx.ist.psu.edu/document?doi=1c90e081b9a491827102617f7a5b61156528da27&repid=rep1&type=pdf)。 | p.294 实验：钠钙与硼硅玻璃维氏压痕，室温 **25 °C、47% RH、保载15 s**；放置 **2 d** 后测。AFM通常精度约 **15 nm**；近尖端3×3 μm扫描用5–10 nm半径探针，精度约 **5 nm**。Fig.2画的是**总开口2u**；Fig.3/4纵轴u为半开口。 | 证实玻璃裂缝可以用纳米级COD量测，且开口随距尖端位置变化。没有从不可清楚读图的曲线臆报“正常新裂缝宽X”。上述精度数字不是裂缝宽度。其压痕残余应力、材料、放置时间均不同于汝窑釉。 |
| Motomura, Imai, Saimoto (2009), “In-Situ Observation of Propagating-Crack Front Geometry in Thermal Stress Cleaving of Thin Glass Plates,” *日本機械学会論文集A* **75(755):925–932**，DOI [10.1299/kikaia.75.925](https://doi.org/10.1299/kikaia.75.925)。[原刊PDF](https://www.jstage.jst.go.jp/article/kikaia1979/75/755/75_KJ00005652786/_pdf)。 | 以干涉条纹原位量测热应力割断的钠钙薄玻璃裂缝前缘与COD。p.928 Eq.(1)的 **δ是半开口**，Fig.5为不同热源移动速度下的开口轮廓。 | 原始实验确实以裂缝两面的光干涉量测开口；可证明“新裂缝会有光干涉”并非仅类比肥皂膜。当前PDF截图缓存失败，**未核实Fig.5坐标单位与逐点数值，不能从OCR报定量开口。** |
| Sekino & Shimizu (2008), “Production of Natural Cracks With Various Shapes in the Heat Resisting Glass Plates and Evaluation of its Crack Opening Displacement by Optical Interferometry,” *実験力学* **8(1):59–64**，DOI [10.11395/jjsem.8.59](https://doi.org/10.11395/jjsem.8.59)。[原刊](https://www.jstage.jst.go.jp/article/jjsem/8/1/8_1_59/_article/-char/en)。 | 作者先用牛顿环校验白光COD测量，再以反复加热/冷却在耐热玻璃中生成边裂缝、1/4椭圆和半椭圆自然裂缝，并观察干涉条纹。 | 是白光观察裂缝干涉的直接实验。没有据摘要报汝窑开口数。 |
| Wiederhorn et al., “Roughness of glass surfaces formed by sub-critical crack growth,” *J. Non-Crystalline Solids* **353 (2007):1582–1591**, DOI [10.1016/j.jnoncrysol.2007.01.029](https://doi.org/10.1016/j.jnoncrysol.2007.01.029)。[原刊摘要](https://www.sciencedirect.com/science/article/abs/pii/S0022309307001883)。 | p.1582摘要：水中双悬臂梁、AFM；裂速约 **10⁻¹⁰–10 m/s**。二氧化硅断面RMS粗糙度约 **0.5→0.35 nm**；钠钙硅酸盐约 **2→0.7 nm**；测量窗口 **(0.5 μm)²–(5 μm)²**。Fig.1约1 μm方区高差约 **2 nm**（这是峰谷高度变化，非RMS）。 | 新鲜玻璃裂面可极光滑，不能先验规定所有裂面都是白粉状漫射面；汝窑多相釉中的晶体、气泡偏转、老化腐蚀可能造成更大粗糙度，但须独立量测。NIST条目把该论文登记为2008且少一作者，以原刊2007卷页为准。 |
| Harvard Natural Sciences Lecture Demonstrations, [Frustrated Total Internal Reflection](https://sciencedemonstrations.fas.harvard.edu/presentations/frustrated-total-internal-reflection)，网页“How it works / Comments”（无印刷页码）。 | 第一方演示：两个45°棱镜背靠背，逐渐挤薄中间气膜，光由全反射逐渐转为透射；接近接触时两个玻璃通过倏逝场耦合。作者说明此演示**未量气膜厚度**。指纹未接触的沟纹显银白，接触处全反射受破坏。 | 空气夹层过窄时不能按两个独立界面各自100%全反射处理。银光是角度与气隙的光学效果，不意味着金属颗粒。 |
| You, Wang, Wang, Pan, Zhou (南京大学), “A new method to demonstrate frustrated total internal reflection in the visible band,” *American Journal of Physics* **76 (2008):224–228**, DOI [10.1119/1.2825389](https://doi.org/10.1119/1.2825389)。 | 作者摘要报告以牛顿环中心附近约 **100 nm** 气膜演示FTIR，强度分布实验符合理论。[作者上传原文预览](https://www.researchgate.net/publication/243493016_A_new_method_to_demonstrate_frustrated_total_internal_reflection_in_the_visible_band)。 | 原刊正文尚未取得，100 nm只按论文摘要量级引用；不据预览报更细实验误差。 |
| Optical Society of America / FSU, [The Refraction of Light](https://osa.magnet.fsu.edu/teachersparents/articles/refractionoflight.html)，§“Total Internal Reflection”，Fig.6。 | 教学第一方来源给出 θc=arcsin(n低/n高)，玻璃 **n=1.5** 对空气临界角约 **41°**；正文“4%”为正常入射单玻璃–空气界面反射。 | n=1.5是教学玻璃假设，**不是清凉寺釉折射率实测**。精算41.81°见下表。 |
| OpenStax, *College Physics 2e*, [§27.7 Thin Film Interference](https://openstax.org/books/college-physics-2e/pages/27-7-thin-film-interference)，特别是显微载玻片气楔示意、Eq.27.40–43。 | 教材解释气楔两面反射的相位差，接触处暗，白光下颜色随间距和观察角改变；气层增厚时角度平均更容易使条纹消失。 | 标准薄膜机制；不能把“裂缝存在”直接等同“照片必有虹彩”。 |

## 计算值：仅作可证伪的渲染尺度估算

以下数值**全部是本次推算**，输入为均匀透明玻璃n=1.50、空气n=1.00、真空波长550 nm；并未测量Cleveland 1957.40或汝窑釉。

| 问题 | 公式与结果 | 使用范围 |
|---|---|---|
| 单独玻璃–空气面什么时候银亮？ | θc=asin(1/1.5)=**41.81°**；正常入射R=((1.5−1)/(1.5+1))²=**4.00%**。 | 入射角是**玻璃内部光线相对裂面法线**的角，不是相机对器物表面的角。大于临界角且第二釉面足够远时才趋近100%反射。 |
| 一个窄气缝能否当完全镜面？ | 倏逝场振幅1/e深度 ℓ=λ/[2π√(n玻²sin²θ−n气²)]。θ=45°：**247.6 nm**；60°：**105.6 nm**。 | 这是场衰减尺度，不是“超过该宽度即全反射”的硬阈值。气隙仅几十到几百纳米时需三层薄膜/FTIR，两个独立几何光学界面会高估白边。 |
| 多薄会有干涉色？ | 正常入射玻璃–空气–玻璃，接触极限反射相消；第一反射极大d=λ/4：550 nm对应 **137.5 nm**；400–700 nm对应 **100–175 nm**。同色相邻极大间距Δd=λ/2：550 nm为 **275 nm**。 | 这是平行平滑气膜、低于临界角、相干两光路的薄膜解；不是实际釉裂宽的测量。宽带、粗糙、曲面、像素/照明角度平均及体散射都会削弱虹彩。不能与超临界角FTIR公式混算。 |
| 白边为什么可远宽于缝口？ | 斜裂面从釉面延至深度h，截面上面偏离釉面法线φ，几何水平投影约w=h·abs(tanφ)。例假设h=**0.5 mm**、φ=**30°**，得 **0.289 mm**。 | 示范“面深度投影”和“面间开口”是两个量；未含折射、照明遮挡与视角，所以不能直接拟合实物白边宽。无须以0.289 mm的空槽生成同宽亮带。 |

要回答“刚开裂缝究竟微米还是更小”，现有证据支持的是**两者都可能；同一裂缝沿深度/距尖端位置也不同**。裂缝宽是应力释放后的位移场，受釉厚、应力、基底约束、深度、时间、水/污染物及重新接触影响，并非一种玻璃的固定材料常数。上述AFM精度与光学计算不能替代汝窑截面数据。

## 两级网络为何第一级更显

可核实的网络形成证据：Bohn, “Hierarchical crack patterns: a comparison with two-dimensional soap foams,” *Colloids and Surfaces A* **263 (2005):46–51**, DOI [10.1016/j.colsurfa.2004.11.013](https://doi.org/10.1016/j.colsurfa.2004.11.013)，摘要与Fig.1：釉裂层级来自**先后形成并不可重新排列**的裂缝。Lahlil, Xu, Li (2015), *J. Cultural Heritage* **16:401–412**, DOI [10.1016/j.culher.2014.10.003](https://doi.org/10.1016/j.culher.2014.10.003)，摘要：以受控仿制釉体研究时间进程，相对釉/胎厚度及烧成温度、气氛影响最终纹样。

但“粗一级=必定更宽、更深”没有由上述文献摘要证明。对1957.40可以提出几种**待验假设**：先形成的裂缝开口更大或裂面更深、截获更多光；已有裂缝释放附近应力，后来细分裂缝开口较小；早裂缝经历更多渗染/腐蚀。二维线长本身不等于截面开口，一级长线也不必全部比二级亮。可检验：先按T形终止关系划形成层级，再分别统计开口/深度/亮度；不能先以黑白粗细划层级，再宣布层级导致粗细。

## “白边、层叠、鱼鳞、冰裂、蟹爪”的物理解释分级

1. **有一般光学实验支持、在汝窑上仍需判别：**倾斜的气隙裂面可把照明反射向相机；局部达到TIR时宽而银亮；小气隙的FTIR/薄膜反射改变亮度或颜色。它预言转动器物或灯时白带的位置、宽度、亮度明显变化，湿润/折射率匹配会改变反光。可在玻璃或现代对照片上检验；不建议为此向馆藏真器加液。
2. **有材料学可能性、尚未找到汝窑定量光学验证：**气泡/晶体使裂面偏折、多面阶梯；裂口小缺损、腐蚀粗化、裂面微晶或污染层产生较宽角度散射；与近釉面平行的横裂或剥层也可能出现鳞片般片状反射。**“看起来层叠”不足以证明存在真实多层剥离。**必须由截面/OCT/CT显示其位置，再关联光学照片。新鲜均质玻璃纳米粗糙度很小，不能凭“裂面总是粗糙”锁定漫反射。
3. **仅形态/鉴赏词：**蟹爪主要指表面支叉、鱼鳞指叠错鳞片轮廓、冰裂指似冰片明暗分块；这些词没有一一对应的唯一裂缝宽度/倾角/横裂深度。名称不能替代测量。

鉴定类说法，以下与实验分开：

- 《一篇文章帮你读懂：关于汝窑的斜开片现象！》[搜狐2020转载](https://www.sohu.com/a/399259277_100146515)，无页码/无实验方法：声称白边可宽约 **0.5–1 mm**，转动后变窄或消失；数条不规则平行曲线与直开片围出鱼鳞形。它把该视觉现象解释为斜开片；此0.5–1 mm是**作者说的可见白带宽**，不是裂缝开口，更不是SEM测量。未见原始校准图、样本编号、截面角度。
- 严家宽《对一件北宋汝窑瓷盘的显微观察》[雅昌2024](https://amma.artron.net/observation_shownews.php?newid=1129422)，作者自测/鉴定文章、器物来源可信度未独立核实：声称一般开口 **0.002 mm (=2 μm)**、局部剥失处约 **0.014 mm (=14 μm)**、部分被表层遮盖约 **0.001 mm (=1 μm)**。无经过论证的测量不确定度；把脏色与“出窑时旧裂/近百年新裂”对应的年代判断**不能当裂缝形成时间实测**。这些数值不得与清凉寺出土样本论文量值合并统计。

## 文件与授权

**没有把远程PDF冒充为已下载文件**。本文件是研究笔记。原始URL已列全。

- NIST Quinn指南：美国联邦政府出版物，但书中部分图片来自署名第三方；不能把整书所有图都笼统标CC0。若用图，检查具体caption。§4.9为文字，无图片比例尺。
- J-STAGE Motomura：页面标“FREE ACCESS”，版权 **©2009 日本機械学会**；Sekino为 **©2008 日本実験力学会**。免费获取不自动授予商业再用；需保留原图版权与图号。
- Burghard：原刊Elsevier，镜像可读不等于版权转让；ResearchGate标签显示CC BY-NC-ND 3.0，但未在原刊独立核实，故不把它当确定许可。图为坐标曲线/AFM示意，不能另加伪比例尺。
- Wiederhorn 2007：Elsevier，未核实开放再用许可；若保留全文仅研究参考。Fig.1影像尺寸约1 μm见正文，不等于独立读出图上的标尺。
- Harvard实验与OSA/FSU：网页未声明开放图像许可；OSA页明确©2008 All Rights Reserved。只作研究参照。
- OpenStax College Physics 2e：教材网页通用许可CC BY 4.0（图若有独立第三方credit以其说明为准）；本笔记只引用文字原理，未复制图。
- 搜狐/雅昌：未声明开放许可，非校准科研图，授权未知；只作作者说法参考。


