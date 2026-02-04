
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set up enhanced plotting parameters for publication quality
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['axes.grid'] = False  # Disable grid globally for all plots
plt.rcParams['font.size'] = 14     # Increased base font size
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['axes.labelsize'] = 14  # Increased axis label font size
plt.rcParams['legend.fontsize'] = 12  # Increased legend font size
plt.rcParams['figure.titlesize'] = 18
plt.rcParams['xtick.labelsize'] = 12  # Increased tick label font size
plt.rcParams['ytick.labelsize'] = 12  # Increased tick label font size

# Define consistent colors for Rapid and Standard formulation types only
FORMULATION_COLORS = {
    'Rapid': '#5ec962',             # Green
    'Standard': '#440154'           # Purple
}

# Define parameter label mapping for publication
PARAM_LABELS = {
    'tmax': 'Tmax (h)',
    'Cmax_normalized': 'Cmax/Dose (μg/ml/mg)',
    'AUC_normalized': 'AUC/Dose (μg·h/ml/mg)',
    't1_2': 'Half-life (h)'
}

# Function to calculate significance between groups
def calculate_significance(data, param, groups):
    """
    Calculate statistical significance between groups for a parameter
    Returns a dictionary of p-values for each pair of groups
    """
    p_values = {}
    
    # Need at least 2 groups to compare
    if len(groups) < 2:
        return p_values
        
    # Generate all pairs of groups
    for i, group1 in enumerate(groups):
        for group2 in groups[i+1:]:
            # Get the values for each group
            values1 = data[data['Formulation Type'] == group1][param].dropna()
            values2 = data[data['Formulation Type'] == group2][param].dropna()
            
            # Need at least 2 values in each group for t-test
            if len(values1) >= 2 and len(values2) >= 2:
                # Perform t-test
                t_stat, p_val = stats.ttest_ind(values1, values2, equal_var=False)
                p_values[(group1, group2)] = p_val
    
    return p_values

# Function to add significance annotation to bar plots
def add_significance_annotation(ax, p_values, formulation_types, y_values, y_max, buffer=0.1):
    """
    Add significance annotations to a bar plot
    """
    # Define significance thresholds
    sig_levels = {
        0.05: '*',    # p < 0.05
        0.01: '**',   # p < 0.01
        0.001: '***'  # p < 0.001
    }
    
    # Add annotations for each pair with significant p-value
    for (group1, group2), p_val in p_values.items():
        # Only annotate if significant
        if p_val <= 0.05:
            # Determine which significance symbol to use
            sig_symbol = ''
            for threshold, symbol in sorted(sig_levels.items(), reverse=True):
                if p_val <= threshold:
                    sig_symbol = symbol
            
            # Get x positions of the bars
            idx1 = formulation_types.index(group1)
            idx2 = formulation_types.index(group2)
            
            # Get y positions of the bars
            y1 = y_values[idx1]
            y2 = y_values[idx2]
            
            # Calculate height for the annotation line
            height = y_max * (1 + buffer * (idx2 - idx1))
            
            # Draw the annotation
            ax.plot([idx1, idx2], [height, height], 'k-', linewidth=1.5)
            ax.text((idx1 + idx2) / 2, height, sig_symbol, ha='center', va='bottom', fontsize=14)

print("===== IBUPROFEN FORMULATION ANALYSIS WITH STANDARD AND RAPID FORMULATIONS ONLY =====")

# Step 1: Load the matched data
print("\nLoading matched PK data...")
try:
    df = pd.read_excel('matched_pk_data_2.xlsx')
    print(f"Successfully loaded data with {df.shape[0]} rows and {df.shape[1]} columns")
except Exception as e:
    print(f"Error loading file: {str(e)}")
    print("Attempting to load Excel file instead...")
    try:
        df = pd.read_excel('matched_pk_data_2.xlsx')
        print(f"Successfully loaded Excel data with {df.shape[0]} rows and {df.shape[1]} columns")
    except Exception as e:
        print(f"Error loading Excel file: {str(e)}")
        exit()

