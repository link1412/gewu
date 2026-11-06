> 已放弃的第一代方案(S1–S10),保留当时的状态,片子没有用上。这里的路径相对 `v1/`。放弃的原因见 `docs/STACK.md`。脚本假定当时的目录和渲染机器,不能直接运行。文档里提到的 `CLAUDE.md`、`HANDOFF.md`、`PROGRESS.md`、`TODO.md` 没有收录。

# 格物

Claude Opus 5.5 发布片的东方艺术版本:37 个镜头,每个镜头是一件东方的器物或一门手艺,它的美来自一个物理现象。
每个镜头逐帧对齐原片的剪辑点和画面里那道凸弧,能和原片并排比。

- 设计:`DESIGN.md`

## 怎么跑

- 量原片(原片放在 `ref/opus55.mp4`,不进 git):`python3 -I tools/spec_measure.py ref/opus55.mp4 spec/shots.json`
- 生成取景模板:`python3 -I tools/compare.py guide out/guide`
- 并排比(左半原片、右半我们的):`python3 -I tools/compare.py seam out/cmp/seam.mp4`
- 第 6 镜的开片:`python3 -I shots/06-guan/crackle.py --out out/06/crackle.json --preview out/06/crackle.png`
- 渲染器:打了补丁的 pbrt-v4。上游 b4ce968 放在 `third_party/pbrt-v4`,打上 `patches/pbrt-v4-gewu.patch`,补丁做什么见 `docs/rnee.md`。构建(静态):`cmake -S third_party/pbrt-v4 -B third_party/pbrt-build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DCMAKE_DISABLE_FIND_PACKAGE_OpenEXR=ON -DCMAKE_DISABLE_FIND_PACKAGE_Imath=ON -DOPENEXR_FORCE_INTERNAL_DEFLATE=ON -DOPENEXR_FORCE_INTERNAL_IMATH=ON -DCMAKE_DISABLE_FIND_PACKAGE_libdeflate=ON`,再 `ninja -C third_party/pbrt-build -j 6 pbrt_exe imgtool`。

## 依赖

- Python 3,numpy,scipy,Pillow
- ffmpeg
- cmake,ninja(构建 pbrt)
