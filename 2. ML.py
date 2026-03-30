import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.metrics import classification_report, confusion_matrix


# -----------------------------
# 1) Read data
# -----------------------------
df = pd.read_csv("merged1.csv", index_col=0)

# -----------------------------
# 2) y: label
# 你这个文件里标签列是 Group1（第一列）
# -----------------------------
le = LabelEncoder()
y = le.fit_transform(df["Group1"].astype(str).values)

# -----------------------------
# 3) X: features
# 去掉标签列 + 去掉字符串列 sample.1（如果存在）
# 并强制把所有特征转为数值（转不了的变 NaN，后面用均值填）
# -----------------------------
X_df = df.drop(columns=["Group1", "sample.1"], errors="ignore")
X = X_df.apply(pd.to_numeric, errors="coerce")  # 非数值 -> NaN

# Preprocess data: impute missing values and standardize features
imputer = SimpleImputer(strategy="mean")
X = imputer.fit_transform(X)
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Use Random Forest to compute feature importances and select features
rf_selector = RandomForestClassifier(n_estimators=100, random_state=42)
rf_selector.fit(X, y)

# Adjust the threshold (try a lower threshold to select more features)
custom_threshold = 0.003
selector = SelectFromModel(rf_selector, threshold=custom_threshold, prefit=True)
X_selected = selector.transform(X)
print("Number of features selected:", X_selected.shape[1])

# Use StratifiedKFold for cross-validation due to small dataset size
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

# Set up parameter grid for Random Forest
param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [None, 5, 10, 20],
    "min_samples_split": [2, 5, 10]
}

# Use GridSearchCV to tune Random Forest parameters
grid_search = GridSearchCV(RandomForestClassifier(random_state=42),
                           param_grid,
                           cv=cv,
                           scoring="accuracy")
grid_search.fit(X_selected, y)
print("Best parameters:", grid_search.best_params_)
print("Best cross-validation accuracy:", grid_search.best_score_)

# Get the best model
best_rf = grid_search.best_estimator_

# Perform cross-validation with the best model to get fold-wise scores
cv_scores = cross_val_score(best_rf, X_selected, y, cv=cv, scoring="accuracy")
print("Cross-validation scores for each fold:", cv_scores)

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 20
# Plot cross-validation results
plt.figure(figsize=(8, 5))
folds = np.arange(1, len(cv_scores) + 1)

# 使用 pre 颜色绘制柱状图
plt.bar(folds, cv_scores, color="#3976B0", edgecolor='black')

# 使用 post 颜色绘制均值曲线（虚线）
mean_score = np.mean(cv_scores)
plt.plot(folds, [mean_score] * len(cv_scores), linestyle='--', color="#CA8E8C", 
         label=f'Mean = {mean_score:.4f}', linewidth=4)

plt.xlabel("Fold")
plt.ylabel("Accuracy")
plt.title("Cross-validation Accuracy per Fold")
plt.xticks(folds)
plt.legend()
plt.tight_layout()
plt.savefig("cross_validation_accuracy.pdf",dpi=300)
plt.close()
# ---------------------------
# 模型评估及分类报告
# ---------------------------
y_pred = best_rf.predict(X_selected)
print("Classification Report:")
print(classification_report(y, y_pred, target_names=le.classes_))

# ---------------------------
# 混淆矩阵图
# ---------------------------

# 生成自定义色带，从 pre 颜色到 post 颜色
custom_cmap = LinearSegmentedColormap.from_list('custom', ["#3976B0", "#CA8E8C"])

cm = confusion_matrix(y, y_pred)
plt.figure(figsize=(6, 5))
# 利用自定义色带绘制混淆矩阵
plt.imshow(cm, interpolation='nearest', cmap=custom_cmap)
plt.title("Confusion Matrix")
plt.colorbar()
tick_marks = np.arange(len(le.classes_))
plt.xticks(tick_marks, le.classes_, rotation=45)
plt.yticks(tick_marks, le.classes_)
plt.xlabel("Predicted Label")
plt.ylabel("True Label")

# 在每个单元格内显示数值
thresh = cm.max() / 2.
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(j, i, format(cm[i, j], 'd'),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
plt.tight_layout()
plt.savefig("confusion_matrix.pdf",dpi=300)
plt.close()

# Convert features to numeric and drop columns that are all NaN
numeric_df = df.iloc[:, 2:].apply(pd.to_numeric, errors='coerce')
numeric_df = numeric_df.dropna(axis=1, how='all')
original_feature_names = numeric_df.columns.values  # Now its length matches X's columns
X = numeric_df.values

print("Shape of X:", X.shape)
print("Number of original features:", len(original_feature_names))

# Preprocess data: impute missing values and standardize features
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

imputer = SimpleImputer(strategy="mean")
X = imputer.fit_transform(X)
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Train RandomForest for feature selection
from sklearn.ensemble import RandomForestClassifier
rf_selector = RandomForestClassifier(n_estimators=100, random_state=42)
rf_selector.fit(X, y)

# Feature selection using a custom threshold
from sklearn.feature_selection import SelectFromModel
custom_threshold = 0.003
selector = SelectFromModel(rf_selector, threshold=custom_threshold, prefit=True)
X_selected = selector.transform(X)
print("Number of features selected:", X_selected.shape[1])

# Now the boolean mask from selector.get_support() should match original_feature_names length
mask = selector.get_support()
print("Mask shape:", mask.shape)
print("Length of original_feature_names:", len(original_feature_names))

# Get selected feature names
selected_feature_names = original_feature_names[mask]

# Get feature importances from a trained model (e.g., rf_selector or best_rf)
importances = rf_selector.feature_importances_
# Get importances only for the selected features
selected_importances = importances[mask]
# Sort selected features by importance (descending)
sorted_indices = np.argsort(selected_importances)[::-1]
top10_indices = sorted_indices[:20]
top10_importances = selected_importances[top10_indices]
top10_feature_names = selected_feature_names[top10_indices]


plt.figure(figsize=(9, 6))
# 使用 pre 颜色 (#3976B0) 填充，使用 post 颜色 (#CA8E8C) 作为边框
plt.bar(range(20), top10_importances, align='center', color="#3976B0")
plt.xticks(range(20), top10_feature_names, rotation=45, ha='right')
plt.xlabel("Feature")
plt.ylabel("Importance")
plt.title("Top 20 Feature Importances")
plt.tight_layout()
plt.savefig("top20_feature_importances.pdf",dpi=300)
plt.close()