# Step 2: Convert data to numeric with special handling for ranges and inequality symbols
print("\nConverting data to numeric format with special value handling...")

# Function to handle special numeric formats
def convert_special_numeric(value):
    if pd.isna(value):
        return np.nan
        
    # Convert to string for processing
    str_val = str(value).strip()
    
    # Handle ranges (e.g., "0.25-0.5" or "0.25‚Äì0.5")
    if '-' in str_val or '‚Äì' in str_val or '–' in str_val:
        # Replace various dash types with standard dash
        str_val = str_val.replace('‚Äì', '-').replace('–', '-')
        parts = str_val.split('-')
        try:
            lower = float(parts[0].strip())
            upper = float(parts[1].strip())
            return (lower + upper) / 2  # Return midpoint
        except:
            return np.nan
    
    # Handle "less than" values (e.g., "<0.25")
    elif '<' in str_val:
        try:
            # Return half the value as an estimate
            val = re.search(r'<\s*(\d*\.?\d+)', str_val)
            if val:
                return float(val.group(1)) / 2
            return np.nan
        except:
            return np.nan
    
    # Handle "greater than" values (e.g., ">10")
    elif '>' in str_val:
        try:
            # Return 1.5 times the value as an estimate
            val = re.search(r'>\s*(\d*\.?\d+)', str_val)
            if val:
                return float(val.group(1)) * 1.5
            return np.nan
        except:
            return np.nan
    
    # Handle approximately values (e.g., "~10")
    elif '~' in str_val:
        try:
            # Return the value as is
            val = re.search(r'~\s*(\d*\.?\d+)', str_val)
            if val:
                return float(val.group(1))
            return np.nan
        except:
            return np.nan
            
    # Try standard numeric conversion
    try:
        return float(str_val)
    except:
        return np.nan

numeric_columns = ['tmax', 'cmax', 'auc', 't1_2', 'dose']
for col in numeric_columns:
    if col in df.columns:
        # Apply our special conversion function
        df[col] = df[col].apply(convert_special_numeric)
        print(f"Column {col}: {df[col].notna().sum()} non-missing values")

# Print basic data statistics
print("\nBasic data statistics:")
print(df[numeric_columns].describe())

# Step 3: Create formulation type column based on tmax values ONLY
print("\nClassifying formulation types based on tmax values ONLY...")

def classify_formulation(row):
    # Default to 'Unknown' if tmax is missing
    if pd.isna(row['tmax']):
        return 'Unknown'
    
    tmax_val = row['tmax']
    description = str(row.get('description', '')).lower() if 'description' in df.columns else ''
    
    # Filter out rectal formulations and IV solutions
    if any(term in description for term in ['rectal', 'suppository', 'iv', 'intravenous', 'injection']):
        return 'Excluded'
        
    # Filter out solution and topical products that aren't specifically oral solutions
    if any(term in description for term in ['solution', 'topical', 'cream', 'gel', 'ointment', 'liquid']):
        if not any(term in description for term in ['oral solution', 'oral liquid', 'syrup']):
            return 'Excluded'
    
    # Classification rules based ONLY on tmax thresholds
    if tmax_val > 3.5:
        return 'Extended Release'
    elif tmax_val < 1.0:
        return 'Rapid'
    else:
        return 'Standard'

# Apply the classification function
df['Formulation Type'] = df.apply(classify_formulation, axis=1)
print(f"Formulation Type distribution after initial classification:")
print(df['Formulation Type'].value_counts())

# Step 4: Handle dose values more carefully
print("\nChecking dose values...")

# For rows with missing or zero dose, use typical doses based on formulation
typical_doses = {
    'Rapid': 400,
    'Standard': 400,
    'Extended Release': 800,  # Extended release typically has higher doses
    'Excluded': 400           # Default for excluded formulations
}

