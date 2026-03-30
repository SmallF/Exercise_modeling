# Network Topology Comparison and Small-Sample Machine Learning Validation

## 1. Network Topology Comparison Visualization

### Overview
This module is designed to visualize and compare the network topology of the same gene, such as a specific VJ combination, under **Pre** and **Post** conditions. It highlights structural differences between the two networks using a shared layout, node size, and color composition.

### Main Features
- Compares Pre and Post networks under a **unified layout**
- Uses **node size** to represent clone abundance
- Uses **node color** or **pie-split nodes** to indicate whether a node is:
  - Pre-only
  - Post-only
  - shared by both Pre and Post
- Exports the main plot and separate legends for presentation or publication

This module is particularly useful for showing topological changes in immune repertoire or receptor networks before and after treatment, intervention, or experimental manipulation.

### Workflow
1. Read the Pre and Post network JSON files.
2. Read the clone size matrices.
3. Merge the two networks into a union graph.
4. Compute one global layout and normalize it into a circular disk.
5. Draw nodes according to condition-specific presence and abundance.
6. Draw edges and clip the network within the disk boundary.
7. Export the main figure and legends.

### Input Requirements
#### Network JSON
Each condition should provide a JSON file containing:
- `nodes`
- `links`

Each node should include:
- `id`
- optional `label`

Each edge should include:
- `source`
- `target`
- optional `weight`

Example:

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

#### Clone Size Matrix
The clone size matrix should:
- use `CDR3(pep)` as the row index
- contain abundance values across samples or columns
- allow row-wise summation to define node-level clone size

Example:

```csv
CDR3(pep),Sample1,Sample2,Sample3
CASSLGQETQYF,10,5,0
CASSIRSSYEQYF,2,8,1
```

### Output
The script produces:
- a main topology comparison figure
- a node size legend
- a node type legend

### Figure Interpretation
- **Larger nodes** indicate higher clone abundance.
- **Pre-only nodes** and **Post-only nodes** are shown as solid single-color circles.
- **Shared nodes** are shown as pie nodes, where sector size reflects the relative abundance in Pre and Post.
- **Edges** represent the union graph and mainly provide structural context.

### Key Functions
- `load_graph(json_path)`: read a network JSON file
- `load_clone_sizes(G, matrix_csv)`: extract clone abundance from the matrix
- `unified_layout_union(G_union)`: compute a unified layout
- `normalize_to_disk(pos, R=1.0, margin=0.08)`: normalize coordinates into a disk
- `radius_map(values, v_max, ...)`: map abundance values to node radii
- `draw_pie_node(...)`: draw shared nodes as pie charts
- `plot_overlay_disk_pie_main(...)`: generate the main comparison plot
- `save_legend_circle_sizes(...)`: save node size legend
- `save_legend_node_types(...)`: save node type legend

### Adjustable Parameters
Common parameters include:
- `disk_R`
- `disk_margin`
- `edge_alpha`
- `edge_width`
- `node_alpha`
- `pie_gap_deg`
- `size_mode`
- `r_min` / `r_max`

### Typical Applications
- Comparing immune network remodeling before and after treatment
- Identifying clone expansion or contraction after intervention
- Evaluating shared and condition-specific clonal structures
- Exploring topological stability and network rewiring

### Notes
- Node `label` values must match the row names in the clone size matrix.
- Edges are currently drawn from the union graph and are not separated by condition.
- For publication-quality figures, a `Pre-only` legend can be added if needed.
- If the network is too crowded, consider reducing node radius or increasing layout margin.

---

## 2. Small-Sample Machine Learning Validation

### Overview
This module performs classification analysis using a random forest model. It includes preprocessing, feature selection, model training, cross-validation, and feature importance visualization, making it suitable for small-sample exploratory validation.

### Main Features
- Reads tabular input data
- Uses `Group1` as the class label
- Handles missing values automatically
- Standardizes numerical features
- Selects informative features using random forest importance
- Tunes model parameters with grid search
- Evaluates performance with stratified cross-validation
- Outputs classification results and feature importance plots

### Input Requirements
The input data table should include:
- `Group1` as the class label column
- an optional `sample.1` column, which will be ignored
- all remaining columns as candidate features

Non-numeric values will be converted to missing values and imputed using the mean.

### Workflow
1. Load the input table.
2. Encode `Group1` into numeric class labels.
3. Convert all candidate features to numeric format.
4. Impute missing values and standardize features.
5. Use random forest to calculate feature importance.
6. Select features using a predefined threshold.
7. Train the classifier with 3-fold stratified cross-validation and grid search.
8. Output classification performance and visualize the top important features.

### Model Tuning
The following parameters are optimized:
- `n_estimators`
- `max_depth`
- `min_samples_split`

### Output
The script generates:
- cross-validation accuracy plot
- confusion matrix plot
- top feature importance plot
- console output showing the best parameters, classification results, and number of selected features

### Applications
This module is suitable for:
- small-sample classification tasks
- exploratory biomarker discovery
- group discrimination analysis
- feature importance ranking and interpretation

### Notes
Random forest is used here as a robust baseline model because it can handle nonlinear relationships and directly provide feature importance scores, making it practical for preliminary screening and validation.
