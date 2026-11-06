# 同画面色标自然场景路线核查

核查日期：2026-11-02。**本路线未找到可确认的背光秋黄叶近照。没有将不合格候选保存到 photos/。** 本文件是本次整理的研究记录，不是原始实验数据或校准证书。

## Gehler / Shi–Funt ColorChecker

- [SFU 官方数据说明](https://www.cs.sfu.ca/~colour/data/shi_gehler/)：568幅室内外场景，Canon 1D / 5D，每幅含 MacBeth ColorChecker，原始拍摄为 Canon RAW。SFU公开的是从RAW变换的12-bit值线性PNG（用16-bit容器），Canon 5D需减黑电平129、1D为0；不能把PNG直接当sRGB。场景光源RGB由不饱和中性色块测量。**有色卡与RAW来源并不保证场景中存在秋黄叶或透射光。** 官方说明页只要求引用研究，未见明确CC许可；不得套用代码库许可证给原始照片。
- [Google FFCC 官方仓库/预处理说明](https://github.com/google/ffcc/blob/master/data/get_shi_gehler.sh)及[导入代码](https://github.com/google/ffcc/blob/master/scripts/GehlerShiImportData.m)说明：其预处理会屏蔽色卡/饱和像素，并产生缩略图、照明RGB、相机与CCM等文件。这种小图适合筛场景，不能交付为同画面保留色卡的真值照片。
- 实际用于快速全体筛选的是[shuwei666/ffcc-python](https://github.com/shuwei666/ffcc-python)，[下载ZIP](https://codeload.github.com/shuwei666/ffcc-python/zip/refs/heads/main)，下载时提交`334461b8c88c312c561018cf1832110a67d8e76b`。它是**第三方FFCC缩略图镜像**，不是原摄影作者来源。实际查看其568张约64像素缩略图的四张联系表；只为识别场景，按配套照明RGB除通道并施加显示gamma，未将其当色度测量。
- 再从[2025 GCC论文作者公开的Gehler镜像](https://huggingface.co/datasets/StevenChangWei/gehler-dataset/tree/main/images)临时取得9张带色卡全尺寸PNG，实际解码/查看：`8D5U5564.png`、`8D5U5565.png`、`8D5U5607.png`、`8D5U5608.png`、`8D5U5614.png`、`IMG_0448.png`、`IMG_0453.png`、`IMG_0767.png`、`IMG_0815.png`。各文件URL为`https://huggingface.co/datasets/StevenChangWei/gehler-dataset/resolve/main/images/`加上述文件名。作者[元数据URL](https://huggingface.co/datasets/StevenChangWei/gehler-dataset/resolve/main/all_cameras_meta.json)提供相机、照明与色卡区域。镜像README的Apache标签不能消除原始照片授权不明；未作为许可证明。
- 结果：5565/0453/0767明显黄色部分主要是花；0448/0815为绿叶；5614为厨房。5564有泛黄庭院叶，5607/5608有秋色远景树和同画面色卡，但**缺少可解析的黄色单叶、透射几何和同照明证明**，不能据此当背光黄叶颜色真值。这9张仅用于排除，不留入交付照片。
- 确认[SFU原Canon1D ZIP](https://www.cs.sfu.ca/~colour/data2/shi_gehler/png_canon1d.zip)支持HTTP Range（总长690,128,673字节）；若未来有明确文件候选可只取成员，无需全包。没有把成功读取ZIP尾部说成下载或检查了完整原始包。9张镜像只用于核查，没有逐字节对比SFU原件。

**范围限制：** 568张缩略图已目视筛选，但没有逐张检查全部原始RAW；缩略图可能漏掉小面积黄叶。没有发现明确目标，不宣称该数据集绝对不存在目标。

## Cube++

- [作者官方仓库](https://github.com/Visillect/CubePlusPlus)、[Zenodo记录4153431](https://zenodo.org/records/4153431)：4890张Canon550D/600D场景，每张有SpyderCube，提供原始CR2、16-bit线性PNG、JPEG、色标左右面照明RGB和EXIF。许可明确 **CC BY 4.0**。左右面色标用于估计不同方向照明；不是叶片透射白参考或光源SPD。
- 下载[原markup.zip](https://zenodo.org/api/records/4153431/files/markup.zip/content)（19,957,846字节）到临时目录，读取properties.csv与全部EXIF以确定季节候选。EXIF九/十/十一月共291张；其中标注outdoor且day的只有33张，均2019年11月。这是基于数据EXIF与人工场景标签的筛选，不是逐叶物候标注。
- [官方JPG ZIP](https://zenodo.org/api/records/4153431/files/JPG.zip/content)总长2,585,933,813字节；HTTP Range读取中央目录及33个成员，分别验证成员ZIP CRC，未下载整包、未宣称校验全ZIP。实际目视看联系表：以晚秋城市建筑、裸枝及少量地面落叶为主，未找到背光黄色单叶。JPEG仅作作者定义的visualization，不能当线性RAW。
- 已检查33个ID：`01_7782, 01_7785, 01_7787, 01_7793, 01_7796, 01_7797, 01_7799, 01_7802, 01_7807, 01_7808, 01_7813, 01_7828, 01_7831, 01_7833, 01_7837, 01_7844, 01_7845, 01_7852, 01_7854, 01_7855, 01_7858, 01_7859, 01_7907, 01_7922, 01_7927, 01_7998, 01_8001, 01_8002, 01_8005, 01_8008, 01_8009, 01_8031, 01_8038`。ZIP成员为`Cube++/JPG/{ID}.jpg`。
- **没有检查全部4890幅图，也没有检查日期/标签不可靠的全部图，故不是穷尽否定。** SimpleCube++已裁掉色标，不选作同画面色卡照片。


