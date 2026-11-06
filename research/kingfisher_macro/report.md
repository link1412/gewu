# 翠鸟蓝羽与点翠：程序化微距镜头参照

核查日期：2026-11-06。用途：确定几何尺度、材质层次、方向变化和老件细节；只提供照片链接，不打包图片。

**推荐方向：建立“羽枝几何＋散射材质＋裁片与底托”的分层模型。** 下列数据支持以平行条纹为主体，并将纳米结构、光照和损伤分别控制。

完成标准：尺寸注明物种／部位和测量对象，波长注明照明与检测几何，照片注明图号与许可；建模假设单列。**本次未补齐的两项是：匹配点翠软羽的羽小枝宽度及间距，以及角度扫描的精确波长终点。** 以下明确保留缺口，不以其他鸟种或纳米孔距代替。

## 1. 羽枝、羽小枝与发色结构

### 1.1 先统一“宽度”和“间距”

本报告中，羽枝 barb 指羽轴两侧的一级分枝，其主干也称 ramus；羽小枝 barbule 是羽枝上的次级分枝。[Lee et al. 2021][s5] 建模时另定义主干外宽 `w`、相邻主干净空 `g`、中心距 `p`；近似平行且同宽时 `p = w + g`。沿轴计数得到的分枝间距与俯视条纹间距，需要投影换算。

### 1.2 可核实的尺寸（统一用 µm）

| 对象／部位 | 数值 | 证据与使用边界 |
|---|---:|---|
| 点翠软羽：完整羽枝直径 | **约 40–70 µm** | 故宫显微观察；文中未将这些材料鉴定到具体翠鸟物种，不能标成全部是 *Alcedo atthis* 的物种统计值。[谷岸等，p.361、图1][s3] |
| 清代花鸟挂屏翠羽：羽枝直径 | **约 40 µm** | 文物样本，现代翠鸟羽作对照；羽小枝短，从背面不明显。不是所有部位的通用宽度。[Gu et al. 2021，Fig.5][s4] |
| *A. atthis* 背羽：海绵层截面宽 `Wkl` | 深蓝 **18.73**；浅蓝 **23.57**；青 **39.18 µm** | 内部海绵层的宽，**不是整根羽枝外宽**。[Kang et al. 2025，§2.2、Fig.3][s2] |
| 同上：海绵层截面厚 `Tkl` | **18.94／19.56／20.76 µm** | 颜色组顺序同上；不是羽枝间距。[Kang et al. 2025，§2.2][s2] |
| 同上：外皮 cortex 厚度 | **3.25–4.45 µm** | 外皮包覆海绵层，不可当羽小枝宽度。[Kang et al. 2025，§2.2、Table S1][s2] |
| *A. atthis* 背／尾羽：海绵纳米结构特征距离 | **0.211 ± 0.009／0.187 ± 0.007 µm** | SEM 的傅里叶分析结果；是内部相关尺度，**不是羽枝或羽小枝的间距**。[Stavenga 2011，p.3961、Fig.4][s1] |
| *A. atthis* 蓝色背／尾羽：羽枝净空及中心距 | **未取得可靠、部位匹配数值** | 已核查正文没有给出可直接采用的统一数值；图中标尺本身不等于被摄结构宽度。[Stavenga，Fig.1、3][s1]、[Kang，Fig.3][s2] |
| 点翠软羽／普通翠鸟蓝色背羽：羽小枝外宽、净空及中心距 | **未取得可靠数值** | 可确认软羽羽小枝短小；硬羽两侧则有较长的暗色羽小枝。不能将硬羽的网格套给软羽。[谷岸等，p.361、图1][s3] |

**间距尤其需要区分“自然羽毛”和“点翠铺排”。** 点翠会裁片、拼接、重新安排羽枝疏密，因此成品条纹间距并不必然保留天然羽片的排列。故宫挂屏的实物研究确认疏密可用于调色，但未提供一套通用间距表。[Gu et al. 2021，Light blue / Violet area][s4]

若需要继续取得自然飞羽的密度，Pap et al. 的跨物种研究及原始数据包含普通翠鸟初级飞羽，方法分别按羽轴和羽枝长度计数。**本次未读取到补充文件中该物种的具体值；即使取得，也只适用于相应初级飞羽，不能视为点翠背部软羽。** 数据入口：[Pap et al. 2015][s10]、[Dryad 数据集][s11]。

### 1.3 蓝色在哪一层