for form_type, typical_dose in typical_doses.items():
    mask = ((df['Formulation Type'] == form_type) & 
            (df['dose'].isna() | (df['dose'] == 0)))
    if mask.sum() > 0:
        df.loc[mask, 'dose'] = typical_dose
        print(f"Filled {mask.sum()} missing/zero doses for {form_type} with {typical_dose} mg")

# Step 5: Normalize Cmax and AUC by dose with better error handling
print("\nNormalizing Cmax and AUC by dose...")

# Create normalized columns with careful division
df['Cmax_normalized'] = np.where(
    (df['cmax'].notna()) & (df['dose'].notna()) & (df['dose'] > 0),
    df['cmax'] / df['dose'],
    np.nan
)

df['AUC_normalized'] = np.where(
    (df['auc'].notna()) & (df['dose'].notna()) & (df['dose'] > 0),
    df['auc'] / df['dose'],
    np.nan
)

# Step 6: Prepare data for analysis - filter to include only Rapid and Standard formulations
print("\nPreparing data for analysis - including only Rapid and Standard formulations...")

# Define parameters to analyze
pk_columns = ['tmax', 'Cmax_normalized', 'AUC_normalized', 't1_2']

# Filter rows with at least tmax and one other parameter
df_filtered = df[df['tmax'].notna() & 
                ((df['Cmax_normalized'].notna()) | 
                 (df['AUC_normalized'].notna()) | 
                 (df['t1_2'].notna()))]

# Filter to include ONLY 'Rapid' and 'Standard' formulation types
df_filtered = df_filtered[df_filtered['Formulation Type'].isin(['Rapid', 'Standard'])]

print(f"Dataset after filtering: {df_filtered.shape[0]} samples")

# Print formulation type counts
print("\n*** VERIFICATION POINT 1: Formulation Type counts after filtering ***")
formulation_counts = df_filtered['Formulation Type'].value_counts()
print(formulation_counts)

# Step 7: Create basic scatter plot of formulation types
print("\nCreating scatter plot by formulation type...")

# Create a subset with non-missing Cmax_normalized for plotting
plot_df = df_filtered.dropna(subset=['tmax', 'Cmax_normalized'])
print(f"Samples available for classification plot: {len(plot_df)}")

if len(plot_df) > 0:
    plt.figure(figsize=(12, 10))
    
    # Create a custom palette dictionary for consistent colors
    palette = {form_type: FORMULATION_COLORS.get(form_type, 'gray') 
               for form_type in plot_df['Formulation Type'].unique()}
    
    # Plot each formulation type with consistent colors
    for form_type, color in palette.items():
        subset = plot_df[plot_df['Formulation Type'] == form_type]
        if len(subset) > 0:
            plt.scatter(subset['tmax'], subset['Cmax_normalized'], 
                       color=color, label=form_type,
                       s=120, alpha=0.7, edgecolor='k')  # Increased marker size
    
    # Add only the Rapid threshold line (no Extended Release threshold)
    plt.axvline(x=1.0, color='green', linestyle='--', alpha=0.7, 
              label='Rapid threshold (Tmax < 1.0 h)')
    
    # Set plot labels (no title)
    plt.xlabel('Tmax (h)', fontsize=14)
    plt.ylabel('Cmax/Dose (μg/ml/mg)', fontsize=14)
    plt.legend(title="Formulation Type", fontsize=12, title_fontsize=14)
    
    # No grid
    plt.tight_layout()
    plt.savefig('ibuprofen_formulation_classification_corrected.png', dpi=600)
    print("Saved formulation classification plot")

# Verify distribution again after plotting
print("\n*** VERIFICATION POINT 2: Formulation Type counts in plot dataset ***")
plot_counts = plot_df['Formulation Type'].value_counts()
print(plot_counts)

# Step 8: Create enhanced violin plots for formulation types
print("\nCreating enhanced violin plots by formulation type...")

# Check which parameters have enough data for violin plots
viable_params_violin = []

