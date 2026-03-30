# 一、网络拓扑对比可视化

## 1. 项目简介

本脚本用于对同一基因（例如某个 VJ 组合）在 **Pre** 与 **Post** 两个条件下的网络拓扑结构进行叠加展示与比较。核心目标是：

- 在**统一布局**下比较 Pre 和 Post 网络；
- 用**节点大小**表示克隆丰度（clone size）；
- 用**节点颜色/扇形比例**表示该节点是：
  - 仅存在于 Pre；
  - 仅存在于 Post；
  - 同时存在于 Pre 和 Post；
- 输出主图和独立图例，便于论文作图与结果展示。

该脚本特别适合用于展示免疫组库或受体网络在干预前后、处理前后、治疗前后等场景中的拓扑变化。


---

## 2. 分析思路

整体流程如下：

1. **读取 Pre 和 Post 的网络 JSON 文件**
   - JSON 中包含：
     - `nodes`：节点信息；
     - `links`：边信息。
   - 每个节点至少需要有 `id`，可选 `label`；
   - 每条边至少需要有 `source` 和 `target`，可选 `weight`。

2. **读取 clone size 矩阵**
   - 从 `Matrix/Pre/*.csv` 和 `Matrix/Post/*.csv` 中读取丰度矩阵；
   - 行索引为 `CDR3(pep)`；
   - 程序会根据图中节点的 `label` 去匹配矩阵中的对应行，并对该行求和，得到该节点的 clone size。

3. **构建 Pre 与 Post 的并集网络**
   - 将两个时间点/条件下的网络合并成一个 union graph；
   - 后续布局只计算一次，保证 Pre 和 Post 使用同一套节点坐标。

4. **统一布局并压缩到圆盘内**
   - 先用 `kamada_kawai_layout` 生成全局布局；
   - 再将所有节点坐标标准化到一个圆盘区域内，便于生成紧凑、美观且可比较的网络图。

5. **绘制节点**
   - **Pre-only 节点**：单色填充；
   - **Post-only 节点**：单色填充；
   - **Pre & Post 共有节点**：绘制成饼图节点（pie node），两部分面积比例分别表示该节点在 Pre 和 Post 的相对丰度。

6. **绘制边与圆盘边界**
   - 边基于 union graph 绘制；
   - 使用圆盘边界进行裁剪，使图像规整。

7. **导出图像**
   - 主图：Pre/Post 拓扑叠加图；
   - 图例 1：节点大小说明；
   - 图例 2：节点类型说明。

---

## 3. 输入文件格式

### 3.1 网络文件（JSON）

脚本要求 Pre 和 Post 各有一个 JSON 文件，例如：

```bash
./networkText/Pre/TRAV13-1;TRAJ36.json
./networkText/Post/TRAV13-1;TRAJ36.json
```

JSON 需要至少包含两个字段：

```json
{
  "nodes": [
    {"id": "n1", "label": "CASSLGQETQYF"},
    {"id": "n2", "label": "CASSIRSSYEQYF"}
  ],
  "links": [
    {"source": "n1", "target": "n2", "weight": 1.0}
  ]
}
```

其中：

- `id`：节点唯一标识；
- `label`：节点标签，通常用于和矩阵中的 `CDR3(pep)` 对应；
- `source` / `target`：边连接的两个节点；
- `weight`：边权重，可选。

---

### 3.2 clone size 矩阵（CSV）

脚本要求 Pre 和 Post 各有一个矩阵文件，例如：

```bash
./Matrix/Pre/TRAV13-1;TRAJ36.csv
./Matrix/Post/TRAV13-1;TRAJ36.csv
```

矩阵示意：

```csv
CDR3(pep),Sample1,Sample2,Sample3
CASSLGQETQYF,10,5,0
CASSIRSSYEQYF,2,8,1
```

要求：

- 第一列为 `CDR3(pep)`，并作为行索引；
- 其余列为样本或其他丰度信息；
- 程序会对某个 CDR3 所在行求和，作为该节点总 clone size。

---

## 4. 输出结果

运行后主要输出 3 类文件：

### 4.1 主图