- **普通翠鸟蓝色主色来自羽枝内部角蛋白／空气海绵结构的相干散射。** 羽小枝不是主要蓝色来源。[Lee et al. 2021，原论文摘要][s5]、[Kang et al. 2025，§2.2][s2]
- **外皮也反光。** cortex 有方向性反光，局部有薄膜谱振荡；较大面积平均后接近宽带反光。[Stavenga 2011，Fig.9][s1]
- **海绵之外还要保留黑色素所在区域。** 较新背羽截面研究区分外皮、海绵层及黑色素；不是一根通体透明或金属蓝的纤维。[Kang et al. 2025，Fig.3][s2]

对普通可见光微距，建议将内部纳米结构的影响放进散射材质；只有切面或“进入内部”的镜头才显式画孔道。SEM 截面不能直接当作完整羽枝的外表面纹理。[建模推论；结构依据：Kang，Fig.3–4][s2]

## 2. 角度变化：能确认的波长与不能混用的数据

“色相多少 nm”在这里指**反射谱峰值波长**，不等于屏幕 HSV 色相；宽峰、照明光谱和白色反光都会影响最终 RGB。Kang 等也将反射谱结合 D65 照明转换成色坐标，而非直接把峰值当成唯一颜色。[Kang et al. 2025，§2.1][s2]

| 实验 | 照明／观察条件 | 已核实结果 |
|---|---|---|
| Stavenga 2011：普通翠鸟背羽尖部 | 入射角 `θ = 0°`；检测角 `φ = 0°, 10°, …, 80°`；检测方向在包含羽枝长轴的平面中变化 | 检测角增大时峰值向短波移动；另有 `θ = 60°` 的扫描。**正文未列出 nm 两端点，本次未取得可读的曲线图像，不能声称已量出“X → Y nm”。** [pp.3963–3964、Fig.8][s1] |
| Meier et al. 2026：普通翠鸟参照羽毛 | 固定光源沿表面法线照明；沿羽枝方向平面改变检测角，以 15°递增 | **15°时峰值 523 nm**；30–75°时峰继续蓝移且主峰变宽。**正文未给出 75°终点数值。** [Results and Discussion，Fig.3a][s6] |
| Kang et al. 2025：普通翠鸟不同颜色背羽组 | 漫反射测量，比较不同样本组 | 深蓝 **471 nm**、浅蓝 **482 nm**、青 **500 nm**。这是**不同羽毛组之间**的差别，不是同一羽毛转动时的 471 → 500 nm。[§2.1、Fig.2C][s2] |

**对镜头的含义：** 窄束光下可显青绿向蓝的变化，漫射照明使角度效应平均、外观较稳定；“非虹彩”不等于定向测量中绝无峰移。[Stavenga 2011，Fig.7–8、Discussion][s1] 因此建议同时记录灯与相机方向。

**勿混用：570／550 nm 是背／尾羽积分谱长波侧半高位置，非峰值或角度端点。** [Stavenga 2011，p.3961][s1]

目前可以交付“已知起点＋蓝移方向＋角度范围”，不能交付经过核实的完整 nm 端点对。若要定量复现，应取得 Fig.8B 或 Meier Fig.3a 的可读原图／原始数据后数字化曲线，并保留部位、角度、峰宽和读图误差；本报告没有将未验证的近似公式输出伪装成实测数据。[待核查原图：Stavenga][s1pdf]、[Meier][s6]

## 3. 点翠怎样裁、怎样贴

以下是不同实物与工艺记录支持的做法，不能认定每件点翠都具有同一套层次。