for param in pk_columns:
    # Check if at least one formulation type has enough samples
    enough_samples = False
    for form_type in df_filtered['Formulation Type'].unique():
        subset = df_filtered[df_filtered['Formulation Type'] == form_type]
        if subset[param].notna().sum() >= 3:
            enough_samples = True
            break
    
    if enough_samples:
        viable_params_violin.append(param)

if viable_params_violin:
    plt.figure(figsize=(5 * len(viable_params_violin), 6))  # Increased height
    
    for i, param in enumerate(viable_params_violin):
        plt.subplot(1, len(viable_params_violin), i+1)
        
        # Drop rows with missing values for this parameter
        temp_df = df_filtered.dropna(subset=[param])
        
        # Create violin plot with individual data points using consistent colors
        sns.violinplot(x='Formulation Type', y=param, data=temp_df, 
                       inner='box', palette=FORMULATION_COLORS)
        
        # Add individual data points
        sns.stripplot(x='Formulation Type', y=param, data=temp_df,
                     color='black', size=5, alpha=0.5, jitter=True)  # Increased point size
        
        # Use proper parameter label for y-axis
        plt.ylabel(PARAM_LABELS.get(param, param), fontsize=14)
        plt.xlabel('Formulation Type', fontsize=14)
        # No title
        # No grid
        
        # Increase tick label font sizes
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
    
    plt.tight_layout()
    plt.savefig('enhanced_formulation_violin_plots_corrected.png', dpi=300)
    print("Saved enhanced violin plots")

# Step 9: Create density plots for parameters with sufficient data
print("\nCreating density plots by formulation type...")

if viable_params_violin:
    plt.figure(figsize=(5 * len(viable_params_violin), 6))  # Increased height
    
    for i, param in enumerate(viable_params_violin):
        plt.subplot(1, len(viable_params_violin), i+1)
        
        for form_type in df_filtered['Formulation Type'].unique():
            subset = df_filtered[df_filtered['Formulation Type'] == form_type]
            # Only plot if we have enough non-missing values
            if subset[param].notna().sum() >= 3:
                color = FORMULATION_COLORS.get(form_type, 'gray')
                sns.kdeplot(subset[param].dropna(), label=form_type, fill=True, alpha=0.3, color=color, linewidth=2)
                
                # Add vertical lines for mean values
                mean_val = subset[param].mean()
                if not pd.isna(mean_val):
                    plt.axvline(x=mean_val, color=color, linestyle='--', linewidth=2,
                              label=f'{form_type} Mean: {mean_val:.2f}')
        
        # Use proper parameter label for x-axis
        plt.xlabel(PARAM_LABELS.get(param, param), fontsize=14)
        # No title
        plt.legend(title="Formulation Type", fontsize=12, title_fontsize=14)
        # No grid
        
        # Increase tick label font sizes
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
    
    plt.tight_layout()
    plt.savefig('formulation_density_plots_corrected.png', dpi=300)
    print("Saved density plots")

# Step 10: Calculate parameter means and standard deviations by formulation type
print("\nCalculating parameter means and standard deviations by formulation type...")

# Create dictionaries to store means and standard deviations
means_dict = {}
std_dict = {}

for param in pk_columns:
    # Initialize Series with proper index
    param_means = pd.Series(index=df_filtered['Formulation Type'].unique())
    param_stds = pd.Series(index=df_filtered['Formulation Type'].unique())
    
    # Calculate mean and standard deviation for each formulation type
    for form_type in df_filtered['Formulation Type'].unique():
        subset = df_filtered[df_filtered['Formulation Type'] == form_type]
        # Only calculate if we have enough non-missing values
        if subset[param].notna().sum() >= 1:
            param_means[form_type] = subset[param].mean()
            # Only calculate std if we have at least 2 samples
            if subset[param].notna().sum() >= 2:
                param_stds[form_type] = subset[param].std()
            else:
                param_stds[form_type] = 0  # No variability can be calculated with just one sample
    
    means_dict[param] = param_means
    std_dict[param] = param_stds

# Convert to DataFrames
means_by_class = pd.DataFrame(means_dict)
stds_by_class = pd.DataFrame(std_dict)

