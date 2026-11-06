# 新增黄叶 R/T：LOTUS（2026-11-02 核查）

## 结论与适用性

已读 `../yinxing2/report.md` 和 `../yinxing3/report.md`。本轮新增获得 **LOTUS 的两个有照片身份对应的黄色叶样的同叶反射/透射数值**，不是前轮 Noda、Morimoto 或 MapS-Wear 的复用。**没有取得黄银杏 T，也没有在本分支找到校准背光照片。**

- **OAK01 / OAK01b：2019-09-19 的黄褐栎叶（Quercus sp.，原表没有种级鉴定）**。原样本表明确写 OAK01 “yellow brown, shiny”，背面 OAK01b “yellowy, hairy”；原始照片实看为黄褐而非鲜亮金黄。OAK01b 的 `b` 按作者 README 表示同一叶背面，**不是第二片独立叶**。可以作为秋季黄褐栎叶的物性替代，不能冒充黄银杏、纯黄色或逐像素背光颜色真值；没有证明两面仪器测量落在精确同一叶肉点。
- **CCAN2：2019-08-21 的浅黄梣叶槭（Acer negundo L.，Manitoba maple）**。作者论文 Figure 1 说明明确称其 very light yellow，实图也显示整片浅黄色；叶绿素 a+b 3.31655、类胡萝卜素 0.409235 μg/cm²。**日期是8月，原因/自然秋季衰老阶段未注明，不能称秋黄样本。** 作为“黄色阔叶”的低色素极端参考有用。