1. **做托、划定纹样。** 金属框架和金属线构成纹样，羽毛贴入线条之间的凹处；首饰可用金、银及鎏金金属托。金属线是清楚可见的边界，而非整面蓝色下面不可见的装饰。[故宫“点翠”词条][s7]、[Met 实物材料记录][s14]
2. **将羽毛整理成可裁的小片。** Gu 等调查记录：羽毛背面朝上放在板上，背面刷胶，干后用刀从板上分离成羽片，再裁成所需形状并粘到支撑体。背胶先维持羽枝排列，贴托胶再固定裁片，两者功能不同；实物显微观察可见小片拼缝。[Gu et al. 2021，Layer 1–3][s4]
3. **胶不是单一配方。** MOCA 修复研究列出鱼鳔胶、其他蛋白胶及海藻胶等传统材料；该头饰光谱与蛋白质及植物类胶的参照谱相关，不能据此断言所有老件均使用纯鱼鳔胶。修复用现代胶也应与原胶分开记录。[MOCA／Devon Lee][s8]
4. **底也不一定是金属。** 故宫挂屏叶片的实例含翠羽、背胶／衬色、粘接胶、衬色和多层竹纸支撑，纸中夹铜条加固。其浅蓝区有黑色背胶，紫色区结合红衬；透过羽枝空隙可影响整体颜色。[Gu et al. 2021，Fig.3、12][s4]
5. **按纹理和图案安排方向。** 可以用片区方向变化和底层起伏构成纹样；故宫围屏有以纸条制作浮起纹理的实例。微距应保留片区内有序、片区之间转向的关系。[谷岸等，p.364、图6–7][s3]
6. **收边：裁形贴合、边角压实、修整多余羽料。** 传承人的现场操作记录显示，用剪刀沿纹理裁出花瓣、反复对托修剪，再以竹签沿边角按压；该记录用的是**现代染色鹅毛和白乳胶**，可参考手部操作与贴合方式，不能倒推古件胶配方。[中新网，肖玉妹工作室现场报道][s12]

**边缘建模取舍：** 对金属首饰，建议把裁断羽枝的端部收在金属线内侧，并保留极细的不齐；这是依据凹槽贴羽结构作的视觉推论。本次没有找到足以支持“所有古件都将羽片折回托背”或“统一由金属包边机械夹紧”的证据，不把这两种做法设为通例。[依据：故宫工艺定义][s7]；裁片边界可再比对下节照片。

## 4. 老件的磨损、缺损和“褪色”

| 现象 | 有来源支持的表现 | 对程序化微距的处理建议 |
|---|---|---|
| 胶层失效 | MOCA 头饰出现羽层不稳、分层、脱离与缺失，缺损处露出鎏金金属；部分金属饰件压瘪变形。[MOCA][s8]、[Lee 的 AIC 项目摘要][s9] | 局部翘边、薄片离底和阴影、成片露底；避免只把蓝色均匀调暗。 |
| 机械磨损 | 羽毛会受压、弯折、折断；结构色表面磨损可能造成颜色损失。[加拿大文物保护研究所 CCI][s13] | 在接触和凸起位置增加断枝、缺口、排列破坏，保留仍完整的蓝色区域；这是效果推演，不是已测磨损分布。 |
| 灰尘和油污 | 羽毛复杂表面容易截留尘粒及油性残留，清理也可能扰动细结构。[CCI，Pollutants][s13] | 让沉积进入沟缝与局部表面，造成斑驳遮蔽和反光变化；不要将每个暗点都解释成蓝色结构消失。 |
| 光照导致色变 | Paulson 对白胸／白喉翡翠 *Halcyon smyrnensis* 的实验中，未粘接羽毛总体较稳定；强 UVA 下更趋无色／灰。不能换算成普通翠鸟的固定“百年褪色率”。[Paulson 2018][s15] | 使用局部失彩或灰化；不要用统一年龄阈值触发全件褪色。 |
| 胶／修复材料改变外观 | 同项研究中，Paraloid B-72 样本更暗、蓝绿更饱和；实物黄绿斑没有在模拟样本中复现，原因仍待研究。[Paulson 2018][s15] | 黄绿斑可作为特定实物的参照特征，不能当作所有点翠必经的老化阶段。 |

**因此，老点翠可以既有鲜蓝残留，也有露底和失光。** “不含蓝色染料”不等于永不变化；胶、污染、结构损伤与光照要分别表现。这里没有足够证据把某件物品的黄绿外观单独归因于羽毛褪色。[综合依据：MOCA][s8]、[Paulson][s15]、[CCI][s13]

## 5. 照片与显微图链接（只作参照）

前四项最贴近微距／显微结构。表中“高分辨整件照”不冒充高倍显微照片。许可只按页面可核查声明填写；未明确开放许可的图片仍可访问参照，但不据此承诺可再发布。