# Replace any remaining NaN with 0 for plotting purposes
means_by_class.fillna(0, inplace=True)
stds_by_class.fillna(0, inplace=True)

# Rename columns to more publication-friendly format
means_by_class.columns = [PARAM_LABELS.get(col, col) for col in means_by_class.columns]
stds_by_class.columns = [PARAM_LABELS.get(col, col) for col in stds_by_class.columns]

# Save parameter means and standard deviations to CSV
means_by_class.to_csv('parameter_means_by_formulation_type_corrected.csv')
stds_by_class.to_csv('parameter_stds_by_formulation_type_corrected.csv')

# Plot means with error bars by formulation type with consistent colors
plt.figure(figsize=(14, 7))  # Increased figure size

# Plot each parameter as a grouped bar chart
x = np.arange(len(means_by_class.columns))
width = 0.8 / len(means_by_class)  # Adjust width based on number of formulation types

# Plot bars for each formulation type with error bars
for i, (form_type, means) in enumerate(means_by_class.iterrows()):
    offset = (i - len(means_by_class)/2 + 0.5) * width
    stds = stds_by_class.loc[form_type]
    plt.bar(x + offset, means.values, width, label=form_type, 
           color=FORMULATION_COLORS.get(form_type, 'gray'),
           yerr=stds.values, capsize=5, error_kw={'elinewidth': 1.5, 'capthick': 1.5})

# No title
plt.xlabel('Parameter', fontsize=14)
plt.ylabel('Mean Value ± Standard Deviation', fontsize=14)
plt.xticks(x, means_by_class.columns, rotation=45, fontsize=12)
plt.legend(title="Formulation Type", fontsize=12, title_fontsize=14)
# No grid
plt.tight_layout()
plt.savefig('parameter_means_with_stds_by_formulation_type_corrected.png', dpi=600)
print("Saved parameter means with standard deviations plot")

# Create a figure with subplots for each parameter
plt.figure(figsize=(16, 12))  # Increased figure size

# Get the parameters from the means DataFrame
parameters = means_by_class.columns

# Create a subplot for each parameter
for i, param in enumerate(parameters):
    ax = plt.subplot(2, 2, i+1)  # 2x2 grid of subplots
    
    # Get the data for this parameter
    param_means = means_by_class[param]
    param_stds = stds_by_class[param]
    
    # Create x positions for the bars
    form_types = param_means.index
    x_pos = np.arange(len(form_types))
    
    # Create bars with error bars
    bars = plt.bar(x_pos, param_means, yerr=param_stds, capsize=5, 
                  color=[FORMULATION_COLORS.get(ft, 'gray') for ft in form_types])
    
    # Calculate significance between formulation types
    p_values = calculate_significance(df_filtered, pk_columns[i], list(form_types))
    
    # Add significance annotations
    if p_values:
        # Get the maximum y value (mean + std) for placing the annotations
        y_max = max(param_means + param_stds) * 1.1
        add_significance_annotation(ax, p_values, list(form_types), param_means, y_max)
    
    # Add labels (no title)
    plt.xlabel('Formulation Type', fontsize=14)
    plt.ylabel('Mean Value ± Standard Deviation', fontsize=14)
    plt.xticks(x_pos, form_types, fontsize=12)
    plt.yticks(fontsize=12)
    # No grid
    
    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + param_stds[bars.index(bar)]*0.2,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=12)

plt.tight_layout()
plt.savefig('separate_parameter_plots.png', dpi=600)
print("Saved separate parameter plots")

# Additionally, create a 2x2 subplot figure with all parameters but each with its own scale
plt.figure(figsize=(16, 12))  # Increased figure size
# No main title

