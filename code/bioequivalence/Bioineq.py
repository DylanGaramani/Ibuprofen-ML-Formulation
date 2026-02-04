
import matplotlib.pyplot as plt
import numpy as np

# Data from user summary table
parameters = [
    "Cmax/Dose (μg/ml/mg)",
    "AUC/Dose (μg·h/ml/mg)",
    "Tmax (h)"
]

# Point estimates (ratios)
point_estimates = [1.67, 1.32, 0.39]

# 90% confidence intervals (lower, upper)
ci_lower = [1.57, 1.20, 0.35]
ci_upper = [1.77, 1.45, 0.42]

# Bioequivalence limits
lower_limit = 0.8
upper_limit = 1.25

# Colors
color_point = "#4C72B0"
color_ci = "#000000"
color_bioeq = "#55A868"  # green for bioequivalence zone

fig, ax = plt.subplots(figsize=(8, 4))

y_pos = np.arange(len(parameters))

# Plot bioequivalence acceptance region
ax.axvspan(lower_limit, upper_limit, color=color_bioeq, alpha=0.2, label="Bioequivalence range (0.8 - 1.25)")

# Plot point estimates with error bars for 90% CI
ax.errorbar(point_estimates, y_pos, xerr=[np.array(point_estimates) - np.array(ci_lower), np.array(ci_upper) - np.array(point_estimates)],
            fmt='o', color=color_point, ecolor=color_ci, capsize=5, markersize=8, label="Geometric Mean Ratio (90% CI)")

# Plot vertical line at 1 (no difference)
ax.axvline(1.0, color='gray', linestyle='--')

# Set y-axis labels
ax.set_yticks(y_pos)
ax.set_yticklabels(parameters, fontsize=12)

# Set x-axis label
ax.set_xlabel("Geometric Mean Ratio (Rapid / Standard)", fontsize=12)

# Add ratio and CI text annotations on the right side
for i, (pt, low, high) in enumerate(zip(point_estimates, ci_lower, ci_upper)):
    ax.text(high + 0.05, i, f"{pt:.2f} ({low:.2f} - {high:.2f})", va='center', fontsize=11, color='red')

# Title
ax.set_title("Bioequivalence Forest Plot: Rapid vs Standard Ibuprofen", fontsize=14)

# Adjust layout
plt.tight_layout()

# Show legend
ax.legend(loc='lower right', fontsize=10)

plt.show()