原始数据和3张身份照片均 **CC BY 4.0**，作者 Reisha D. Peters、Scott D. Noble，数据 [DOI10.20383/103.0606](https://doi.org/10.20383/103.0606)，[FRDR原记录](https://www.frdr-dfdr.ca/repo/dataset/2fb09058-9182-4460-8594-591a4b6a9c61)。论文为 [Peters & Noble 2024, RSE 315:114424](https://doi.org/10.1016/j.rse.2024.114424)。仓库许可原文、README和样本原表已保留。

## 测法与校准

[作者预印本原文](https://harvest.usask.ca/server/api/core/bitstreams/440059d4-47c7-4122-bb56-a1ae34c56451/content) 的 §2.1、§2.2、§2.3.3、Figure 1 及对应数据 README 已实际读取。以下不是由反射照片反推透射率。

- 样品来自 Saskatoon 校园周围树木、花园、温室及农田，采后独立塑料袋置暗冷箱/冰上，光谱和生物物理测量在采后3小时内完成。不是先压干再拍摄。之后的烘干用于干物质量，不等于这里光谱测的是烘干叶。
- **Cary 5000 + diffuse reflectance accessory**：作者称 diffuse hemispherical R/T，垂直照明，200–2500 nm、1 nm输出间距；用 Labsphere 已表征 Spectralon 反射参考校正，并用空样品架透射测量修正小开口/光束尺寸不匹配。**1 nm间距不等于已证明1 nm光谱分辨率**；不额外推断是否包含全部镜面分量。交付的每条Cary曲线2301行，两个数字列依次为波长nm、无量纲 R 或 T（0.4为40%）。
- **GoSPo（仅选 CCAN2 的已积分 R/T）**：原始双向测量以垂直照明、天顶平面5°角间隔采集，再近似积分为半球量。校准目标是已表征的100μm PTFE薄片；实物文件400–1650nm、1nm输出、1251行。它与Cary是不同几何和积分方法，不能当成重复测量后随意平均；未将近似积分曲线称绝对角分布或相机像素。
- **没有交付逐样本原始白/暗读数、Spectralon校准证书、不确定度、光源SPD、响应校正表**。上述只说明作者采用参考物校正的实测物性，不能宣称计量溯源完备。给定光源SPD后可计算 `SPD×T(λ)` 的颜色；不能用 T 本身当亮度或将半球T直接当某方向的背光像素。
- 原始UV透射含少量负值，全部原样保留。Cary可见区400–700nm所选R/T无负值，同面R+T均未超过1；具体极值及全部异常数见 validation.json。未裁零、平滑、重新归一化。

## 照片仅证明叶色和样本身份

三图已完整解码并实际查看。均4032×3024 JPEG（EXIF Orientation=6，显示为竖图），Apple **iPhone SE**、4.15mm f/2.2、ISO25、1/60s、自动白平衡、EXIF标记sRGB、无嵌入ICC；不是RAW/DNG。拍摄时间分别2019-08-21及2019-09-19，与样本表一致。作者明确将叶平放浅色表面、固定相机高度，地面校准/映射供叶面积计算。实图可见纸面、相机支架及手绘1cm格线；**这是反射外观照，不是背光图**。

纸面没有声明为已校准白板/灰卡，未见ColorChecker；光源未标型号/色温/SPD，面积校准也不是色度校准。故三图均不能取RGB当颜色真值。照片和光谱按同名叶ID匹配，仍不构成同一画面上的透射校准。OAK01正面偏黄褐、OAK01b背面偏浅褐；没有把两者称两片黄叶。

## 原始文件逐项来源

下表全部原始文件许可均为 **CC BY 4.0**。8条谱均保留下载原字节，仅简化本地名；3图也未调色、转码或裁切。SHA-256均与FRDR发布的[完整性清单](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/frdr-dfdr-checksums.txt)对应条目一致，详细哈希和字节数在 `data/spectra_new/lotus/manifest.json`。没有下载整个8.8GB数据集。

| Local file | Original source URL | Content and calibration |
|---|---|---|
| `data/spectra_new/lotus/CITATION.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/CITATION.txt) | Original citation text. |
| `data/spectra_new/lotus/Cary5000_CCAN2_R.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Hemispherical%20Data/Cary%205000/CCAN2_R.txt) | Cary 5000; Spectralon / empty holder correction; 2301 rows, 200-2500 nm. |
| `data/spectra_new/lotus/Cary5000_CCAN2_T.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Hemispherical%20Data/Cary%205000/CCAN2_T.txt) | Cary 5000; Spectralon / empty holder correction; 2301 rows, 200-2500 nm. |
| `data/spectra_new/lotus/Cary5000_OAK01_R.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Hemispherical%20Data/Cary%205000/OAK01_R.txt) | Cary 5000; Spectralon / empty holder correction; 2301 rows, 200-2500 nm. |
| `data/spectra_new/lotus/Cary5000_OAK01_T.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Hemispherical%20Data/Cary%205000/OAK01_T.txt) | Cary 5000; Spectralon / empty holder correction; 2301 rows, 200-2500 nm. |
| `data/spectra_new/lotus/Cary5000_OAK01b_R.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Hemispherical%20Data/Cary%205000/OAK01b_R.txt) | Cary 5000; Spectralon / empty holder correction; 2301 rows, 200-2500 nm. |
| `data/spectra_new/lotus/Cary5000_OAK01b_T.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Hemispherical%20Data/Cary%205000/OAK01b_T.txt) | Cary 5000; Spectralon / empty holder correction; 2301 rows, 200-2500 nm. |
| `data/spectra_new/lotus/GoSPo_CCAN2_R.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Hemispherical%20Data/GoSPo/CCAN2_R.txt) | GoSPo angular data approximated to hemisphere; PTFE correction; 1251 rows, 400-1650 nm. |
| `data/spectra_new/lotus/GoSPo_CCAN2_T.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Hemispherical%20Data/GoSPo/CCAN2_T.txt) | GoSPo angular data approximated to hemisphere; PTFE correction; 1251 rows, 400-1650 nm. |
| `data/spectra_new/lotus/LICENSE.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LICENSE.txt) | CC BY 4.0 full legal text. |
| `data/spectra_new/lotus/Leaf Information.xlsx` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Leaf%20Information.xlsx) | Original date/species/traits/color table. Selected Excel rows 204, 277, 278. |
| `data/spectra_new/lotus/README.txt` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/README.txt) | Original sample ID rules, methods, calibration target, fields and license. |
| `photos/lotus/CCAN2.jpg` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Images%20of%20leaves/CCAN2.jpg) | Reflected JPEG for sample identity; no color calibration, no backlight, no RAW. |
| `photos/lotus/OAK01.jpg` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Images%20of%20leaves/OAK01.jpg) | Reflected JPEG for sample identity; no color calibration, no backlight, no RAW. |
| `photos/lotus/OAK01b.jpg` | [Original file](https://www.frdr-dfdr.ca/repo/files/12/published/publication_601/submitted_data/LOTUS/Images%20of%20leaves/OAK01b.jpg) | Reflected JPEG for sample identity; no color calibration, no backlight, no RAW. |

## 派生核查文件

以下为本次从上述原件计算/摘取的整理，随原数据CC BY4.0注明来源；不是作者新增测量或校准证书。

| 文件 | 来源 | 内容 |
|---|---|---|
| `data/spectra_new/lotus/manifest.json` | 上表所有原件及FRDR发布checksum清单 | 逐文件URL、许可、大小、本地及发布SHA-256、核对结果 |
| `data/spectra_new/lotus/validation.json` | 上表8条原始谱 | 行数、波长范围、全谱/可见极值、负值/大于1计数、450/550/650nm数值；配对Cary R+T可见最大值 |
| `data/spectra_new/lotus/selected_sample_metadata.json` | 原始 `Leaf Information.xlsx` | 仅CCAN2、OAK01、OAK01b原表行；Excel日期转换为ISO日期，保留原表行号；未改物性值 |
| `data/spectra_new/lotus/photo_metadata.json` | 三张原JPEG的EXIF与解码 | 尺寸、相机、曝光、WB、ICC有无；非光源标定 |

## 其它核查的边界

- [LOPEX93](https://data.ecosis.org/dataset/leaf-optical-properties-experiment-database--lopex93-)、[ANGERS](https://data.ecosis.org/api/3/action/package_show?id=angers-leaf-optical-properties-database--2003-)已在第2轮报告查过；ANGERS为6月，LOPEX93缺此轮需要的已标记秋黄身份，没有重复交付整套候选。
- [Hovi & Rautiainen 的25种北方树叶/针叶R/T](https://data.mendeley.com/datasets/nvgjcn5nsx/1)，数据CC BY4.0，确含5–10月银桦/欧洲山杨时序；[原论文](https://silvafennica.fi/article/7753)说明10月吸收降低。但已查元数据和原文未给逐样本yellow标签，不能把“10月”直接当黄色身份证明。本分支Mendeley公开API/下载未取得目标原数值；没有保留空文件或声称已得到黄叶谱。
- 本分支无新银杏T数值，也未将夏季绿银杏、其它物种的R/T拼成银杏物性。已有Noda、Morimoto、MapS-Wear没有重新下载凑增量。