```bash
./network_plot_{gene}_overlay_disk_pie.pdf
```

该图展示：

- 圆盘内的统一网络布局；
- 灰色边：union graph 中的边；
- 节点大小：总 clone size；
- 节点颜色/扇形：Pre / Post 的存在状态与相对丰度。

### 4.2 节点大小图例

```bash
./legend_circle_size_1_6.pdf
```

表示不同圆点大小所对应的等级或示意范围。

### 4.3 节点类型图例

```bash
./legend_node_types_postonly_pie.pdf
```

表示：

- `Post-only`
- `Pre & Post (pie split)`

如果你后续想更完整，也可以扩展加入 `Pre-only` 图例。

---

## 5. 图形含义解读

### 5.1 节点大小
节点越大，说明该节点对应的 clone size 越高，即该 CDR3（或该节点标签对应的对象）在矩阵中的总丰度越高。
### 5.2 节点颜色
当前脚本中使用如下配色：

- `C_PRE_ONLY = "#7A9994"`：Pre-only
- `C_POST_ONLY = "#DEA97D"`：Post-only
- `C_EDGE = "#9AA0A6"`：边颜色
- `C_DISK_EDGE = "#D0D0D0"`：圆盘边界
- `C_EMPTY = "#BBBBBB"`：空节点/无 clone 节点。

### 5.3 饼图节点（共有节点）
如果一个节点同时出现在 Pre 和 Post 中，则绘制为一个 pie node：

- 一部分代表 Pre；
- 一部分代表 Post；
- 两部分的面积比例由 `pre_val / (pre_val + post_val)` 决定。

因此：

- 如果节点大部分是 Pre 颜色，说明该节点丰度主要来自 Pre；
- 如果节点大部分是 Post 颜色，说明该节点丰度主要来自 Post；
- 如果两部分接近 1:1，则说明该节点在两个状态中丰度相近。

### 5.4 边的含义
边来自 Pre 与 Post 图的并集网络，用于展示整体拓扑连接关系。当前主图中边主要承担**结构背景**作用，不区分 Pre-only edge 和 Post-only edge。

---

## 6. 核心函数说明

### `load_graph(json_path)`
读取 JSON 网络文件，构建 `networkx.Graph()`。

### `load_clone_sizes(G, matrix_csv)`
根据图中节点的 `label`，从矩阵文件中提取对应 clone size。

### `unified_layout_union(G_union)`
对并集网络计算统一布局。

### `normalize_to_disk(pos, R=1.0, margin=0.08)`
将布局压缩到圆盘中，便于统一显示。

### `radius_map(values, v_max, ...)`
将 clone size 映射为可视化节点半径。支持：
- `sqrt`
- `log`
等模式。
### `draw_pie_node(...)`
绘制同时存在于 Pre/Post 的饼图节点。

### `plot_overlay_disk_pie_main(...)`
主函数，完成：
- 读图；
- 合并网络；
- 计算布局；
- 绘制边；
- 绘制不同类型节点；
- 导出主图。

### `save_legend_circle_sizes(...)`
保存节点大小图例。

### `save_legend_node_types(...)`
保存节点类型图例。

---

## 7. 运行方式

你可以直接修改脚本末尾的参数：

```python
gene = "TRAV13-1;TRAJ36"
pre_json  = f"./networkText/Pre/{gene}.json"
post_json = f"./networkText/Post/{gene}.json"
pre_matrix_csv  = f"./Matrix/Pre/{gene}.csv"
post_matrix_csv = f"./Matrix/Post/{gene}.csv"
```

然后运行：

```bash
python your_script.py
```

程序会自动输出：

- 主图 PDF；
- 节点大小图例 PDF；
- 节点类型图例 PDF。

---

## 8. 主要可调参数

在 `plot_overlay_disk_pie_main()` 中可以调节：

- `disk_R`：圆盘半径；
- `disk_margin`：节点距离圆盘边缘的留白；
- `edge_alpha`：边透明度；
- `edge_width`：边宽；
- `node_alpha`：节点透明度；
- `pie_gap_deg`：pie 两部分之间的分隔角度；
- `size_mode`：节点大小映射模式，可选 `sqrt` 或 `log`；
- `r_min` / `r_max`：节点最小/最大半径。

