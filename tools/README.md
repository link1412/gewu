# tools

- `arc.py`:量画面里那道弧的矢高、弧顶和落在弧上的列占比。`--film` 量全片。
- `seams.py`:找线性帧里笔直的亮度跳变,用来发现矩形暗块和接缝。

```sh
python3 -I tools/arc.py IMAGE...
python3 -I tools/arc.py --film
python3 -I tools/seams.py 'out/v2/*/final.linear.npy'
```
