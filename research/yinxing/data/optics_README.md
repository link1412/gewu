# 光学数据来源与使用边界

- `ANGERS/`：EcoSIS 原始四个 XLSX，2003 年 6 月、276 个样本。400–2450 nm 叶反射/透射；Metadata 和逐物种清单中**没有银杏**。说明表明确 N 来自 PROSPECT 反演；Anth = -999 是缺测。
- `LOPEX/`：EcoSIS 原始四个 XLSX 与 Hosgood et al. 1994 原始报告。400–2500 nm 叶反射/透射，元数据中 330 个有效样本，**没有银杏**。
- 两库光谱 XLSX 前三行是样本号、文件名、测量类型，第四行开始才是波长。数值已经是 0–1 分数，不能再除以 100。原始文件未改；Metadata CSV 是逐单元格导出，保留缺测编码。`metadata_species_audit.json` 说明物种审计。
- `Xu_Ye_2023_Supplementary1.xlsx`：Xu & Ye (2023), Scientific Reports 13:4694, DOI 10.1038/s41598-023-31718-1 的原始 Supplementary Information 1。Ginkgo 工作表为 5 个绿叶样本的**色素乙醇提取液吸光度**，400–1000 nm。不是叶反射或透射。对应 CSV 文件名刻意含 `NOT_leaf_RT`。
- `Jurcevic_Sangut_Samec_2024_Table1_pigments_mg_g_dw.csv`：从 Jurčević Šangut & Šamec (2024), Plants 13:3044, DOI 10.3390/plants13213044 Table 1 人工转录的均值和 SD，单位 mg/g 干重，不是作者逐叶原始数据。原表年份写 2020，但方法和 Fig.1 写 2022；正文一处单位误写 µg/g，表头与方法都为 mg/g。本文件按表/方法抄录，未擅自转换面积单位。
- `zenodo_12564322/`：Liu & Du (2024-06-27), Zenodo V1.0, DOI 10.5281/zenodo.12564322 的原始模型代码和匿名多种叶 R/T。记录声称 849 样本，但本地 XLSX 实际有 853 个数值样本列，且没有可用物种映射，**不能当银杏证据**。400–2400 nm，方向–方向测量，也不能当积分球数据。

`optics_downloads_manifest.json` 给原始文件 URL、大小、SHA-256、文件头、XLSX ZIP 完整性及真实光谱行列检查。ANGERS/LOPEX 的 EcoSIS 授权字段为 Other (Open)，未找到更具体 CC 条款；使用时保留数据作者与出处。原始文件仅下载，未作插值、裁剪、归一化或反演。