for i, param in enumerate(parameters):
    ax = plt.subplot(2, 2, i+1)
    
    # Get formulation types
    form_types = means_by_class.index
    
    # Plot bars for each formulation type with error bars
    for j, form_type in enumerate(form_types):
        means = means_by_class.loc[form_type, param]
        stds = stds_by_class.loc[form_type, param]
        ax.bar(j, means, width=0.6, label=form_type if i == 0 else "", 
              color=FORMULATION_COLORS.get(form_type, 'gray'),
              yerr=stds, capsize=5, error_kw={'elinewidth': 1.5, 'capthick': 1.5})
        
        # Add value labels on top of each bar
        ax.text(j, means + stds*0.2, f'{means:.3f}', 
               ha='center', va='bottom', fontsize=12)
    
    # Calculate significance between formulation types
    p_values = calculate_significance(df_filtered, pk_columns[i], list(form_types))
    
    # Add significance annotations
    if p_values:
        # Get the maximum y value (mean + std) for placing the annotations
        y_max = means_by_class[param].max() + stds_by_class[param].max()
        add_significance_annotation(ax, p_values, list(form_types), means_by_class[param], y_max)
    
    # Parameter name label instead of title (to avoid headlines)
    ax.text(0.5, 0.93, param, transform=ax.transAxes, 
            fontsize=16, ha='center', va='center')
    
    ax.set_ylabel('Mean Value ± Standard Deviation', fontsize=14)
    ax.set_xticks(range(len(form_types)))
    ax.set_xticklabels(form_types, fontsize=12)
    ax.tick_params(axis='y', labelsize=12)
    # No grid

# Add a single legend for the entire figure
handles, labels = plt.gca().get_legend_handles_labels()
plt.figlegend(handles, labels, loc='upper right', bbox_to_anchor=(0.95, 0.98), 
             title="Formulation Type", fontsize=12, title_fontsize=14)

plt.tight_layout()
plt.savefig('parameter_subplots_by_formulation_type.png', dpi=600)
print("Saved parameter subplots")

# Step 11: Machine Learning Classification with Confusion Matrix and Feature Importance
print("\n===== CLASSIFICATION ANALYSIS =====")

# Prepare data for classification
print("\nPreparing data for classification...")

# We need to handle missing values for classification
# Create a dataset with the most complete columns to maximize sample size
classification_params = []
min_samples_for_ml = 10  # Need reasonable sample size for classification

for param in pk_columns:
    if df_filtered[param].notna().sum() >= min_samples_for_ml:
        classification_params.append(param)

print(f"Parameters with sufficient data for classification: {classification_params}")

