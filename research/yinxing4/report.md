# 背光黄叶颜色参考：第三轮检索与下载

核查日期：2026-11-02。开工前已读 [yinxing2/report.md](../yinxing2/report.md) 和 [yinxing3/report.md](../yinxing3/report.md)。本轮只交付新增材料，没有复制前轮 Noda、Morimoto 或 Mander 示例。

## 结论

**仍没有找到完全满足“黄色秋叶透射拍摄＋同框颜色参考或可核实标定光源”的照片，也没有取得新鲜秋黄银杏的 T(λ)。** 找到一张有**相机响应标定**资料、呈黄色且有透光迹象的槭叶原 TIFF，是本轮最接近的照片；它缺少场景照明标定，不能升级为目标颜色真值。

本轮有实质增量：**LOTUS 公开的黄褐栎叶、浅黄梣叶槭同叶 R/T 原始数值**，带样本身份照片与参考物校正说明。它们不是银杏，照片也不是透射照片。

| 材料 | 实际交付 | 能否当这次颜色真值 |
|---|---|---|
| McGill `pippin0245` | 2560×1920 原 TIFF、原始相机标定 MATLAB 与说明PDF | 有条件的场景外观／相机响应参考；无同框色卡、逐场光源SPD、纯透射证明，且有高光编码上限；**不能直接定黄银杏基色或 T** |
| LOTUS OAK01 / OAK01b | 2019-09-19 黄褐栎叶两面 R/T，各200–2500nm；正反身份照 | 可作秋季采集的黄褐叶物性替代；非金黄银杏，自然衰老原因未逐样本证明 |
| LOTUS CCAN2 | 作者明确浅黄的梣叶槭，Cary及GoSPo R/T；身份照 | 可作黄色阔叶物性参考；**2019-08-21，不证明秋黄状态** |
| HyperspecI 2024 | 原论文图4、Source Data工作簿、限制访问证据 | 只有浅色叶透射示意及任意单位谱；非 T、非公开数值立方体、非已证实秋黄叶 |

推荐用本轮 **LOTUS 实测 T** 补充前轮物性范围，用 McGill TIFF 检查黄色叶片透光、褐斑和重叠阴影的外观。若要严格判定渲染颜色对错，当前证据仍不足：照明SPD、测量几何、物种与叶片状态必须对应，不能把另一物种的半球 T 或经过相机处理的 RGB 当作黄银杏逐像素真值。

## 1. 最接近的照片：McGill 校准相机拍摄的黄叶 TIFF

### 原件、拍法与许可

文件：[photos/mcgill/pippin0245_full_2560x1920.tif](photos/mcgill/pippin0245_full_2560x1920.tif)，14,761,194字节，2560×1920、RGB每通道8位、TIFF内部无压缩、无嵌入ICC。**不是RAW/DNG，也不是已线性化的sRGB。** 原字节未改色、裁切或重编码。