| 优先级与链接 | 看什么／定位 | 类型与许可 |
|---|---|---|
| **1. [Gu et al. 2021，故宫挂屏原始论文][s4]** | **Fig.3**：破损、侧面和层次；**Fig.5**：古翠羽与现代对照的羽枝；**Fig.6**：海绵 SEM；**Fig.12**：疏密与衬色。网页各图可进入 Full size image。 | 真正显微照片。文章 **CC BY 4.0**，图片原则上包含在许可内，第三方另标除外；适合优先参照。 |
| **2. [谷岸等《从微观尺度看清代宫廷的点翠技法与色彩表现》PDF][s3]** | **p.361 图1**：软羽 300×、软／硬羽及鹅毛 115×对照；**p.362 图2**：衬色层；**p.363 图4**：成品条纹；**p.364 图7**：残片正、背、侧面。 | 彩色显微／局部照片。故宫公开 PDF，**未核实开放再用许可**。 |
| **3. [Lee et al. 2021 原论文][s5]／[可查看相关图的 Earth@Home 页面][s5images]** | 原论文 **Fig.1**：普通翠鸟海绵截面；**Fig.2**：背、尾、翼羽的正反面与放大细节。转载页将图放在 Feather colors in kingfishers 段。 | 光学与显微参照。转载页明确标这两幅论文图为 **CC BY-NC 4.0**；NC 限制需保留。原论文入口本次未能完整打开，图定位按转载图注核对。 |
| **4. [Stavenga 2011 作者机构 PDF][s1pdf]** | **Fig.3D–F**：羽枝、细胞、海绵，标尺 50／5／2 µm；**Fig.5–6**：彩色光学显微；**Fig.8**：角度谱。按图号定位。 | 光学与 SEM；**未核实 CC 许可**。标尺不等于羽枝直径。 |
| **5. [Kang et al. 2025 原论文][s2]** | **Fig.3A**：外皮／海绵／黑色素截面；**Fig.4A–C**：海绵纳米网络。 | SEM，非外表面彩色微距。网页标 Open Access；**本次未核实具体图片许可**。 |
| **6. [MOCA 头饰修复记录][s8]** | 页面中的 **Ornament 19 before/after**：羽层翘起与加固；**detached kingfisher feather pieces**：脱落裁片；**ornament 16 straight on/from the side**：原羽与仿补材料角度表现。 | 近距离修复照片，适合接缝、翘边、露底；未标定放大倍率，**未见明确开放许可**。 |
| **7. [Wikimedia：19 世纪点翠发簪][s16]** | Nalin Singapuri 拍摄，**3053 × 3053 px**；可放大看蓝色区域与金属轮廓。 | 高分辨整件照，**不是显微照**；作者上传，**CC BY-SA 4.0**。 |
| **8. [Met：Ornaments for a Headdress，15.95.182a–d][s14]** | 18–19 世纪，金、鎏金金属、翠羽、玻璃和宝石；页面 Enlarge Image 与多视图适合核对底托和构图。 | 馆藏器物照，**不是显微照**；页面明确 **Public Domain**。 |

补充原始图像来源：[Meier et al. 2026，Fig.2c–d][s6] 有点翠羽枝排布与普通翠鸟 SEM，Fig.3 是角度结果。文章标 **CC BY-NC-ND 4.0**；其中文物照片另署 Field Museum 及摄影者，需同时核对具体图的署名条件。[期刊许可页][s6license]

## 6. 给程序生成镜头的一套起始设定

下表是**作者提出的建模方案，不是新增生物测量**。选择点翠软羽，是因为它有可核查的完整羽枝直径和成品显微参照；现有证据尚不足以标定全部羽小枝几何及完整角度光谱。

| 项目 | 建议起点 | 依据／假设边界 |
|---|---|---|
| 可见几何 | 羽枝外宽先取 **50 µm**，在已报告 40–70 µm 范围内变化 | 范围来自点翠材料；50 µm 是建模选值，非普通翠鸟均值。[谷岸等][s3] |
| 条纹间距 | 先设净空 **5 µm**，得中心距 **55 µm**；另留疏密控制参数 | **5 µm 是视觉假设，无实测出处**。它不能被报告为自然羽枝间距。后续应用 Fig.5 或明确目标老件重新标定。 |
| 镜头尺度 | 例如横向视野 **2 mm**，约容纳 **36 个**上述条纹中心距 | 由 `2000/55 ≈ 36` 计算，属于镜头设计；需按条纹法向理解，不是天然密度测量。 |

建议按前述证据验收尺寸、发色层级、拼片、损伤和照明响应。没有标尺的照片只比形态，不从像素反推微米。

## 7. 文献与核查边界