if len(classification_params) >= 2 and len(df_filtered) >= min_samples_for_ml:
    # Get samples that have at least 2 non-missing parameters
    ml_df = df_filtered.copy()
    
    # Print verification of formulation types before imputation
    print("\n*** VERIFICATION POINT 3: Formulation Type counts before imputation ***")
    print(ml_df['Formulation Type'].value_counts())
    
    # Impute missing values for classification
    # For classification, we'll impute missing values with the mean of each parameter by formulation type
    for param in classification_params:
        for form_type in ml_df['Formulation Type'].unique():
            form_mask = ml_df['Formulation Type'] == form_type
            param_mean = ml_df.loc[form_mask, param].mean()
            # Fill missing values for this formulation type with its mean
            ml_df.loc[form_mask & ml_df[param].isna(), param] = param_mean
    
    # Check if we still have missing values (could happen if a formulation type has no data for a parameter)
    # Fill remaining missing values with overall mean
    for param in classification_params:
        overall_mean = ml_df[param].mean()
        ml_df[param] = ml_df[param].fillna(overall_mean)
    
    print(f"Prepared dataset for classification with {len(ml_df)} samples")
    
    # Print verification of formulation types after imputation
    print("\n*** VERIFICATION POINT 4: Formulation Type counts after imputation ***")
    print(ml_df['Formulation Type'].value_counts())
    
    # Make sure we have at least 2 samples per class
    valid_formulations = []
    for form_type in ml_df['Formulation Type'].unique():
        if ml_df[ml_df['Formulation Type'] == form_type].shape[0] >= 2:
            valid_formulations.append(form_type)
    
    if len(valid_formulations) >= 2:
        # Filter to keep only valid formulation types
        ml_df = ml_df[ml_df['Formulation Type'].isin(valid_formulations)]
        
        # Print verification after filtering for valid formulations
        print("\n*** VERIFICATION POINT 5: Formulation Type counts after valid formulation filtering ***")
        print(ml_df['Formulation Type'].value_counts())
        
        # Define features and target
        X = ml_df[classification_params]
        y = ml_df['Formulation Type']
        
        # Split the data
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y)
            
            print(f"Training set: {X_train.shape[0]} samples")
            print(f"Test set: {X_test.shape[0]} samples")
            
            # Print verification of training and test sets
            print("\n*** VERIFICATION POINT 6: Training set formulation type distribution ***")
            print(y_train.value_counts())
            print("\n*** VERIFICATION POINT 7: Test set formulation type distribution ***")
            print(y_test.value_counts())
            
            # Train a Random Forest classifier
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X_train, y_train)
            
            # Evaluate the classifier
            y_pred = rf.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"\nRandom Forest Classifier Accuracy: {accuracy:.2f}")
            
            # Cross-validation for more robust evaluation
            cv_scores = cross_val_score(rf, X, y, cv=min(5, len(valid_formulations)), scoring='accuracy')
            print(f"Cross-validation accuracy: {cv_scores.mean():.2f} ± {cv_scores.std():.2f}")
            
            # Classification report
            print("\nClassification Report:")
            print(classification_report(y_test, y_pred))
            
            # Define the correct order of formulation types
            correct_form_order = ['Rapid', 'Standard']
            
            # Generate and plot confusion matrix with proper ordering
            all_labels = sorted(set(y_test) | set(y_pred), 
                               key=lambda x: correct_form_order.index(x) if x in correct_form_order else 999)
                               
            cm = confusion_matrix(y_test, y_pred, labels=all_labels)
            plt.figure(figsize=(10, 8))
            
            # Print the actual confusion matrix values for verification
            print("\n*** VERIFICATION POINT 8: Confusion Matrix Values ***")
            print(cm)
            
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                        xticklabels=all_labels,
                        yticklabels=all_labels, annot_kws={"size": 14})  # Increased annotation size
            plt.xlabel('Predicted Formulation Type', fontsize=14)
            plt.ylabel('True Formulation Type', fontsize=14)
            plt.xticks(fontsize=12)
            plt.yticks(fontsize=12)
            # No title
            plt.tight_layout()
            plt.savefig('formulation_confusion_matrix_corrected.png', dpi=600)
            print("Saved confusion matrix")
            
            # Feature importance
            # Get the formatted parameter names for the feature importance plot
            formatted_params = [PARAM_LABELS.get(param, param) for param in classification_params]
            
            feature_importances = pd.DataFrame({
                'Feature': formatted_params,
                'Importance': rf.feature_importances_
            }).sort_values('Importance', ascending=False)
            
            print("\nFeature Importance:")
            print(feature_importances)
            
            # Plot feature importance
            plt.figure(figsize=(10, 6))
            
            # Create colors based on feature names
            feature_colors = []
            for i, feature in enumerate(classification_params):
                feature_name = str(feature).lower()
                if 'tmax' in feature_name:
                    feature_colors.append(FORMULATION_COLORS['Standard'])
                else:
                    feature_colors.append(FORMULATION_COLORS['Rapid'])
            
            # Create bar plot
            plt.barh(feature_importances['Feature'], feature_importances['Importance'], color=feature_colors)
            # No title
            plt.xlabel('Relative Importance', fontsize=14)
            plt.ylabel('Pharmacokinetic Parameter', fontsize=14)
            plt.xticks(fontsize=12)
            plt.yticks(fontsize=12)
            plt.tight_layout()
            plt.savefig('feature_importance_corrected.png', dpi=600)
            print("Saved feature importance plot")
            
        except Exception as e:
            print(f"Error in classification: {str(e)}")
    else:
        print("Not enough samples per class for classification")
else:
    print("Not enough data for classification analysis")

print("Analysis complete.")
