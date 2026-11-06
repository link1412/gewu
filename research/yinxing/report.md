# 秋黄银杏叶：光学、叶形与真实照片资料

检索与下载日期：2026-11-02。对象为 **Ginkgo biloba L.**；优先寻找仍在枝上或刚落下、保水的秋季黄叶。压干标本、长期干叶、转色叶与鲜黄叶分别标注。

## 使用结论与证据标记

推荐以 **PROSPECT-D 的反射率 R(λ) 与透射率 T(λ)** 作为叶肉光学起点，另用实际叶形、叶脉和上下表面资料控制几何与表面外观。PROSPECT-PRO 将干物质拆为蛋白质与其他碳基组分；本次目标没有必要仅为可见光黄叶外观增加这些未测参数。这是建模建议，不是银杏实测结论。[Féret et al., 2017, *Remote Sensing of Environment* 193:204–215, DOI:10.1016/j.rse.2017.03.004](https://doi.org/10.1016/j.rse.2017.03.004)；[Féret et al., 2021, *RSE* 252:112173, DOI:10.1016/j.rse.2020.112173](https://doi.org/10.1016/j.rse.2020.112173)。

**目前没有足够依据交付一组声称“实测秋黄银杏叶”的完整 PROSPECT 参数。** 本报告交付已核实的测量、可下载数据、照片及缺口，不给凭颜色挑选的参数预设，也不把普通绿叶的反演范围冒充黄叶测量。

证据性质统一使用：**实测**（原作者测量；仅有曲线时注明）、**引用**（本源引用另一研究，未核原测量）、**反演**（模型拟合输出）、**推断/换算**（公式、视觉判断或单位换算，说明前提）、**模型数据/设定**（模型系数、模拟范围与固定参数，不是实测叶片）。“没找到”表示本次未取得可核查的该项信息，不等于文献中绝对不存在。图上有数据但没有机器可读表时，只交图号，不读图估数。

PROSPECT 输出的是半球积分反射/透射，不是完整 BRDF/BTDF。官方实现说明指出，它不区分近轴/远轴解剖，也不能把叶夹的定向反射直接当作半球反射比较；同一套模型折射率也不等于已测得银杏角质层折射率。因此，照片里的高光、叶面起伏与背光脉纹不能只靠修改色素含量复现。[Féret & de Boissieu, `prospect` 官方教程，2026-11-01，“Brief introduction”, Fig.1 及简化假设列表](https://jbferet.gitlab.io/prospect/articles/prospect.html)。

## 1. 叶的光学

### 1.1 实测叶反射/透射谱

| 来源与具体位置 | 样品/测量 | 可交证据 | 限制、性质 |
|---|---|---|---|
| Ph. Matile, B. M.-P. Flach & B. M. Eller (1992), *Botanica Acta* 105(1):13–17, **Autumn Leaves of Ginkgo biloba L.: Optical Properties, Pigments and Optical Brighteners**, DOI [10.1111/j.1438-8677.1992.tb00261.x](https://doi.org/10.1111/j.1438-8677.1992.tb00261.x) | 秋季衰老银杏；摘要明确讨论可见与红外光学、叶绿素降解和类胡萝卜素保留 | 原文定位明确；PDF [直接链接](https://onlinelibrary.wiley.com/doi/pdf/10.1111/j.1438-8677.1992.tb00261.x) | 原站 PDF 403；未获正文，**图号、逐波长表、是否完整包含 R/T、波长上下限均未核实**。只能把光学结论写为原作者摘要报告，不能伪称看过图。 |
| Yao Zhang et al. (2022), *Sensors* 22(8):3025, **PROSPECT-PMP+: Simultaneous Retrievals of Chlorophyll a and b, Carotenoids and Anthocyanins in the Leaf Optical Properties Model**, DOI [10.3390/s22083025](https://doi.org/10.3390/s22083025), [PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9028795/), Table 2、§2.1–2.2 | 2015年9–12月浙江大学 LOPEX_ZJU；Table2 银杏 5片，成熟 M/衰老 S，SPAD 3.8–41.8；上表面 DHR/DHT，UV-3600积分球，240–2400 nm，约1 nm分辨率；HPLC分离色素，按单面叶面积归一 | **实测**成对叶R/T、色素的研究确实存在，且覆盖衰老银杏 | 没找到银杏单独谱图号/逐叶R/T表/参数表。Data Availability Statement: Not applicable；正文未提供公开原始表附件。SPAD不能当Cab。Table2物种栏写Ginkgo，未细写biloba。 |
| Kai Xu & Hong Ye (2023), *Scientific Reports* 13:4694, **Light scattering in stacked mesophyll cells results in similarity characteristic of solar spectral reflectance and transmittance of natural leaves**, DOI [10.1038/s41598-023-31718-1](https://doi.org/10.1038/s41598-023-31718-1), Fig.3b–e、Experiments/Characterizations | 合肥2020年7月12–19日成熟绿叶；银杏5片，来自不同个体；上表面方向–半球 R/T，DUV-3700积分球，透射垂直入射 | **实测**绿银杏 R/T：**Fig.3b，400–2500 nm**（已查看原图；橙色虚线为Ginkgo，反射读左轴、透射读右侧倒置轴；[原图](data/Xu_Ye_2023_Fig3.png)，CC BY 4.0）。Fig.3c厚度、3d色素/水/干物质、3e反演N | 没找到叶R/T数值附件。Supplementary1.xlsx（已下载）只有各物种提取液吸光度，Ginkgo sheet=400–1000nm、每1nm、5样本；不是叶透射。N是遗传算法反演，不是解剖实测。 |
| Zhengnan Zhao et al. (2026), *Plants* 15(15):2255, **Phenology-Dependent Sex Identification in Mature Ginkgo biloba Using Hyperspectral Imaging**, DOI [10.3390/plants15152255](https://doi.org/10.3390/plants15152255), [PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC13468224/), **Fig.1a–c**, §5.1–5.2 | 北京玉泉山25–30年成熟树；2025年3月开花、7月绿叶、11月黄叶；400–1000nm高光谱成像，卤素灯/暗箱/白黑参考；黄叶243片，绿叶1395片 | **实测反射**，Fig.1b绿叶、Fig.1c黄叶，分雌雄均值±SD；正文仅给黄叶NIR约0.50（作者粗略概述，不是逐波长表） | 不含透射；成像方向性反射不能直接当积分球DHR。Data Availability：合理请求；附表S1–S3是分类混淆矩阵指标，没有光谱表。 |
| Xin Yang et al. (2025), *Plant Methods* 21:130, DOI [10.1186/s13007-025-01439-9](https://doi.org/10.1186/s13007-025-01439-9), [全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC12533460/), **Fig.4–6**, Materials and methods | 3460银杏苗、590家系，10月底–11月20日四阶段；350–1000nm成像；乙醇提取测面积色素 | **实测**色素季节变化Fig.4、阶段色素统计Fig.5、原始反射示意Fig.6a | 是苗冠ROI光谱，不是单叶DHR/DHT；原始数据需合理请求；没有在表中给阶段Cab/Car精确值，本次不读图估值。 |

### 1.2 已下载的通用光谱库：物种核验结果

#### ANGERS

来源：S. Jacquemoud, L. Bidel, C. François, G. Pavan，2003，ANGERS Leaf Optical Properties Database；[EcoSIS原始数据页](https://data.ecosis.org/dataset/angers-leaf-optical-properties-database--2003-)；研究参考：Féret et al. (2008), *Remote Sensing of Environment* 112:3030–3043, DOI [10.1016/j.rse.2008.02.012](https://doi.org/10.1016/j.rse.2008.02.012)。

- 原始 `Angers2003_Metadata_Naming_and_Notes.xlsx` A1:A6：June2003、43species、276samples、last update 3Sep2013。
- 已下载 `data/ANGERS/Angers2003_Reflectance.xlsx` / `Transmittance.xlsx` / `Metadata.xlsx` / `Metadata_Naming_and_Notes.xlsx`。
- 光谱首三行是Sample_#/file/measurement_type，之后400–2450nm每1nm；不是400–2500nm。反射/透射数是0–1分数（例如0.0334），勿因EcoSIS页面单位字段写%再除100。
- `Metadata.xlsx` C列逐样本物种名，276有效样本、strip后43物种标签，**无Ginkgo**，已导出CSV与species_list.txt；审计在 `data/metadata_species_audit.json`。
- Notes row13：N由PROSPECT反演。Anth列-999是缺测，不能解释为0。
- EcoSIS许可字段 Other(Open)；无更具体CC条款，保留来源。
- 官方prospect R包下载入口代码：[download_leaf_db.R](https://gitlab.com/jbferet/prospect/-/raw/master/R/download_leaf_db.R)；指向GitLab myshareddata，直下429；最终通过EcoSIS API的公开资源直链成功。

#### LOPEX93

来源：B. Hosgood, S. Jacquemoud, G. Andreoli, J. Verdebout, A. Pedrini, G. Schmuck (1994)，JRC Report EUR16095EN，**Leaf Optical Properties Experiment93 (LOPEX93)**；[EcoSIS原始页](https://data.ecosis.org/dataset/leaf-optical-properties-experiment-database--lopex93-)。

- 完整报告、四xlsx已下载 `data/LOPEX/`。报告 §3：400–2500nm，每1nm；λ19/BaSO4积分球，上表面反射/透射。报告Appendix Table1（PDF第29页；页面图示Table1）完整拉丁物种表无Ginkgo；EcoSIS Metadata的330有效样本、46strip后物种标签也无Ginkgo。
- 注意论文常报45species，物种口径/文件版本不同；不要拿本次标签审计强改原论文数字。此处只据Metadata核“无银杏”。
- 说明表与CSV已保存；原始光谱头三行同ANGERS，之后400–2500nm。
- EcoSIS Other(Open)。此为夏季绿/新鲜叶实验，不能作为秋黄银杏替代。

#### 另核查的多物种光谱：无物种映射，不纳入有效银杏数据

Liu & Du (2024-06-27), V1.0，[Zenodo DOI10.5281/zenodo.12564322](https://doi.org/10.5281/zenodo.12564322)，记录称849片、95种。下载后核查，R/T表为400–2400 nm、每1 nm，但没有物种或样本映射；实际853个数值样本列也与记录不一致。**不能认定任何列是银杏**，因此未将这些匿名光谱作为交付数据，避免误用。对应PROSPECT-DP，也不是下述Zhou2024的银杏研究。

### 1.3 银杏季节色素

#### Li et al. (2020)：自然秋季

Weixing Li, Lu Wang, Zhichong He, Zhaogeng Lu, Jiawen Cui, Ningtao Xu, Biao Jin & Li Wang (2020), *Horticultural Plant Journal* 6(6):396–408，**Physiological and Transcriptomic Changes During Autumn Coloration and Senescence in Ginkgo biloba Leaves**，DOI [10.1016/j.hpj.2020.11.002](https://doi.org/10.1016/j.hpj.2020.11.002)，§2.1–2.2，§3.1，**Fig.1B–M**。

扬州3棵健康成年树、相同高度向阳的两年生枝；2017年8月21、9月12、10月6/26、11月8/21取样。绿叶期GS=9/12，转色TS=10/26，黄叶YS=11/8；11/21近落叶。**总色素是新鲜样混合溶剂(丙酮/无水乙醇/水4.5/4.5/1)提取后的分光光度测量；类胡萝卜素分组另做HPLC**。正文精确值如下，单位mg/g（方法以鲜叶称样，但原数字段未明写FW；本报告标为“原文mg/g、鲜样方法”，不加dry weight）。

| 时点 | Chla | Chlb | Car总量 | 性质和位置 |
|---|---:|---:|---:|---|
| 9月（最高） | 1.30 | 0.83 | 没找到正文精确值 | 实测，§3.1、Fig1C |
| 10月初（仍绿） | 没找到正文精确值 | 没找到正文精确值 | 0.47（最高） | 实测，§3.1、Fig1D |
| 11月下旬（近落叶黄叶） | 0.07 | 0.05 | 0.31 | 实测，§3.1、Fig1C–D |

“黄叶Cab=0.12mg/g”只能标为**本报告对0.07+0.05的计算**，不是原文单列Cab。没有同批FMA/叶面积，不能算µg/cm²；不可用另研究的叶厚或LMA补转换。HPLC各组分见Fig1F–M；不把图柱估成数值。

#### Jurčević Šangut & Šamec (2024)：逐月表

Iva Jurčević Šangut & Dunja Šamec (2024), *Plants* 13(21):3044，**Seasonal Variation of Polyphenols and Pigments in Ginkgo (Ginkgo biloba L.) Leaves: Focus on3′,8″-Biflavones**，DOI [10.3390/plants13213044](https://doi.org/10.3390/plants13213044)，[PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC11548628/)，**Table1**、§3.2–3.3、Fig1。

2022克罗地亚Koprivnica五棵约30年树；冻干粉纯丙酮提取，分光光度；**单位以Table1和方法为mg/g dry weight**，不是面积。下表全为实测均值±SD，原表已人工转CSV `data/Jurcevic_Sangut_Samec_2024_Table1_pigments_mg_g_dw.csv`，CSV不是作者原始个体数据。

| 月 | Chla (mg/g dw) | Chlb | Cab | Car |
|---|---:|---:|---:|---:|
| 5 | 0.68±0.04 | 0.15±0.04 | 0.84±0.08 | 0.02±0.00 |
| 6 | 0.96±0.04 | 0.18±0.02 | 1.13±0.06 | 0.03±0.00 |
| 7 | 1.71±0.06 | 0.35±0.01 | 2.07±0.07 | 0.24±0.01 |
| 8 | 0.87±0.01 | 0.17±0.01 | 1.04±0.02 | 0.05±0.01 |
| 9 | 0.73±0.01 | 0.13±0.00 | 0.86±0.01 | 0.05±0.00 |
| 10 | 0.20±0.01 | 0.09±0.01 | 0.29±0.02 | 0.08±0.00 |
| 11 | 0.07±0.00 | 0.08±0.01 | 0.15±0.01 | 0.11±0.01 |

**原文存在冲突**：Table1首列题“Season2020”，但方法§3.2与Fig1均写2022；正文讨论July peak单位误写µg/g dw，Table1+§3.3明确mg/g dw。未找到勘误，故报告按表/方法抄录并保留冲突。无同批LMA不能转换µg/cm²。

#### Xu & Ye (2023)：绿叶面积对照

同§1.1引用，Fig3d及正文Results：银杏Cab均值**42.1µg/cm²**，5片夏季成熟绿叶，乙醇提取分光测定，**实测**。Car/Cw/Cm仅Fig3d、N仅Fig3e，本次没有数值表就不估。正文给的Car11.5µg/cm²、Cw11.6mg/cm²、Cm9.9mg/cm²都是**10物种总体均值，绝不能当银杏值**。补表有Ginkgo提取液光谱，可保留为色素实测支持。


#### Lichtenthaler, Abuslima & Nick (2023)：绿银杏 Cab、Car 与 Cm 对照

来源：*Photosynthetica* **61(3):297–307**，**Table 2, p.302；Table 3, p.303**，[*Strong increase of photosynthetic pigments and leaf size in a pruned Ginkgo biloba tree*](https://doi.org/10.32615/ps.2023.020)，[原刊PDF](https://ps.ueb.cas.cz/pdfs/phs/2023/03/04.pdf)（[本地副本](data/Lichtenthaler_Abuslima_Nick_2023.pdf)）。以下只取**未修剪对照树 Tree 2** 的2022年7月绿叶（Table2为每叶类4–8次测定的均值），不混用强修剪树的异常高色素叶，也不是秋黄叶。

| Tree 2 叶类 | Cab：原表 mg/m² → µg/cm² | Car：原表 mg/m² → µg/cm² | SLM（干物面密度）：原表 mg/cm² → Cm g/cm² | 性质/定位 |
|---|---:|---:|---:|---|
| 深绿 | 769±73 → 76.9±7.3 | 171±18 → 17.1±1.8 | 10.1±0.8 → 0.0101±0.0008 | 提取分光色素与干物面密度**实测**；Cab/Car Table2，SLM Table3；箭头后为纯单位换算 |
| 绿 | 471±55 → 47.1±5.5 | 103±10 → 10.3±1.0 | 7.3±0.3 → 0.0073±0.0003 | 同上；保留原表±数。Table3同一Cab格写472±55，与Table2相差1 mg/m²；本表明确采用Table2 |
| 浅绿 | 263±19 → 26.3±1.9 | 81±8 → 8.1±0.8 | 10.5±0.3 → 0.0105±0.0003 | 同上；浅绿不等于秋季衰老黄叶 |

Table3给的是水占鲜重百分比，并非EWT；没有据此当成实测Cw。以上也不能与另一论文的干重色素浓度拼接，反算一片不存在的秋黄叶。

### 1.4 同类落叶树的秋黄叶对照

| 树种/状态 | Cab 或总叶绿素 | Car | 性质、方法与精确出处 |
|---|---:|---:|---|
| 挪威槭 *Acer platanoides*，绿叶 | 31.6±9.1 µg/cm² | 没找到对应数值表 | **光学估计/经验标定**，不是这些叶块逐片提取的直接生化值。Mattila & Tyystjärvi (2023), *Tree Physiology*43:751–768，Fig.1图注（均值±SD，4个生物重复）；方法“Calibration of pigment measurements”说明 MultispeQ 用 DMF 提取分光数据校准。[DOI10.1093/treephys/tpad010](https://doi.org/10.1093/treephys/tpad010)、[全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10177003/)。 |
| 同种，秋季黄叶块 | 8.1±5.0 µg/cm² | 仅见 Supplementary Fig.S18c 的色素对比图，未估读 | 同上，Fig.1；是该实验的黄/浅绿色叶块，不能解释为所有秋黄阔叶的通用Cab。 |
| 挪威槭，夏季绿叶（2020年6月） | 3.09±0.24 µg/mg鲜重 | 0.190±0.66 µg/mg鲜重（原表照录） | **提取实测**；100%甲醇提取、分光法，非HPLC。Macioszek, Chalamońska, Oliwa, Staszak & Sobczak (2025), *Plants*14(6):909，Table3；方法§4.3“Chlorophyll and Carotenoid Content”。[DOI10.3390/plants14060909](https://doi.org/10.3390/plants14060909)、[原表](https://pmc.ncbi.nlm.nih.gov/articles/PMC11945391/#plants-14-00909-t003)。 |
| 同研究，秋季黄区（2020年11月） | 0.540±0.15 µg/mg鲜重 | 0.431±0.07 µg/mg鲜重 | 同上，Table3，均值±SD，8个重复；取有“green islands”症状叶的黄色区域，属于特定生理背景，不是无病银杏。 |

上述鲜重单位不能直接填入PROSPECT。缺少同批叶的鲜重面密度，**没有换算成µg/cm²**。原表夏叶Car的SD大于均值，保留原值并标疑，不自行修小数。Mattila2023补充包的[下载链接](https://pmc.ncbi.nlm.nih.gov/articles/instance/10177003/bin/mattila2022_si_v4_tpad010.zip)本次返回HTML验证页而非ZIP，未把它保存成伪数据；可重取：

```sh
curl -fL -A 'GinkgoResearch/1.0' \
  'https://pmc.ncbi.nlm.nih.gov/articles/instance/10177003/bin/mattila2022_si_v4_tpad010.zip' \
  -o data/Mattila_Tyystjarvi_2023_supplement.zip
```

### 1.5 秋黄银杏 PROSPECT 参数：逐项状态

| 参数 | 秋黄银杏结论 | 有用来源/限定 |
|---|---|---|
| N（结构，无量纲） | **没找到**可核实的单独黄银杏值 | Xu&Ye2023 Fig3e绿银杏N是反演，仅图；LOPEX_ZJU不公开逐叶表。 |
| Cab、Car（µg/cm²） | **没找到**有明确秋黄银杏阶段且可抄表的数值；有上述mg/g季节表 | 不跨研究拼LMA换单位；SPAD不是Cab。 |
| Anth（花青素，µg/cm²） | **没找到**秋黄银杏独立定量值 | LOPEX_ZJU确测Ants，但无银杏逐叶数；PROSPECT论文固定0不等于实测不存在。 |
| Cbrown（经验褐色素，无量纲） | **没找到**秋黄银杏反演值 | 这是经验无量纲褐色吸收参数，不能直接用“褐色素含量mg/g”替换；Zhou2024模拟表单位误写µg/cm²也应指出。 |
| Cw（EWT，cm） | **没找到**秋黄银杏同批定量值 | Xu&Ye2023绿叶Fig3d只是图；水占鲜重%不是EWT。 |
| Cm（LMA，g/cm²） | **没找到**秋黄银杏同批定量值 | 干重面积质量，不能用色素mg/g dw替代。 |

Kai Zhou et al.(2024), *Plant Phenomics*6:0282，**Coupling PROSPECT with Prior Estimation of Leaf Structure to Improve the Retrieval of Leaf Nitrogen Content in Ginkgo from Bidirectional Reflectance Factor Spectra**，DOI [10.34133/plantphenomics.0282](https://doi.org/10.34133/plantphenomics.0282)，[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11641793/)，**Table2**：N1.0–2.5、Cab10–100µg/cm²、Car0.5–20µg/cm²、Cw1–40mg/cm²、Anth0、Cbrown0是**模拟输入范围/固定假设**，不是测得的黄银杏参数。采样为7–9月且研究重点氮肥处理，数据仅合理请求，补充只是FigsS1/S2。请勿把Table2当成秋黄叶拟合结果。

### 1.6 PROSPECT-D 完整光谱系数（已下载、已校验）

| 文件 | 内容、出处与性质 |
|---|---|
| [data/prospect_d_spectra.txt](data/prospect_d_spectra.txt) | 原始文本，**模型数据**，不是银杏测量。取自 J. Gómez-Dans 的开源 Python `prosail` **2.0.5** 发行包内 `prosail/prospect_d_spectra.txt`；与检索当日仓库 master 的同名文件逐字节一致。文件头为 `dataSpec_PDB.m — January, 16th 2017`，注明 Féret, Gitelson, Noble & Jacquemoud (2017)。[版本页](https://pypi.org/project/prosail/2.0.5/)、[源码文件](https://github.com/jgomezdans/prosail/blob/master/prosail/prospect_d_spectra.txt)、[原始直链](https://raw.githubusercontent.com/jgomezdans/prosail/master/prosail/prospect_d_spectra.txt)。 |
| [data/prospect_d_coefficients.csv](data/prospect_d_coefficients.csv) | 上述数据添加明确列名后的 CSV；数值未拟合、插值或重标定。 |
| [data/prospect_d_provenance.json](data/prospect_d_provenance.json) | 固定发行版本、下载直链、发行包与原文件 SHA-256、波长和列定义。 |

| 原文件列 | CSV 列名 | 单位/意义（按原文件头） | 性质与精确位置 |
|---|---|---|---|
| 1 | wavelength_nm | nm | 模型网格；文件头 `[1]` 及全部数据行 |
| 2 | n | 无量纲，叶材料有效折射率 | 模型校准数据；文件头 `[2]` |
| 3 | kCab | cm²/µg，叶绿素 a+b 比吸收系数 | 模型校准数据；文件头 `[3]` |
| 4 | kCar | cm²/µg，类胡萝卜素比吸收系数 | 模型校准数据；文件头 `[4]` |
| 5 | kAnth | cm²/µg，花青素比吸收系数 | 模型校准数据；文件头 `[5]`。以此数据文件的约定为准；不可直接混用以 nmol/cm² 报告的实验数据。 |
| 6 | kBrown | arbitrary units，褐色素比吸收系数 | 模型数据；文件头 `[6]`，注明由 F. Baret 提供，不是银杏黄叶的生化测定。 |
| 7 | kCw | cm⁻¹，水吸收系数 | 模型数据；文件头 `[7]` |
| 8 | kCm | cm²/g，干物质比吸收系数 | 模型数据；文件头 `[8]` |

已程序核验：**2101 个数据行、8 列，400–2500 nm、逐 1 nm、无缺行、数值全部有限**；这些是本次对下载文件的检查结果。原文件 SHA-256：`e703b345f0a0860808e230ca0869f5b108ca1115ab9950c9651a29fee72c474d`。发行包的 SHA-256 也与 PyPI 元数据一致。`k` 是与对应面密度相乘使用的比吸收系数，不应当作渲染器中以长度为单位的体吸收系数直接填入。

可重取固定版本：

```sh
curl -fL -A 'GinkgoResearch/1.0' \
  'https://files.pythonhosted.org/packages/b5/52/d0c15ab469e8c82bc76a6b6cd614efbc60e43d09d5bacaa349170d229e91/prosail-2.0.5-py3-none-any.whl' \
  -o /tmp/prosail-2.0.5.whl
unzip -p /tmp/prosail-2.0.5.whl prosail/prospect_d_spectra.txt > data/prospect_d_spectra.txt
```

#### 原始论文和附件重取

```sh
curl -L --fail 'https://onlinelibrary.wiley.com/doi/pdf/10.1111/j.1438-8677.1992.tb00261.x' -o data/Matile_Flach_Eller_1992.pdf
curl -L --fail 'https://static-content.springer.com/esm/art%3A10.1038%2Fs41598-023-31718-1/MediaObjects/41598_2023_31718_MOESM1_ESM.xlsx' -o data/Xu_Ye_2023_Supplementary1.xlsx
```

第1条本次403，需有权访问原出版商；第2条已成功。

### 1.7 解剖、叶脉与上下表面

**结论**：已有足够的原始实测资料约束成熟绿叶的厚度、脉间距、长短枝差异及形状，但没有找到同一叶片由绿转黄时的这些几何量的配对实测。不能把绿叶解剖表冒充秋黄叶表。下文的表格均保留样本背景和测量定义；未数字化图上的柱高。

Leigh et al. (2011；在线发表于2010)，*New Phytologist* **189**, 459–470，[*Structural and hydraulic correlates of heterophylly in Ginkgo biloba*](https://doi.org/10.1111/j.1469-8137.2010.03476.x)，**Table 1、Fig. 3、Fig. 4**。下表全部为作者**实测，均值±SE**；B/C/M 分别为叶片基部/中部/近口沿。厚度在各部位**尽可能远离叶脉处**量取，不是脉处厚度。短枝、长枝列是该研究的样本，不能混成种级固定值。在线全文含表：[出版商全文](https://nph.onlinelibrary.wiley.com/doi/10.1111/j.1469-8137.2010.03476.x)。

| 量 | 位置 | 短枝叶 | 长枝叶 | 性质与定位 |
|---|---|---:|---:|---|
| 叶肉处厚度 (µm) | B | 278.0±9.3 | 278.0±14.2 | 实测；Table 1；Fig. 3a |
| 同上 | C | 206.0±7.6 | 233.3±11.4 | 实测；同上 |
| 同上 | M | 163.3±7.5 | 202.7±11.2 | 实测；同上 |
| 脉间距 (mm) | B | 0.69±0.01 | 0.80±0.02 | 实测；Table 1；Fig. 3c |
| 同上 | C | 0.67±0.01 | 0.83±0.02 | 实测；同上 |
| 同上 | M | 0.70±0.02 | 0.85±0.02 | 实测；同上 |
| 脉长密度 (cm/cm²) | B | 15.15±0.22 | 13.79±0.26 | 实测；Table 1；仅测B/M |
| 同上 | M | 14.97±0.26 | 12.70±0.28 | 实测；同上 |
| 束鞘延伸部分横截面积 (µm²) | B | 20957±2314 | 24542±2609 | 实测派生：上、下BSE分别近似矩形，以宽×深相加估面积；Table 1；Fig. 3f、4e–h |
| 同上 | C | 9496±522 | 13577±522 | 同上 |
| 同上 | M | 7563±529 | 10075±443 | 同上 |

**单位提醒**：上表脉长密度量的是总脉长/叶面积，不是边缘截线上的“条/mm”。如需统一成 mm/mm²，纯单位换算是以上 cm/cm² 数除以10（如15.15→1.515），应标“单位换算”；不要把它写成实测的条/mm。原文 Fig. 4 的 BSE 是脉至表皮的细胞群，通常叶下侧较宽。该论文 Table 1 在线版的 LMA 单位标 g/m²、数字却为0.84与0.97，存在量级疑点；未擅自修正或采用为渲染参数。

Klimko, Korszun & Bykowska (2015)，*Acta Scientiarum Polonorum Hortorum Cultus* **14(4)**,169–189，[*Comparative morphology and anatomy of the leaves of Ginkgo biloba L. cultivars*](https://czasopisma.up.lublin.pl/asphc/article/view/2608)，[原刊PDF](https://czasopisma.up.lublin.pl/asphc/article/download/2608/1842/9360)，无 DOI（未找到）。**2013年8月、波兰同一园地、长枝叶；21个栽培品种及雌雄各一克隆**；形态各30叶；解剖用酒精保存、甘油明胶装片切片，不是活叶无损厚度。下表的厚度取原文 **Table 3, p.182；方法 p.171；文字 p.185；Fig.57–58 p.184**。

| 量 | 结果 (µm) | 性质、范围定义、定位 |
|---|---|---|
| 脉处叶总厚度（不是脉的横向宽） | 不同品种均值329.6–626.2 | 作者实测；Table 3“Leaf vein thickness”；不是全体叶的最小/最大值 |
| 脉间叶片厚度 | 不同品种均值316.1–492.1 | 作者实测；Table 3“Leaf lamina thickness” |
| 上侧 epicuticular layer 厚 | 不同品种均值3.3–5.3 | 作者实测；Table 3；作者标题为epicuticular layer，正文称cuticle；不混同表皮细胞厚 |
| 下侧 epicuticular layer 厚 | 不同品种均值4.2–6.5 | 同上 |
| 雄克隆：脉处/脉间厚度，上/下 epicuticular layer | 479.6 / 421.1；3.9 / 4.7 | 作者实测；Table 3 |
| 雌克隆：同上 | 484.3 / 472.6；4.2 / 6.5 | 作者实测；Table 3 |

表面与束鞘（上述Klimko2015实测）：上侧角质层多呈平滑微纹理，下侧有乳突、平滑或平滑带条纹；蜡有直立管状棒晶（**pp.175–177；SEM Fig.24–54**）。气孔主要在下侧且下陷，作者在上侧仅少见气孔（**p.175；Figs24–29；p.185；Fig.58**）。束有薄壁细胞鞘和伸至表皮的BSE，木质部向上、韧皮部向下（**p.185；Fig.57–58**）。这些显微结构并不直接给出表面 roughness、specular 权重或BRDF；**黄银杏叶上下表面的绝对光泽、BRDF/BTDF实测：没找到**。

| 不能混淆的量 | 查得状态 |
|---|---|
| 维管束/脉的横向总宽度及近柄/叶缘的分布 | 没找到可直接采用的数值表；不能用上表“脉处厚度”或管胞直径冒充 |
| BSE 表面投影宽 | Baresch, Crifò & Boyce (2019；2018在线)，*New Phytologist*221:628–639，[DOI10.1111/nph.15476](https://doi.org/10.1111/nph.15476)，Discussion给银杏136 µm；**基于表皮脉迹占比/迹长密度的计算量**，不是裸维管束总宽；具体Ginkgo来源须再核Table S1，因此不建议填入“脉宽”材质参数 |
| 秋黄叶叶肉/脉处厚度变化 | 没找到同叶、同季节配对实测 |

## 2. 叶形与叶脉发育

### 2.1 尺寸、缺刻与长短枝差别

*Flora of China* **4**, p.8 (1999)，Ginkgoaceae（Fu Liguo, Li Nan & Robert R. Mill），[官方植物志PDF](https://www.iplant.cn/foc/pdf/Ginkgo.pdf)：常见叶宽**5–8 cm**；叶柄**(3–)5–8(–10) cm**；长枝叶中央深窄裂、两叶瓣还可再裂，短枝叶远端波状及浅缺刻。**性质：植物志描述范围，不是统计样本均值。** 叶片长采用下方定义明确的实测统计。

Klimko2015 **Table 1, pp.172–173；方法pp.170–171** 的下列数值均为**作者实测，均值±SD（括号中单样本范围），单位mm**。叶片长是从叶片基部至最长叶瓣顶端，**不含叶柄**；缺刻为该文的“depth of indentation”。下列雌雄克隆更接近普通形状，仍非随机种级总体。完整品种表在PDF中。

| 样本 | 叶片长 | 叶宽 | 中央缺刻深 | 叶柄长 |
|---|---:|---:|---:|---:|
| 雄克隆 | 62.8±5.5 (51.0–72.2) | 92.7±11.4 (65.4–119.7) | 14.1±10.7 (0–38.8) | 50.6±11.2 (31.0–76.7) |
| 雌克隆 | 61.5±6.3 (47.3–73.6) | 74.7±11.3 (50.6–93.8) | 18.4±14.7 (0–86.3)† | 54.6±9.0 (37.3–75.9) |

**原表雌克隆的最大缺刻86.3mm大于同表最大叶片长73.6mm，有内部不一致；照录并标疑，不把86.3mm用作几何约束。** 该文p.175原文称叶片基部通常4–9脉（Table 1, p.173个别样本范围还含3），这是“叶片基部”可见脉，不等于叶柄内的原始两束。

长短枝差别的原始资料：

| 量/观察 | 结果 | 性质与出处 |
|---|---|---|
| 叶面积 | 短枝28.0±1.2 cm²；长枝11.0±0.5 cm² | 实测均值±SE；Leigh2011 Table1；其外冠、相当叶位样本，不是普适大小排序 |
| 轮廓复杂度 LDI=周长/√面积 | 短枝4.57±0.03；长枝5.04±0.08 | 实测派生量，均值±SE；Leigh2011 Table1；Fig2给轮廓示例 |
| 早/晚叶 | 早叶通常不裂或二浅裂；长枝晚叶常四裂；二次侧缺刻可至叶片长的1/3 | 实测描述；Critchfield1970 *Botanical Gazette*131(2):150–162，[DOI10.1086/336526](https://doi.org/10.1086/336526)，pp.158–159，Figs9–10、13–14，[USDA原文PDF](https://www.fs.usda.gov/psw/publications/critchfield/psw_1970_critchfield002.pdf) |
| 普通银杏扇形张角的总体统计、边缘波纹振幅/波长统计 | 没找到 | 不以扇形几何假设倒算并冒充实测 |
| 近似普通扇形的栽培克隆角度 | Li et al.2024 *Front.Plant Sci.*15:1367121，[DOI10.3389/fpls.2024.1367121](https://doi.org/10.3389/fpls.2024.1367121)，Fig1B与Supplementary Table S3含“normal”Tubifolia-6(CK6) basal angle | 实测；附表已下载data/anatomy/li2024_supplementary_table_S3.pdf：CK6为318.87±20.27°；同表另两种卷叶为42.67±9.46°和14.03±3.44°。其角定义/异常形态背景不适合普通扇形；同表CK6叶面积标225631.33 mm²、鲜重0.66 g，单位/量级存在疑点，未找到勘误，故仅照录线索，不推荐用作普通银杏扇角 |

**轮廓数据集**：Hang, Bauer, Mio & Mander (2021)，*Royal Society Open Science*8:210978，[DOI10.1098/rsos.210978](https://doi.org/10.1098/rsos.210978)，§2、Fig1–5；468片现代叶，来自同一未达生殖成熟树、半阴环境、长短枝混合；有灯箱照片和比例尺。原文按形状空间/PCA描述主要变异为尺寸、中央沟深和叶基两叶瓣夹角，并非发布一个“标准扇角”。原始叶影像：[Mander et al.2021, Living and fossil Ginkgo leaves, Dryad](https://doi.org/10.5061/dryad.7h44j0zsj)。这比凭一片叶拟合固定扇形更适合作为轮廓参考；压干样本不能当成鲜黄叶颜色标定。

### 2.2 叶脉发育与生成规则

| 所问 | 找到的可用证据 | 性质、出处与边界 |
|---|---|---|
| 叶柄输入的两束 | 在5片成熟叶中，叶柄各有两个独立维管束，每束供一个叶瓣；整片有5或6个Strahler级（末端定为1） | 作者显微实测；Carvalho, Turgeon, Owens & Niklas2017，*American Journal of Botany*104(9):1285–1298，[DOI10.3732/ajb.1700277](https://doi.org/10.3732/ajb.1700277)，Results“Conductive areas…”、Fig1–2。级数不等于从柄起每支必等长分叉5–6次 |
| 从柄至叶缘 | 主要开放二叉、向边缘变细 | 上述2017实测；Fig1（全叶脉拓扑）；Fig2（横切）。不要凭此强加等长、等角、同步分叉 |
| 二叉发育机制 | 叶原基突起连续分叉；第二次突起分叉方向约与第一次垂直；作者推测叶缘较粗脉与不均等二叉前形成层有关 | Hara1980，*Botanical Magazine, Tokyo*93:1–12，[DOI10.1007/BF02489482](https://doi.org/10.1007/BF02489482)，p.1摘要（全文订阅）；前半SEM观察实测、后半原文明确推测。这个约直角是**早期叶原基形态的相继分叉方向**，不能当成成熟叶脉的平面叉角 |
| 到叶缘的条数及间距 | 早叶每半片48–75个末梢、平均脉距0.50–0.78mm；长枝晚叶每半片40–59、0.74–1.11mm | 作者实测；Critchfield1970 p.159 Fig11；早叶含该研究枝4、5，晚叶枝4；不加倍成单片统计，左右并未证明完全相等 |
| 分叉段长/分叉间距分布 | 没找到数值统计 | 2017 Fig1显示段长并不恒定；未从图测量或估值 |
| 成熟叶脉分叉角原始统计 | 没找到已核实的原始统计表 | Carvalho, Losada & Niklas2018，*Phloem networks in leaves*, *Curr Opin Plant Biol.*43:29–35，[DOI10.1016/j.pbi.2017.12.007](https://doi.org/10.1016/j.pbi.2017.12.007)，[作者机构全文](https://stri-apps.si.edu/docs/publications/pdfs/Carvalho_2018_phloem_network_in_leaves.pdf)，p.30有22°±2°（性质：引用，原始测量未核），但属综述且该句未给测量方法/样本，不能标作已核实直接实测；仅作后续溯源线索 |
| 是否绝不连接 | 不是：1065叶/11树的调查中9.9%叶至少有1处吻合，长枝13.4%、短枝8.2% | Arnott1959，*Am.J.Bot.*46(6):405–411，[DOI10.1002/j.1537-2197.1959.tb07030.x](https://doi.org/10.1002/j.1537-2197.1959.tb07030.x)，p.405摘要；透光观察与透明化实测；若做典型纹理可主用开放二叉，不能写成生物学上“从无吻合” |

**生成模型文献**：Fujita & Mochizuki (2006)，*Developmental Dynamics*235:2710–2721，[DOI10.1002/dvdy.20908](https://doi.org/10.1002/dvdy.20908)，**MODEL、Fig3B与Fig7A** 给叶片扩张、生长素与外排载体正反馈共同生成近银杏式二叉脉的机制模型；**性质为模拟/推断，不是银杏叉距/叉角的标定实测**。因此可参考其机制，但没有理由照其无量纲参数当银杏毫米尺度。

**“Arens1997”辨认**：能核到的是Nan Crystal Arens1997，*PALAIOS*12(1):84–94，[DOI10.2307/3515296](https://doi.org/10.2307/3515296)，题名*Responses of leaf anatomy to light environment in the tree fern Cyathea caracasana (Cyatheaceae) and its application to some ancient seed ferns*；对象是树蕨，不是银杏二叉脉的生成统计。没有找到对应的“Arens1997银杏脉二叉论文”，不能把树蕨数直接填入银杏。

## 3. 真照片（已下载 6 张；另列成对上下表面扫描 2 张的下载链接）

检索截至 2026-11-02。下表像素已用本地 JPEG 文件读取验证；作者、授权和拍摄说明来自对应 Wikimedia Commons 文件页（第一方上传者）。所有已下载图片均逐张查看。**本次没找到同时具备新鲜全黄单叶、透射扫描/灯箱、可校准尺度和色卡的一组照片；没找到同一片叶经过定量校准的透射与反射成对拍摄。** 不能把下列 JPEG 的像素值当作光谱透射率。

|本地文件 / 来源页（作者、日期）|授权（本表选用的开放许可）|原图直接链接；已核验像素|相机、镜头 / 扫描仪（EXIF，未写者为没找到）|光线、尺度、色卡与适用性|
|---|---|---|---|---|
|[backlit_dsg7056.jpg](photos/backlit_dsg7056.jpg)；[DSG7056-1](https://commons.wikimedia.org/wiki/File:DSG7056-1_Yellow_Ginkgo_biloba_leaves_-_vivid_translucent_illumination_by_autumn_sunlight.jpg)；Franz van Duns，2021-10-22|[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)|[JPEG](https://upload.wikimedia.org/wikipedia/commons/5/52/DSG7056-1_Yellow_Ginkgo_biloba_leaves_-_vivid_translucent_illumination_by_autumn_sunlight.jpg)；3028 × 3028|Sony ILCE-7RM4 / Alpha 7R IV；FE 200–600 mm F5.6–6.3 G OSS；实际焦距 400 mm；f/7.1、1/2000 s、ISO 800（本地 EXIF 与源页 Technical Details）|**作者明确说明秋季太阳透射照明**；脉、卷曲、叠叶遮光清楚。源页 Technical Details [9]：顶叶宽约 **80 mm**，为作者近似说明，非画面标尺。无色卡。源页 [6] 明确调整曲线、texture、clarity、vibrance、saturation；适合作背光外观参考，不能定量校色。|
|[autumn_leaf_scan.jpg](photos/autumn_leaf_scan.jpg)；[Autumn Ginkgo Leaf](https://commons.wikimedia.org/wiki/File:Autumn_Ginkgo_Leaf.jpg)；Ninjatacoshell，2008-11-07|[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)（另有 GFDL 可选）|[JPEG](https://upload.wikimedia.org/wikipedia/commons/4/4c/Autumn_Ginkgo_Leaf.jpg)；1552 × 1944|Canon CanoScan LiDE 70；EXIF 600 × 600 dpi；Paint.NET v3.05；相机镜头不适用|作者明确说扫描；**是黄中带绿的转色叶，不是均匀全黄**。叶片完整、二叉脉与口沿细节可见；透射/反射扫描模式没找到。名义尺度为扫描仪 EXIF 的 600 dpi，尚无未重采样/校尺证明；无尺子、无色卡。|
|[dry_autumn_leaf_scan.jpg](photos/dry_autumn_leaf_scan.jpg)；[Feuille d’automne et séchée… (1)](https://commons.wikimedia.org/wiki/File:Feuille_d%27automne_et_s%C3%A9ch%C3%A9e_de_Ginkgo_biloba_(1).jpg)；Jean-Pierre Bazard / Jpbazard，2018-08-05|[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)（源页另列旧版 CC 与 GFDL）|[JPEG](https://upload.wikimedia.org/wikipedia/commons/9/99/Feuille_d%27automne_et_s%C3%A9ch%C3%A9e_de_Ginkgo_biloba_%281%29.jpg)；2545 × 2628|扫描仪型号/镜头没找到；EXIF 72 dpi、Photoshop CS6，此 72 dpi **不是已知扫描采样率**|作者明确：2017 年秋叶，**干燥十个月**后扫描。叶片黄、脉清楚，适合作干燥黄叶形态/纹理，不能冒充新鲜黄叶含水光学。扫描透反模式没找到；真实尺度没找到；无色卡。|
|[sunlit_branch_olga.jpg](photos/sunlit_branch_olga.jpg)；[Feuilles de Ginkgo biloba](https://commons.wikimedia.org/wiki/File:Feuilles_de_Ginkgo_biloba.jpg)；Olga Rithme，2013-11-13|[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)|[JPEG](https://upload.wikimedia.org/wikipedia/commons/f/f5/Feuilles_de_Ginkgo_biloba.jpg)；3543 × 5335|Nikon D90；焦距 200 mm；f/6.3、1/1000 s、ISO 560；镜头型号没找到（本地 EXIF 与源页 Metadata）|作者称阳光下枝上秋叶；查看可见黄色枝叶、亮叶与阴影混合，部分有透亮外观（**视觉判断**，不据此断定所有叶正/背光）。无尺度、无色卡；EXIF 300 dpi 是照片排版分辨率，**不是物体尺度**。|
|[fall_color_erdbaer.jpg](photos/fall_color_erdbaer.jpg)；[Ginkgo biloba leaves in fall color](https://commons.wikimedia.org/wiki/File:Ginkgo_biloba_leaves_in_fall_color.jpg)；Erdbaer，2011-11-02|[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)|[JPEG](https://upload.wikimedia.org/wikipedia/commons/5/5c/Ginkgo_biloba_leaves_in_fall_color.jpg)；2592 × 1944|Canon PowerShot SX200 IS；源页 Lens used 5.0–60.0 mm；实际 60 mm；f/5.3、1/500 s、ISO 100（本地 EXIF 与源页 Metadata）|枝上黄叶、明显叠叶投影与表面起伏；自然光、受光/阴影混合为**视觉判断**；光源光谱、灯位、纯正光几何没找到。无尺度、无色卡。|
|[dry_leaves_scan_300dpi.jpg](photos/dry_leaves_scan_300dpi.jpg)；[Gingo biloba leaves scan](https://commons.wikimedia.org/wiki/File:Gingo_biloba_leaves_scan.jpg)；Aida（上传者，源页作者写 me），2007-09-02|作者释放到 **Public domain**（源页 Licensing）|[JPEG](https://upload.wikimedia.org/wikipedia/commons/4/43/Gingo_biloba_leaves_scan.jpg)；2315 × 2950|Canon CanoScan LiDE 25；300 × 300 dpi；CanoScan Toolbox 4.9.3（本地 EXIF 与源页 Metadata）|作者明确干叶扫描，采叶约两周前；查看为**干褐叶，非目标全黄叶**，仅保留作干燥与叶形对照。扫描透反模式没找到；名义 300 dpi，未有校尺/未重采样证明；无色卡。|

以上所有曝光、焦距、dpi 是原图 EXIF 或原作者 Metadata/Technical Details，属于拍摄元数据；“太阳透射”“干十个月”等为原作者说明；“脉清楚”“混合光”等为此次查看后的视觉判断。没有从图像颜色反演色素或光学参数。图像下载时未改像素或元数据；文件字节数与 SHA-256 见 [photos/manifest.json](photos/manifest.json)。

### 补充：上下表面扫描（源页互相链接，原图下载被 HTTP 429 拒绝）

|来源 / 作者 / 日期|授权|原图直接链接；源页像素|扫描元数据与限制|
|---|---|---|---|
|[Ginkgo biloba top 01](https://commons.wikimedia.org/wiki/File:Ginkgo_biloba_top_01.jpg)；NobbiP，2020-11-15|CC BY-SA 3.0（另有 2.5/2.0/1.0、GFDL 可选）|[JPEG](https://upload.wikimedia.org/wikipedia/commons/1/1a/Ginkgo_biloba_top_01.jpg)；2656 × 2256（源页 File history/Metadata，非本地核验）|作者说明叶上面扫描；Canon CanoScan LiDE 220，400 × 400 dpi，GIMP 2.10.22。源页将 bottom 02 列为另一版本。未下载查看原图；无色卡信息；未证明两侧图保持相同像素比例。|
|[Ginkgo biloba bottom 02](https://commons.wikimedia.org/wiki/File:Ginkgo_biloba_bottom_02.jpg)；NobbiP，2020-11-15|CC BY-SA 3.0（另有旧版 CC、GFDL 可选）|[JPEG](https://upload.wikimedia.org/wikipedia/commons/4/41/Ginkgo_biloba_bottom_02.jpg)；1177 × 1000（源页，非本地核验）|作者说明叶下面扫描；Canon CanoScan LiDE 220，400 × 400 dpi，GIMP 2.10.22。类别为 Yellow Ginkgo biloba leaves。与 top 01 为同日同作者、源页互链的一组上下表面记录；**未取得原图，不能确认逐叶对应及未重采样**。无色卡信息。|

429 后未继续密集重试。可稍后在项目根目录运行以下命令：

```sh
curl --fail --location --user-agent 'LeafReferenceResearch/1.0' 'https://upload.wikimedia.org/wikipedia/commons/1/1a/Ginkgo_biloba_top_01.jpg' --output photos/yellow_scan_top_nobbip.jpg
curl --fail --location --user-agent 'LeafReferenceResearch/1.0' 'https://upload.wikimedia.org/wikipedia/commons/4/41/Ginkgo_biloba_bottom_02.jpg' --output photos/yellow_scan_bottom_nobbip.jpg
```

同叶正光/背光成对、灯箱与有色卡黄叶：**没找到**。公开授权原图足够参考叶形和背光视觉，仍不足以校准物理反射/透射、BRDF 或绝对色彩。

### 补充：具有真实灯箱和比例尺的原始照片数据集（颜色尚未核验）

[Mander, Hang, Bauer & Mio (2021), *Living and fossil Ginkgo leaves*, Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.7h44j0zsj)，DOI [10.5061/dryad.7h44j0zsj](https://doi.org/10.5061/dryad.7h44j0zsj)；对应 [Hang et al. (2021), *Royal Society Open Science* 8:210978](https://doi.org/10.1098/rsos.210978)，论文 §2 “A dataset of modern and fossil leaves” / Data accessibility。原作者明确说明 **468 片成熟展开叶、压干、相机位于灯箱上方 20 cm、每片与比例尺同拍**。这是已找到最贴合灯箱与尺度要求的学术原始照片数据源，但本次未能查看其中的原始照片，因此 **是否秋黄、脉是否清楚、相机镜头、像素尺寸、色卡均为没找到/尚未核验**；压干叶不能代表新鲜黄叶的 Cw。数据页 JSON-LD 许可为 [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)。

文件 `Supplementary_Information.zip`（数据页文件长度 **745,843,529 bytes**）的[直接下载链接](https://datadryad.org/downloads/file_stream/1145562)。只请求 ZIP 尾部以查询目录、避免整包下载时返回 HTTP 403，本次未下载该包；可运行：

```sh
curl --fail --location --user-agent 'LeafReferenceResearch/1.0' 'https://datadryad.org/downloads/file_stream/1145562' --output data/ginkgo_dryad_Supplementary_Information.zip
```

## 下载文件与核验记录

| 文件/目录 | 用途与已做核验 |
|---|---|
| [data/ANGERS/](data/ANGERS/) | 原始反射/透射、元数据及说明各一份；2051波长×276样本；**无银杏**。另存元数据CSV和物种列表用于复查。 |
| [data/LOPEX/](data/LOPEX/) | 同类四表及原始实验报告；2101波长×330样本；**无银杏**。 |
| [data/metadata_species_audit.json](data/metadata_species_audit.json) | 本次按有效物种行的审计结果；与原始表对应。 |
| [data/optics_downloads_manifest.json](data/optics_downloads_manifest.json) | 光谱资料的下载直链、文件长度、SHA-256、XLSX ZIP完整性、实际波段行数和样本列数；已下载的文件通过格式与完整性检查。 |
| [data/Jurcevic_Sangut_Samec_2024_Table1_pigments_mg_g_dw.csv](data/Jurcevic_Sangut_Samec_2024_Table1_pigments_mg_g_dw.csv) | 从发表表格转录，带单位/年份冲突注记；不是未加工个体实验数据。 |
| [data/Xu_Ye_2023_Supplementary1.xlsx](data/Xu_Ye_2023_Supplementary1.xlsx)、[Fig.3](data/Xu_Ye_2023_Fig3.png) | 前者是**提取液吸光度**；后者才展示叶片实测R/T，不能互相替代。 |
| [data/anatomy/](data/anatomy/) | Klimko2015原刊与Li2024附表；来源记录在[sources.json](data/anatomy/sources.json)。 |
| [data/prospect_d_provenance.json](data/prospect_d_provenance.json) | PROSPECT-D固定发行版来源与系数文件校验，见§1.6。 |
| [photos/manifest.json](photos/manifest.json) | 六张原图的直链、字节数、SHA-256及核验像素；已逐张看图。 |


