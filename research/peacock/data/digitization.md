# 光谱提取与验证说明

所有脚本离线处理已下载的原始文件，不访问网络。环境：Python 3.13，PyMuPDF、NumPy、Pillow；`scipy` 不影响本交付脚本。重算时在项目根目录运行：

```sh
python scripts/digitize_spectra.py
python scripts/digitize_yoshioka_angles.py
python data/spectra_prepare.py
python scripts/measure_geometry_figure.py
```

- Kane2019：作者 XLSX 的 ZIP/XML 直接读表，未增加平滑；删除5个逐点重复列；percent除100得到fraction；1nm表间隔不是1nm独立仪器分辨率。源表及其完整列CSV保留。
- Dakin2013 Fig2：9条矢量折线，每条401顶点；由PDF文字刻度/矢量坐标标定。300–700nm，percent；细节见对应metadata。30/45/60是宏观灯对正面观察方向的夹角，不是局部表面的对称镜面入射角。
- Freyer2020 Fig5：PDF第10页第一个原始嵌入JPEG，1331x710；每面板用实际刻度位置标定（边框超出300和900nm刻度，不把边框直接当300/900）。用粗线RGB与细线区分，每列取最接近目标颜色的线心，再线性采样5nm。只取7条探头粗线，排除MSP细线；数据为fraction，保留作者已除4的值。原图、校准JSON、黑点叠加图齐备。保守数字化误差±3–5nm、各面板显示满量程±1–2%，不是实验误差。
- Zi2003 Fig2A：本地PDF第3页彩色矢量折线；x_pdf=70.819→425nm、278.919→750nm；y_pdf=175.591→0、55.045→0.6。仅选该面板的四种线色，避免混入Fig4模拟谱。重复x均值再5nm线性采样，不超出原线范围；绿线450nm起。导出fraction；保守排版读取误差±1nm/±0.005R，非实验误差。
- Yoshioka2002 Fig2：原始1-bit扫描图4560x3358，内部像素白色代表墨迹；基线y2744。左面板x400=469、x700=2082；右面板2666/4280。只接受每列可分离出8条曲线且排除文字、坐标轴的点，因此输出只是可辨识局部谱段。用同面板15°曲线采样最大值设为1、轴基线为0，没有逐曲线归一化；不同面板强度不可比较。局部扫描线宽约2–8nm；以5nm采样不要视为5nm光谱分辨率。`angular_peaks.csv`仅是采样范围内最大值；`peak_inside_resolved_range=False`是边界截断，不能作为真实峰位。此表属于非眼斑部位的辅助证据，主要角度基准应使用Dakin。

目视验证：Freyer每个面板的提取点落在粗线上；R6两条曲线未与细MSP混淆。Zi四条提取点叠在原矢量线上。Yoshioka有点的部分位于原曲线，合并处未强行补齐。Dakin与Kane由CSV重绘并对照原图，主峰、副峰、角度线型和振幅一致。图形位数不代表实验精度。

`artifact_manifest.csv` 保存最终资料的大小、PDF页数、图像像素、CSV行列数及SHA-256，排除清单自身。`validation.json` 记录交付检查结果。
