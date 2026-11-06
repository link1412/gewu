# 参数与光谱数据

- mechanism_parameters.csv：27条参数；保留实测、推断、转引、模拟设定的区别，包含页/图和来源URL。M1=Dejoie2014，M2=Fukushima2022，M3=海老塚/岡本2023，M4=Feng2023，M6=Shi2019；其余采用作者/对象名。证据局限见根目录report.md。
- querry1985_hematite_o_380-780nm.csv：α-Fe₂O₃ ordinary。
- querry1985_hematite_e_380-780nm.csv：α-Fe₂O₃ extraordinary。
- querry1985_magnetite_380-780nm.csv：Fe₃O₄。
- yamasaki1994_sherd_glaze_wt_percent.csv：古代建窑窑址片釉的化学组成，不是稻叶；原文索引转写，PDF视觉校核待完成，未归一化。
- pbrt_optics/：上述三份n/k的六份波长–数值SPD文件；格式转换已核对，未渲染测试。

n/k CSV中波长单位为nm，n、k无量纲；范围380–780nm，原间隔10nm，未插值。数据许可为CC0，原始文献追溯与未核事项见optical_data_README.md。

没有稻叶原件的校准反射率CSV、BRDF、膜厚分布或ε相nk；缺失数据没有补造。这里也没有把照片RGB转成所谓实测光谱。
