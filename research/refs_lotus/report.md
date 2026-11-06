# 荷花实拍渲染参照下载报告

完成日期：2026-11-05（Asia/Tokyo）。用途为本地外观观察，不发布原照片。

共下载 **34 张互不重复的 JPEG 实拍照片**，按指定的三个目录存放。每个目录包含 `SOURCES.txt`，逐张记录文件名、来源页、许可与链接、作者、实际像素、来源原图像素、下载规格、下载地址、观察重点和 SHA-256。

| 目录 | 张数 | 实际像素范围（宽 × 高） | 内容覆盖 |
| --- | ---: | --- | --- |
| [leaf_water](leaf_water/) | 10 | 1920×1280 至 4665×2624 | 贴水/平浮荷叶、蜡质与掠射反光、叶脉、起伏卷边、水面背景 |
| [leaf_drop](leaf_drop/) | 12 | 1280×960 至 5568×3712 | 单珠和多珠近景，高光、暗边、折射放大的叶脉、叶面细节 |
| [petal](petal/) | 12 | 1600×1200 至 5760×3840 | 粉色与白色，花瓣微距和整朵近景，逆光/透射光，自然背景 |

## 筛选与方案依据

优先选择 Commons 文件页有明确开放许可、摄影者和尺寸记录的真实摄影。本次全部照片均有 Commons 来源页，部分照片从其所列 Flickr / Unsplash 摄影原来源取得原文件。未收录纯保留版权的作品。

已目视筛选拍摄对象与画面，结合来源文字、分类和可用的相机记录排除绘画、雕塑照片、渲染图和明显的睡莲等误标结果。例如搜索中常见的 [Lotus2mq.jpg](https://commons.wikimedia.org/wiki/File:Lotus2mq.jpg) 来源描述明确含 CG，已排除；电脑动画、扫描电镜图以及只有植物远景的图片也未作为最终参照。

## 分辨率与下载限制

实际取得 **7 张摄影来源原文件/原尺寸文件**，其余 **27 张为 Wikimedia 官方标准尺寸缩放版**。没有把缩放版标成原图，也没有本地放大。

原尺寸文件：

- `leaf_water/05_fallen_petals_on_leaf.jpg`：4665×2624；与 Commons 原文件 SHA-1 一致。
- `leaf_drop/02_backlit_drop_leaf_veins.jpg`：5568×3712；与 Commons 原文件 SHA-1 一致。
- `leaf_drop/09_giant_drop_summer_palace.jpg`：1600×1200；与 Commons 原文件 SHA-1 一致。
- `petal/02_pink_petal_inner_macro.jpg`：1600×1200；与 Commons 原文件 SHA-1 一致。
- `petal/03_white_petal_dew_macro.jpg`：4512×2898；与 Commons 原文件 SHA-1 一致。
- `petal/05_pink_translucent_backlight.jpg`：5760×3840；从摄影来源获取，未声称与 Commons 文件字节相同。
- `petal/07_pink_open_flower.jpg`：5184×3456；与 Commons 原文件 SHA-1 一致。

Wikimedia 原文件域名多次返回 HTTP 429；按服务器提示查阅 [官方标准尺寸说明](https://www.mediawiki.org/wiki/Common_thumbnail_sizes)，使用其支持的 3840、1920、1280 像素宽度版本，逐张取不超过来源原宽的最大可用标准尺寸。原始下载地址及原尺寸仍保留于清单，便于以后在可访问时替换。

## 画面适配的实际边界

`leaf_water` 的 01、02、03、05、09 是优先的材质与贴水斜视角参照；04、06、07、08 含较高的俯斜视角，用于补充叶脉、浮水轮廓、卷边和反射关系；10 为水面高度的机位，画面同时包含挺水叶。并非每张都同时具备强水面虚化与全部要求细节，清单已逐张写明，不能将较高机位误认为低机位。

`leaf_drop` 同时保留水珠微距与较宽的近景，便于对照高光/折射和叶脉尺度；并非所有图片都达到显微或 1:1 微距。`petal` 包含花瓣细节、粉白整花和逆光自然背景。

物种以来源页学名/分类及可见形态筛选。少数叶片照片来源只到 Nelumbo 或通称 lotus，未具备标本级物种鉴定证据，已在对应 `SOURCES.txt` 标明；未将此类照片当作独立鉴定证据。

## 许可记录的特别说明

- `leaf_drop/01_barthlott_bead_macro.jpg`：页面 Author 写 Issempa，文件标题另署 © W. Barthlott / Lotus-Salvinia.de，已同时保留，许可按页面 CC BY-SA 4.0 记录。
- `petal/05_pink_translucent_backlight.jpg`：Commons 标记为旧 Unsplash CC0（2015 年作品），同时仍有待许可审核分类；已如实标注此状态，没有把现行 Unsplash 通用许可替代历史许可。

## 验证

- 逐张解码最终 JPEG，核验实际宽高；没有 HTML 错误页伪装成照片。
- 三类均满足 10–14 张；文件 ID 和 SHA-256 均无重复；清单与实际照片逐一对应。
- 查看最终文件生成的联系表并检查重点材质细节；摄影题材、色彩和光照按实际画面核对。

- 图片仅下载到本地；未发布、上传或发送给他人。

已完成上述文件核验与目视检查，并在本目录创建空文件 `DONE`。
