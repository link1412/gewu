# 黄银杏叶照片补充调查

调查日期：2026-11-02。下载的三个文件均为 Commons 所列 **Original file** 的原字节文件，未裁切、调色或重新编码；已实际打开检查。`checksums.json` 记录大小、SHA-1、SHA-256。三张文件的 SHA-1 与 Commons 页面给出的值一致。

结论：找到有详细拍摄/处理记录的**在枝黄银杏透射照片**，以及可看斑点、细条纹和局部褐边的高清在枝照片、秋叶扫描。**没有找到公开可直接下载、带色卡/透射白参考、可作绝对颜色真值的新鲜黄银杏透射照片或相应 RAW。** 已知白平衡设置、ICC 或扫描仪型号不能替代光源光谱与色度标定。

## 1. 黄色在枝银杏，明确阳光透射，3028 × 3028

- 路径：`photos/supplementary/ginkgo_yellow_sun_transmission_Franz_van_Duns_2021.jpg`，3,129,292 字节。
- [来源与作者拍摄说明](https://commons.wikimedia.org/wiki/File:DSG7056-1_Yellow_Ginkgo_biloba_leaves_-_vivid_translucent_illumination_by_autumn_sunlight.jpg)；[原图 URL](https://upload.wikimedia.org/wikipedia/commons/5/52/DSG7056-1_Yellow_Ginkgo_biloba_leaves_-_vivid_translucent_illumination_by_autumn_sunlight.jpg)。作者：Franz van Duns。许可：[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)，复用须署名，改编须按许可处理。
- 拍法：2021-10-22，德国 Dortmund；仍连在同一枝条上的黄叶，作者明确称秋日阳光透射。Sony Alpha 7R IV，FE 200–600 mm 镜头，400 mm、ISO 800、1/2000 s、f/7.1、曝光补偿 −1.3 EV；相机白平衡 5600 K。来源说明曾同时拍 JPEG 与 ARW，但**仅此 JPEG 公开，未找到 ARW 下载**。
- 处理：Lightroom 色温 5700 K、tint +13、texture +50、clarity +30、vibrance +10、saturation +3，并有非线性色调曲线；TIFF 中间文件后经 Photoshop 裁切成 JPEG。以上为作者记录，不能把 WB 数值当成实测日光色温。文件实际嵌入 `sRGB IEC61966-2.1` ICC（`sips` 检查）。
- 校准：无同场色卡、无白/灰参考、无光源 SPD/照度；后期已改对比度和饱和度。**只能作透射外观、脉序和重叠阴影参考，不能取色当真值**。
- 比例：作者称最上叶宽约 **80 mm**，可粗定尺度；无同平面实体尺，叶片弯曲、倾斜，不宜用作精密毫米标定。
- 新鲜性与细节：叶仍在枝上（来源文字和图像均支持），不属干燥标本。实际图可见放射条纹、细脉和重叠阴影；褐斑较少，边缘高光局部很亮。

## 2. 高清在枝黄叶，斑点与局部褐边，4032 × 3024

- 路径：`photos/supplementary/ginkgo_turning_yellow_Famartin_2020.jpg`，1,809,873 字节。
- [来源](https://commons.wikimedia.org/wiki/File:2020-10-24_13_13_22_Ginkgo_leaf_turning_yellow_in_autumn_at_the_Franklin_Farm_Village_Shopping_Center_in_the_Franklin_Farm_section_of_Oak_Hill,_Fairfax_County,_Virginia.jpg)；[原图 URL](https://upload.wikimedia.org/wikipedia/commons/5/57/2020-10-24_13_13_22_Ginkgo_leaf_turning_yellow_in_autumn_at_the_Franklin_Farm_Village_Shopping_Center_in_the_Franklin_Farm_section_of_Oak_Hill%2C_Fairfax_County%2C_Virginia.jpg)。作者：Famartin。许可：[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。
- 拍法：2020-10-24，Virginia Franklin Farm，室外在树黄叶近照；iPhone X、4 mm、f/1.8、1/2114 s、ISO 20、自动曝光、自动 WB、无闪光；JPEG。文件实际嵌入 **Display P3** ICC（`sips` 检查），不要无视 ICC 直接按 sRGB 读 RGB 数值。
- 校准：无色卡、白参考、RAW、光源实测色温/SPD；**作者未明确说背光，单凭图像不能确认是纯透射**，保留作形态补充，不作为已校准透射图。
- 比例：无尺、未知叶宽，不能定毫米比例；EXIF 的 72 dpi 不能用来算叶片实物大小。
- 新鲜性与细节：图中叶柄连接树枝，支持在枝新鲜秋叶；实际打开可清楚看叶肉细条纹、小褐斑、轻微残绿和局部边缘褐损。不是扫描、压叶或干叶。

## 3. 单片变黄银杏扫描，1552 × 1944

- 路径：`photos/supplementary/ginkgo_autumn_scan_Ninjatacoshell_2008.jpg`，430,760 字节。
- [来源](https://commons.wikimedia.org/wiki/File:Autumn_Ginkgo_Leaf.jpg)；[原图 URL](https://upload.wikimedia.org/wikipedia/commons/4/4c/Autumn_Ginkgo_Leaf.jpg)。作者：Ninjatacoshell。页面双许可，选用 [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)（另有 GFDL）。
- 拍法：2008-11-07，Brigham Young University 校园取得的秋季变色叶；Canon **CanoScan LiDE 70**；EXIF 600 × 600 dpi、自动 WB、Paint.NET v3.05；公开文件为 JPEG，实际嵌入 `sRGB IEC61966-2.1` ICC。**页面只确认扫描，未称透射模式**，因此不算已知透射扫描。
- 校准：无色卡、白参考测量、RAW、扫描色度标定文件或灯光 SPD。白底不等于可追溯透射白参考。
- 比例：没有实体尺。若 600 dpi 是未经缩放的真实采样分辨率，则每像素约 **0.0423 mm**、整幅约 65.7 × 82.3 mm；但文件经过编辑，未核实是否缩放，**只能有条件粗估，不是确定尺度**。
- 新鲜性与细节：来源说秋天变色叶，未提供采后时长、含水或是否干燥处理；**不能保证新鲜**。图像能看黄绿过渡、放射细脉、斑和较暗边缘，可作纹理/形态参考。

## 查过但未下载/未满足的候选

- [Leafsnap 官方数据页](https://leafsnap.com/dataset/)：说明 lab 叶片为 Smithsonian **pressed leaves**，含 controlled backlit/front-lit 两种，银杏有 120 张 lab + 21 张 field。页面未给出可核实开放许可，README 下载本次返回 HTTP 403；压叶也不等于新鲜秋叶，故没有为凑数下载约 977 MB 数据包。仅凭背景白色也无法证明光源/色度校准。
- [HALVS 作者仓库](https://github.com/WeizhenLiuBioinform/HALVS-Hierarchical-Vein-Segment)：大豆、甜樱桃、悬铃木未经化学处理的透射扫描；完整数据要求签用户协议并通过邮件申请。该来源没有可直接获取且许可明确的目标原图，不下载。论文/仓库只能作已知扫描方案线索，不能算已交付图像。
- [Gingo biloba leaves scan](https://commons.wikimedia.org/wiki/File:Gingo_biloba_leaves_scan.jpg)：作者明确是采集约两周后的 **dry** leaves，尽管有 CanoScan LiDE 25 / 300 dpi 记录和公有领域声明，不符合新鲜黄叶优先目标，未下载。
- [Public Domain Pictures 的 green ginkgo biloba leaves changing](https://www.publicdomainpictures.net/en/view-image.php?image=375672&picture=green-ginkgo-biloba-leaves-changing)：免费版本仅 1280 × 1920，4000 × 6000 原图须登录付费；无校准或尺度，未购买、未下载。


