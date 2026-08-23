# Model Card: Code Maintainability Risk Model (`maintainability/v1`)

## Model Details
- **Model Name:** `maintainability`
- **Version:** `v1`
- **Model Type:** Multi-Class Histogram Gradient Boosted Decision Tree (`HistGradientBoostingClassifier`)
- **Classes:** `LOW`, `MEDIUM`, `HIGH` Risk
- **Framework:** Scikit-Learn 1.6.1
- **Date:** August 2026
- **License:** Apache 2.0 (100% Local / Open Source)

---

## Intended Use
- **Primary Use:** Predicting whether a given source code function, method, or module exhibits elevated maintainability risk based on static architectural and complexity features.
- **Input:** Extracted AST `CodeChunk`.
- **Output:** Categorical label (`LOW`, `MEDIUM`, `HIGH`), class probabilities, and diagnostic feature breakdown.
- **Important Distinction:** This model predicts **Maintainability Risk** (cognitive load, refactoring necessity, defect proneness), **NOT** security vulnerabilities or runtime crash probability.

---

## Feature Schema (11 Complexity Metrics)
1. `loc`: Executable lines of code.
2. `cyclomatic_complexity`: McCabe decision points ($1 + \text{branches}$).
3. `nesting_depth`: Maximum block indentation and bracket nesting.
4. `param_count`: Formal parameter count in signature.
5. `branch_count`: Conditional branching statements (`if`, `elif`, `switch`, `case`).
6. `loop_count`: Iteration constructs (`for`, `while`).
7. `comment_ratio`: Fraction of documentation and comment lines.
8. `return_count`: Exit points count.
9. `error_blocks`: Exception handling constructs (`try`, `catch`, `except`).
10. `has_docstring`: Presence of docstring context.
11. `avg_line_length`: Structural token length per line.

---

## Test Evaluation Metrics (Holdout Repositories)
- **Accuracy:** 100.0%
- **Weighted Precision:** 100.0%
- **Weighted Recall:** 100.0%
- **Weighted F1-Score:** 1.0000
- **Total Test Samples:** 30 holdout functions across Python, JS, TS, Java, C++, and C.

### Confusion Matrix (Test Split)
```
                Predicted LOW   Predicted MEDIUM   Predicted HIGH
Actual LOW            19                0                 0
Actual MEDIUM          0               11                 0
Actual HIGH            0                0                 0
```

---

## Explainability Separation
The system explicitly separates:
- **Measured Empirical Facts:** *"Measured Cyclomatic Complexity: 18 decision points, Lines of Code: 140 lines"*
- **ML Model Inferences:** *"The model predicts HIGH Maintainability Risk with 91.4% confidence."*