- **Stavenga, D. G., Tinbergen, J., Leertouwer, H. L. & Wilts, B. D. (2011).** *Kingfisher feathers – colouration by pigments, spongy nanostructures and thin films*. **Journal of Experimental Biology 214:3960–3967**. [DOI][s1]；[作者机构全文][s1pdf]。
- **Kang, J. et al. (2025).** *Elucidating and Biomimicking the Coloration Mechanisms Responsible for the Vibrant Blue Hues of the Common Kingfisher*. **Advanced Optical Materials 13, 2402936**. [DOI／全文][s2]。
- **谷岸、孔艳菊、王娜、侯佳钰、李根（2021）。**《从微观尺度看清代宫廷的点翠技法与色彩表现》，**《故宫学刊》总第22辑，359–364**。[故宫文献页][s3landing]；[PDF][s3]。引用出版年 2021，不将文件上传的 2022 年当出版年。
- **Gu, A. et al. (2021).** *Analytical investigation of the feather decoration technique of a seventeenth to eighteenth century Chinese imperial hanging screen*. **Heritage Science 9, 82**. [全文／DOI 10.1186/s40494-021-00555-8][s4]。
- **Lee, E. et al. (2021).** *Microstructures in Blue Feathers of the Common Kingfisher*. **PNIE 2(1):21–25**. [DOI][s5]；[可核查摘要的 KCI 记录][s5abstract]。
- **Meier, M. C., de La Codre, H., Kokkori, M. & Katsaggelos, A. K. (2026).** *Investigating Structurally and Pigmentary Colored Featherworks via Noninvasive Methodologies*. **ACS Omega 11:26029–26036**. [DOI][s6]。本次主要通过期刊已索引正文核对；未声称从图中读出终点。
- **Paulson, M. (2018).** *Visible effects of adhesive and pressure on color in kingfisher feathers*. UCLA 学位论文，导师 Ellen Pearlstein。[论文库与结果摘要][s15]；[AIC 的研究入口][s15aic]。实验物种为 *H. smyrnensis*。
- **Pap, P. L. et al. (2015).** *Interspecific variation in the structural properties of flight feathers in birds indicates adaptation to flight requirements and habitat*. **Functional Ecology 29:746–757**。[DOI][s10]；[原始数据][s11]。仅作为后续查自然飞羽密度的入口，未提取数值。

**本次访问限制：** 网页正文与部分 PDF 的索引文本可读，但 PDF 截图未返回可视图像，浏览器查看服务不可用；本地下载也未成功。因此未进行像素量尺、曲线数字化或照片视觉鉴定。照片表中的倍率、图号和许可依据原文图注／页面说明；本报告没有下载参考照片，也没有生成镜头或声称完成渲染验证。



[s1]: https://doi.org/10.1242/jeb.062620
[s1pdf]: https://pure.rug.nl/ws/files/6770003/2011JExpBiolStavenga.pdf
[s2]: https://advanced.onlinelibrary.wiley.com/doi/10.1002/adom.202402936
[s3]: https://img.dpm.org.cn/Uploads/File/2022/03/09/u62282bfb2f0be.pdf
[s3landing]: https://www.dpm.org.cn/explode/others/257446.html
[s4]: https://www.nature.com/articles/s40494-021-00555-8
[s5]: https://doi.org/10.22920/PNIE.2021.2.1.21
[s5abstract]: https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003044231
[s5images]: https://evolution.earthathome.org/kingfishers/vce/museum-science/kingfisher-plumage/
[s6]: https://doi.org/10.1021/acsomega.6c02770
[s6license]: https://pubs.acs.org/doi/abs/10.1021/acsomega.6c02770
[s7]: https://www.dpm.org.cn/lemmas/244072.html
[s8]: https://www.mocanyc.org/collections/stories/conservation-treatment-of-a-tian-tsui-headdress-from-the-moca-collections-by-devon-lee/
[s9]: https://resources.culturalheritage.org/osg-postprints/still-got-the-blues-the-technical-study-and-conservation-treatment-of-a-tian-tsui-headdress/
[s10]: https://doi.org/10.1111/1365-2435.12419
[s11]: https://datadryad.org/dataset/doi:10.5061/dryad.1538t
[s12]: https://www.chinanews.com/cul/2021/04-02/9445955.shtml
[s13]: https://www.canada.ca/en/conservation-institute/services/preventive-conservation/guidelines-collections/feathers-quills-horn-keratinous-materials.html
[s14]: https://www.metmuseum.org/art/collection/search/60801
[s15]: https://escholarship.org/uc/item/7mb7f244
[s15aic]: https://resources.culturalheritage.org/osg-postprints/v25/paulson/
[s16]: https://commons.wikimedia.org/wiki/File:Tian-tsui_(kingfisher_feather)_hair_pins.jpg