来源：[McGill Foliage 浏览页](https://www.colorscenedatabase.com/Foliage14.html)（实际文件索引也见本地manifest），[官方全尺寸 Foliage ZIP](https://www.colorscenedatabase.com/ZippedFoldersFullImagesStamped/Foliage.zip)，成员 `Foliage/pippin0245.TIF`。仅以HTTP Range提取此成员，ZIP成员CRC通过；完整归档4,030,910,330字节，**未整包下载或验证全包哈希**。网站单图[TIF ZIP](https://www.colorscenedatabase.com/Tifpic/Foliage/pippin0245.zip)实际只有768×576缩小版，本次最终交付的是从全尺寸归档取得的2560×1920版本，缩小版未保留。

[网站许可声明](https://www.colorscenedatabase.com/welcome.html)：图像研究用途免费，**不允许商业用途**，使用须引用 Olmos & Kingdom (2004), *A biologically inspired algorithm for the recovery of shading and reflectance images*, Perception 33:1463–1473。不是CC0或CC BY。标定代码与PDF未找到独立许可，不套用开放代码许可或扩展商业使用权。

实图已打开：在枝黄色、带较多褐斑的掌状裂叶，外形似槭属，叶片相互遮挡，有很亮的透光区域。**黄色及透射分量是目视判断；原记录未给物种鉴定、拍摄日期或纯背光标记**，不能据外形指定槭树种，也不能把全部像素解释为纯 T。未见同框ColorChecker、灰卡、标定白板；背景树干或叶间亮处不是已知参考物。

### 有什么标定、还缺什么

[官方相机说明](https://www.colorscenedatabase.com/backgroundinfo.html)与[校准说明](https://www.colorscenedatabase.com/howtocalibrate.html)：两台 Nikon Coolpix5700 分别称 Pippin、Merry，提供实测相机响应线性化和RGB→LMS转换。标定在实验室进行，使用Macbeth灰阶、光谱辐射计、恒流灯及滤光片测相机响应／光谱灵敏度；**色卡属于相机标定实验，并未出现在这张叶片照片中**。统一设置包含ISO200、f/8、Cloudy白平衡、关闭锐化／降噪等处理；Cloudy是相机设置，不是实测照明。

TIFF的 `ImageDescription = pippin-0.0085763`，给出相机Pippin和曝光0.0085763秒。原程序按 `a_c × (b^code − 1) / 曝光秒数` 线性化，再乘矩阵估计Smith–Pokorny LMS。已在本地按原 `.m` 参数重算，全像素计算有限；没有生成或伪装成标准sRGB、XYZ或绝对 cd/m² 的“校准彩色预览”。作者说明该结果与场景亮度线性相关，**不等于提供了逐场光源、叶片T或绝对色度不确定度**。

原TIFF中红／绿／蓝达到255的像素分别95,895／25,580／0个，占1.951%／0.520%／0；任一通道达到255共115,533个，约**2.351%**。这是文件编码上限，未取得RAW，不能据此定位传感器级饱和；这些高光的颜色不能恢复。未饱和区域仍有8位量化、相机→LMS近似及混合反射／透射的限制。**可以作为带相机响应标定的外观候选，不能当已知光源下的新鲜秋黄银杏颜色真值。**

原 `.m` 中 `rgb2lms.m` 的函数名写为 `rgb2lmsnew`，若用MATLAB需使文件／调用名称一致；本次原件未修改。PDF表中系数与所附程序略有不同，本地数值核查采用所附程序参数，没有混用。

### 文件逐项来源

| 本地文件 | 出处URL／成员 | 许可与性质；拍法／校准信息 |
|---|---|---|
| [原TIFF](photos/mcgill/pippin0245_full_2560x1920.tif) | [官方全尺寸ZIP](https://www.colorscenedatabase.com/ZippedFoldersFullImagesStamped/Foliage.zip)，`Foliage/pippin0245.TIF` | 图像研究免费、不可商用；相机／场景限制见上；非RAW |
| [rgb2linear.m](data/mcgill/rgb2linear.m) | [原ZIP](https://www.colorscenedatabase.com/Extras/rgb2linear.zip)，`rgb2linear.m` | 原始标定代码，无单独开放许可；相机响应／曝光校正，非照片或光源测量 |
| [rgb2lms.m](data/mcgill/rgb2lms.m) | [原ZIP](https://www.colorscenedatabase.com/Extras/rgb2lms.zip)，`rgb2lms.m` | 原始标定代码，无单独开放许可；提供相机RGB→LMS矩阵，非叶片光谱 |
| [McGillCameraCalibration.pdf](data/mcgill/McGillCameraCalibration.pdf) | [官方PDF](https://www.colorscenedatabase.com/Extras/McGillCameraCalibration.pdf) | 原始方法文件，无单独开放许可；相机标定实验，非本场景标定证书 |
| [validation.json](data/mcgill/validation.json) | 上述TIFF与原程序，本地计算 | 本轮生成；位深、曝光、编码上限、系数和计算范围；无新增实验校准 |
| [archive_selection.json](data/mcgill/archive_selection.json) | 上述全尺寸ZIP的目录及成员 | 本轮生成；成员CRC／字节数和选择性下载范围 |
| [manifest.json](data/mcgill/manifest.json) | 上述4个原件及网站许可声明 | 本轮生成；逐文件URL、归档成员、字节数和SHA-256；非校准证书 |

## 2. 新增黄叶同叶 R/T：LOTUS

本轮新增获得 **LOTUS 两片有照片身份对应的黄／黄褐叶样同叶反射／透射数值**；OAK01与OAK01b为同一片叶的两面。没有黄银杏。

- **OAK01 / OAK01b：2019-09-19 的黄褐栎叶（Quercus sp.，原表没有种级鉴定）**。原样本表明确写 OAK01 “yellow brown, shiny”，背面 OAK01b “yellowy, hairy”；原始照片实看为黄褐而非鲜亮金黄。OAK01b 的 `b` 按作者 README 表示同一叶背面，**不是第二片独立叶**。可以作为秋季黄褐栎叶的物性替代，不能冒充黄银杏、纯黄色或逐像素背光颜色真值；没有证明两面仪器测量落在精确同一叶肉点。
- **CCAN2：2019-08-21 的浅黄梣叶槭（Acer negundo L.，Manitoba maple）**。作者论文 Figure 1 说明明确称其 very light yellow，实图也显示整片浅黄色；叶绿素 a+b 3.31655、类胡萝卜素 0.409235 μg/cm²。**日期是8月，原因/自然秋季衰老阶段未注明，不能称秋黄样本。** 作为“黄色阔叶”的低色素极端参考有用。

原始数据和3张身份照片均 **CC BY 4.0**，作者 Reisha D. Peters、Scott D. Noble，数据 [DOI10.20383/103.0606](https://doi.org/10.20383/103.0606)，[FRDR原记录](https://www.frdr-dfdr.ca/repo/dataset/2fb09058-9182-4460-8594-591a4b6a9c61)。论文为 [Peters & Noble 2024, RSE 315:114424](https://doi.org/10.1016/j.rse.2024.114424)。仓库许可原文、README和样本原表已保留。

### 测法与校准

[作者预印本原文](https://harvest.usask.ca/server/api/core/bitstreams/440059d4-47c7-4122-bb56-a1ae34c56451/content) 的 §2.1、§2.2、§2.3.3、Figure 1 及对应数据 README 已实际读取。以下不是由反射照片反推透射率。

- 样品来自 Saskatoon 校园周围树木、花园、温室及农田，采后独立塑料袋置暗冷箱/冰上，光谱和生物物理测量在采后3小时内完成。不是先压干再拍摄。之后的烘干用于干物质量，不等于这里光谱测的是烘干叶。
- **Cary 5000 + diffuse reflectance accessory**：作者称 diffuse hemispherical R/T，垂直照明，200–2500 nm、1 nm输出间距；用 Labsphere 已表征 Spectralon 反射参考校正，并用空样品架透射测量修正小开口/光束尺寸不匹配。**1 nm间距不等于已证明1 nm光谱分辨率**；不额外推断是否包含全部镜面分量。交付的每条Cary曲线2301行，两个数字列依次为波长nm、无量纲 R 或 T（0.4为40%）。
- **GoSPo（仅选 CCAN2 的已积分 R/T）**：原始双向测量以垂直照明、天顶平面5°角间隔采集，再近似积分为半球量。校准目标是已表征的100μm PTFE薄片；实物文件400–1650nm、1nm输出、1251行。它与Cary是不同几何和积分方法，不能当成重复测量后随意平均；未将近似积分曲线称绝对角分布或相机像素。
- **没有交付逐样本原始白/暗读数、Spectralon校准证书、不确定度、光源SPD、响应校正表**。上述只说明作者采用参考物校正的实测物性，不能宣称计量溯源完备。给定光源SPD后可计算 `SPD×T(λ)` 的颜色；不能用 T 本身当亮度或将半球T直接当某方向的背光像素。
- 原始UV透射含少量负值，全部原样保留。Cary可见区400–700nm所选R/T无负值，同面R+T均未超过1；具体极值及全部异常数见 validation.json。未裁零、平滑、重新归一化。

### 照片仅证明叶色和样本身份

三图已完整解码并实际查看。均4032×3024 JPEG（EXIF Orientation=6，显示为竖图），Apple **iPhone SE**、4.15mm f/2.2、ISO25、1/60s、自动白平衡、EXIF标记sRGB、无嵌入ICC；不是RAW/DNG。拍摄时间分别2019-08-21及2019-09-19，与样本表一致。作者明确将叶平放浅色表面、固定相机高度，地面校准/映射供叶面积计算。实图可见纸面、相机支架及手绘1cm格线；**这是反射外观照，不是背光图**。

纸面没有声明为已校准白板/灰卡，未见ColorChecker；光源未标型号/色温/SPD，面积校准也不是色度校准。故三图均不能取RGB当颜色真值。照片和光谱按同名叶ID匹配，仍不构成同一画面上的透射校准。OAK01正面偏黄褐、OAK01b背面偏浅褐；没有把两者称两片黄叶。

### 原始文件逐项来源

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

### 派生核查文件

以下为本次从上述原件计算/摘取的整理，随原数据CC BY4.0注明来源；不是作者新增测量或校准证书。

| 文件 | 来源 | 内容 |
|---|---|---|
| `data/spectra_new/lotus/manifest.json` | 上表所有原件及FRDR发布checksum清单 | 逐文件URL、许可、大小、本地及发布SHA-256、核对结果 |
| `data/spectra_new/lotus/validation.json` | 上表8条原始谱 | 行数、波长范围、全谱/可见极值、负值/大于1计数、450/550/650nm数值；配对Cary R+T可见最大值 |
| `data/spectra_new/lotus/selected_sample_metadata.json` | 原始 `Leaf Information.xlsx` | 仅CCAN2、OAK01、OAK01b原表行；Excel日期转换为ISO日期，保留原表行号；未改物性值 |
| `data/spectra_new/lotus/photo_metadata.json` | 三张原JPEG的EXIF与解码 | 尺寸、相机、曝光、WB、ICC有无；非光源标定 |


可直接核对的 Cary 5000 T 值（无量纲比例，非RGB；完整原谱才是交付数据）：

| 样本／照明叶面标识 | T450nm | T550nm | T650nm |
|---|---:|---:|---:|
| CCAN2 | 0.19548 | 0.43630 | 0.44372 |
| OAK01 | 0.021636 | 0.14041 | 0.24096 |
| OAK01b | 0.018022 | 0.12785 | 0.23538 |

同一叶两面的半球R/T可以约束物性，但不等于朝相机方向的透射辐亮度。要算约定光源下的颜色，须用该光源SPD乘T再与标准观察者积分；不能把上表三波长当RGB，也不能把CCAN2的T与另一张黄银杏照片拼成同叶真值。

## 3. 新空间透射线索：HyperspecI 2024，未取得目标立方体

Bian 等，*A broadband hyperspectral image sensor with high spatio-temporal resolution*，[原论文](https://doi.org/10.1038/s41586-024-08109-1)，[原全文XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11541218/fullTextXML)。图4已实际打开，最左叶浅黄／米色，另两片黄绿及绿色；LED从叶背照明。但**原文未给这几片叶的物种、采收日或秋季状态**。

传感器响应矩阵有单色仪／功率计标定；叶片模式未提供LED型号、实测SPD、同框色卡、RGB相机RAW或逐叶白暗参考。工作簿 Fig4b 光源和叶片谱各61点，400–1000nm、10nm间隔，但两者都单独达到最大值1，列头为 `Intensity (a.u.)`；Fig4d三叶谱也为任意单位。没有共同曝光／增益尺度证明，**不可相除冒充绝对 T**。未给它们导出所谓T或“真值颜色”。

[作者仓库](https://github.com/bianlab/Hyperspectral-imaging-dataset)要求向所有者取得链接；[ScienceDB记录](https://www.scidb.cn/en/detail?dataSetId=f9a0d077d12d478d81df5ec0358c6a0f)，DOI[10.57760/sciencedb.18287](https://doi.org/10.57760/sciencedb.18287)，页面JSON-LD明确 `conditionsOfAccess = RESTRICTED`、license空。**未取得数值立方体，未申请或联系作者**。

| 本地文件 | 原始出处URL | 许可；拍法／校准／真值适用性 |
|---|---|---|
| [HyperspecI_2024_Fig4_original.png](data/spatial_new/HyperspecI_2024_Fig4_original.png) | [出版社原图](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-024-08109-1/MediaObjects/41586_2024_8109_Fig4_HTML.png) | 论文CC BY-NC-ND4.0；完整原图未修改；仅供核查实验／叶色，**非独立原照片、非T真值** |
| [HyperspecI_2024_SourceData_Fig4.xlsx](data/spatial_new/HyperspecI_2024_SourceData_Fig4.xlsx) | [出版社原工作簿](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-08109-1/MediaObjects/41586_2024_8109_MOESM5_ESM.xlsx) | 随论文CC BY-NC-ND4.0，未见另行许可；3表原字节，a.u.谱，不是透射率 |
| [sciencedb_access_evidence.json](data/spatial_new/sciencedb_access_evidence.json) | 上述ScienceDB页面JSON-LD选存 | 本次摘取的访问限制元数据；源license空，无实验／颜色校准 |
| [validation.json](data/spatial_new/validation.json) | 上述XLSX本地解析 | 本次生成；维度、单位与最大值核查，无校准效力 |
| [manifest.json](data/spatial_new/manifest.json) | 上述原图、工作簿、元数据及本地计算 | 本次生成；每文件来源、许可、大小及SHA-256 |

未保留整篇补充PDF、其它无关实验图或无法用作本任务的立方体占位文件。更详细的核查依据在 [data/spatial_findings.md](data/spatial_findings.md)。

## 4. 照片检索覆盖与未采用的路线

这里记录实际检查范围，**不是证明全网或整个数据集没有目标**。优先区分透射几何、叶色身份与颜色校准，普通白底、形态尺度标记、已设白平衡或有相机型号都不自动等于真值。

| 来源／本轮动作 | 结果与停止依据 |
|---|---|
| [raw.pixls.us](https://raw.pixls.us/)，读取[公开2020条清单](https://raw.pixls.us/json/getrepository.php?set=all) | 对描述列搜leaf/leaves/autumn/foliage/ginkgo/backlit/lightbox/maple等无命中；厂牌“Leaf”不是叶片主题。描述稀疏，**未目视穷查2020张RAW**。站点明确不征集色卡照片，此路线没有取得目标。记录见 `data/raw_pixls_check.json` |
| [McGill Foliage](https://www.colorscenedatabase.com/Foliage1.html) | 20页共320缩略图目视筛查；放大检查pippin0245、pippin_park0027、merry0131、Merry_0019_Lasalle，最后仅保留最接近的pippin0245完整TIFF，限制见§1 |
| [Gehler／Shi–Funt官方](https://www.cs.sfu.ca/~colour/data/shi_gehler/) | 查看568幅FFCC缩略图，另检查9幅带色卡的全尺寸候选：有远景秋色树，但没有可确认黄色单叶透射的候选；未把黄花当黄叶。缩略图来自[第三方FFCC镜像](https://github.com/shuwei666/ffcc-python)，9图来自[研究作者镜像](https://huggingface.co/datasets/StevenChangWei/gehler-dataset/tree/main/images)，**未与SFU原件逐字节核对，也未把镜像代码许可当照片许可** |
| [Cube++官方](https://github.com/Visillect/CubePlusPlus)，[Zenodo](https://zenodo.org/records/4153431)，CC BY4.0 | 每幅含SpyderCube且有CR2。读取markup的EXIF／场景标签后，提取查看33幅11月白天室外JPEG：以晚秋城市、裸枝为主，未找到目标；**未查全4890幅，也未下载无目标的CR2**。33成员CRC验证，不宣称整JPG ZIP哈希验证 |
| [Untreated leaf image dataset](https://zenodo.org/records/7070266)，[论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10358950/)，CC BY4.0 | 确认Canon EOS M6II＋Sinkohsha SV530A*STD-1216U透射灯台。ArUco及蓝方块用于形态／面积标定，并非色卡。3.92GB tar.gz顺序抽查12张Morella_rubra，均绿色；继续读取时发生JPEG解码错误，停止，**未检查其余物种，不能说479叶全无黄叶**。原文未给颜色／SPD标定，不下载整包凑数 |
| Commons／Flickr原作者及Pixls照片 | 按yellow/autumn/backlit＋ColorChecker/灰卡/灯箱等组合检索，没有找到新增可核实、同时满足条件的公开原照片；结果中的普通背光照、泛称灯箱或后期增强黄色不能补缺。前轮Franz灯箱干银杏、Smallrig背侧光帖子已排除，不重复交付 |

其它新空间数据的排除依据：

- [LeafSpec-Dicot 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10098794/)确有卤素灯和白参考校正的整叶透射成像，但作者明确不分享数据，未取得cube。
- [Wei等2023榆树病叶](https://www.fs.usda.gov/nrs/pubs/jrnl/2023/nrs_2023_wei_001.pdf)，[DOI](https://doi.org/10.1016/j.aiia.2023.09.003)，数据仅合理请求后提供；病叶不自动等于秋黄叶。
- [番茄透射数据](https://zenodo.org/records/10498387)标Files Restricted，且为9点采谱，不能叫空间立方体。
- [公开拟南芥／烟草高光谱](https://figshare.com/articles/dataset/Hyperspectral_images_of_Arabidopsis_thaliana_and_Nicotiana_benthamiana_leaves/30402409)的[原始方法](https://www.bio-protocol.org/en/bpdetail?id=5541&pos=q&type=0)区分反射高光谱与660nm透射光度计，不能混称秋黄透射cube。
- [LOPEX93](https://data.ecosis.org/dataset/leaf-optical-properties-experiment-database--lopex93-)／ANGERS前轮已有调查，没有新增可确认的黄秋叶身份文件；[Hovi北方树叶时序](https://data.mendeley.com/datasets/nvgjcn5nsx/1)虽含10月测量，未取得带yellow逐样本身份的目标数值。本轮不以月份或低叶绿素单独判黄，不重复交付整套旧候选。

同框色标路线的逐ID、镜像来源、许可和筛查范围保存在 [data/calibrated_scenes_findings.md](data/calibrated_scenes_findings.md)。

## 5. Mander 2021

[Mander Dryad](https://doi.org/10.5061/dryad.7h44j0zsj)本轮未发现新公开下载路径，原文件入口仍403，完整包未取得，不重复前轮示例。

## 6. 完整性、辅助文件与交付边界

- McGill全尺寸TIFF实际解码并目视，ZIP成员CRC通过，原始标定代码静态读取、按其方程核查计算；未执行来源代码中的网络操作，未将图片另行调色。
- LOTUS的15个原始文件（8谱、3照、4份说明／样本／许可资料）SHA-256均与FRDR发布清单匹配；全部数值谱解析，Cary各2301点、GoSPo各1251点。400–700nm无负值，Cary同面R+T不超过1；全谱UV负值保留。3张照片逐张目视，均为反射身份照。
- HyperspecI原图已查看、XLSX已解析；无数值空间cube，没有将a.u.光谱、论文显示图或色标指数转写成T。
- 没有新增黄银杏T、RAW/DNG，或严格符合照明标定条件的秋黄透射照片。近似材料的缺口没有通过照片取色、跨物种／跨叶拼配或猜光源来填补。

以下均为本轮生成的辅助记录，不是原始实验或校准证书。它们的出处是本文相应外部来源及本地核验，未从外部获得独立许可；其中引用／摘录材料仍受所列来源许可约束。

| 文件 | 来源／作用 |
|---|---|
| [data/raw_pixls_check.json](data/raw_pixls_check.json) | raw.pixls.us清单URL、2020条描述检索与范围限制 |
| [data/additional_search_checks.json](data/additional_search_checks.json) | McGill320缩略图／4放大候选与Kyushu12张绿色抽查、错误及未查范围 |
| [data/spectra_findings.md](data/spectra_findings.md) | LOTUS原论文／FRDR／原表／本地解码的详细研究记录 |
| [data/spatial_findings.md](data/spatial_findings.md) | HyperspecI原论文／Source Data／ScienceDB及其它空间候选核查 |
| [data/calibrated_scenes_findings.md](data/calibrated_scenes_findings.md) | Gehler／Cube++官方及镜像来源、实际筛查范围 |
| [data/file_checksums.json](data/file_checksums.json) | 全体交付文件（此索引自身除外）的字节数与本地SHA-256；不是上游发布校验值 |
| [report.md](report.md) | 本次综合报告，逐项外部证据在相应位置给出 |