在图例函数中也可调整：

- `labels=(1,2,3,4,5,6)`：节点大小示意；
- `pie_pre_frac=0.5`：示例 pie 图中 Pre 占比；
- `figsize`：图例尺寸。

---

## 9. 适用场景

该分析尤其适合以下问题：

- 比较治疗前后免疫网络是否发生重塑；
- 比较干预前后关键克隆是否扩增或衰减；
- 比较某个基因、某个 VJ 组合或某类克隆在两个状态中的共享程度；
- 从拓扑角度观察网络结构稳定性与条件特异性变化。

---

## 10. 结果解释建议

在论文或汇报中，可从以下几个角度描述结果：

1. **网络整体结构是否变化**
   - Post 中是否出现更多新增节点；
   - 网络是否更稠密或更分散。

2. **共享节点比例**
   - Pre/Post 共有节点多，说明核心克隆结构较稳定；
   - Post-only 节点多，说明干预后出现了新的克隆特征。

3. **丰度变化**
   - 通过 pie node 比例观察共享节点在两个状态中的丰度偏移；
   - 通过节点大小观察高丰度克隆是否集中在某些局部区域。

4. **拓扑重塑**
   - 若新增节点集中在某一局部模块，可能提示特定克隆群在 Post 中扩张；
   - 若大节点在 Post 中明显增多，可能提示克隆扩增增强。

---

## 11. 注意事项

- 图中节点 `label` 必须能够与矩阵中的行名对应，否则该节点 clone size 会被记为 0。
- 当前边是并集边，不区分来源于 Pre 还是 Post；
- 当前图例中仅明确展示了 `Post-only` 与 `Pre & Post`，若用于正式发表，建议补充 `Pre-only` 图例；
- 当节点数量很多时，图可能较拥挤，可通过减小 `r_max`、增大 `disk_margin` 或更换 layout 进一步优化；
- 当前布局基于 union graph，因此适合做“前后对比”，不建议单独把某一状态拿出来解释绝对位置。

---

# 二、小样本验证机器学习
# Random Forest 分类与特征筛选

这是一个用于分类分析的脚本，主要完成特征预处理、随机森林特征筛选、模型训练、交叉验证评估以及重要特征可视化。

## 功能简介

本脚本以表格数据为输入，使用 `Group1` 作为分类标签，对其余数值特征进行建模分析。整体流程包括：

- 数据读取
- 标签编码
- 缺失值填补
- 特征标准化
- 随机森林特征筛选
- 网格搜索优化模型参数
- 交叉验证评估模型性能
- 输出混淆矩阵和特征重要性图

## 输入数据要求

输入数据应为一个表格文件，其中：

- `Group1` 为类别标签列
- `sample.1` 如果存在，会被自动忽略
- 其余列默认为候选特征
- 非数值内容会被转为缺失值，再用均值填补

## 分析流程

### 1. 数据预处理
脚本首先读取数据，并将 `Group1` 编码为模型可用的数字标签。随后对特征进行数值化处理，缺失值使用均值填补，再进行标准化。

### 2. 特征筛选
使用随机森林计算特征重要性，并按照阈值 `0.003` 进行筛选，保留重要特征进入后续建模。

### 3. 模型训练
采用随机森林分类器，并结合 3 折分层交叉验证与网格搜索，对以下参数进行优化：

- `n_estimators`
- `max_depth`
- `min_samples_split`

### 4. 模型评估
脚本会输出：

- 最优参数
- 最佳交叉验证准确率
- 每一折交叉验证准确率
- 分类报告
- 混淆矩阵图

### 5. 特征解释
在完成训练后，脚本会再次提取被选中的特征，并按重要性排序，绘制前 20 个最重要特征的柱状图。

## 输出结果

脚本会生成以下结果：

- 交叉验证准确率图
- 混淆矩阵图
- Top 20 特征重要性图
- 控制台中的最佳参数、分类结果和特征数量信息


