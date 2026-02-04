
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Set up basic plotting parameters for publication quality
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['axes.grid'] = False  # Disable grid globally
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10

# Define consistent colors for formulation types
FORMULATION_COLORS = {
    'Rapid': '#5ec962',             # Green
    'Extended Release': '#21918c',  # Teal
    'Standard': '#440154'           # Purple
}

# Define colors for formulation principles (added Ibuprofen poloxamer 407)
PRINCIPLE_COLORS = {
    'Ibuprofen (acid)': '#440154',           # Dark Purple
    'Ibuprofen lysine': '#3b528b',           # Blue-Purple
    'Ibuprofen arginine': '#21908c',         # Teal
    'Amorphous ibuprofen': '#5ec962',        # Green
    'Ibuprofen poloxamer 407': '#31a354',    # Another green shade
    'Aluminium ibuprofen': '#fde725',        # Yellow
    'Sodium ibuprofen dihydrate': '#f5a21e', # Orange
    'Dexibuprofen': '#e55c30',               # Red-Orange
    'Unknown': '#cccccc'                     # Gray
}

# Define colors for dosage forms - removed Hard capsule
DOSAGE_COLORS = {
    'Tablet': '#440154',               # Dark Purple
    'Oral suspension': '#3b528b',      # Blue-Purple
    'Soft gel capsule': '#21908c',     # Teal
    'Effervescent tablet': '#fde725',  # Yellow
    'Oral solution': '#f5a21e',        # Orange
    'Chewable tablet': '#e55c30',      # Red-Orange
    'Granules': '#9c3768',             # Pink
    'Other': '#cccccc'                 # Gray
}

# Define parameter label mapping for publication
PARAM_LABELS = {
    'tmax': 'Tmax (h)',
    'Cmax_normalized': 'Cmax/Dose (μg/ml/mg)',
    'AUC_normalized': 'AUC/Dose (μg·h/ml/mg)',
    't1_2': 'Half-life (h)'
}

def convert_special_numeric(value):
    """Handle special numeric formats like ranges and inequality symbols"""
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

def classify_formulation(row):
    """Classify formulation types based on tmax values"""
    # Default to 'Unknown' if tmax is missing
    if pd.isna(row['tmax']):
        return 'Unknown'
    
    tmax_val = row['tmax']
    description = str(row.get('description', '')).lower() if 'description' in row else ''
    
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
    elif tmax_val < 0.83:
        return 'Rapid'
    else:
        return 'Standard'

def classify_formulation_principle(row):
    """
    Classify the formulation principle based on the specified groups:
    - Ibuprofen (acid)
    - Ibuprofen lysine
    - Ibuprofen arginine
    - Amorphous ibuprofen
    - Ibuprofen poloxamer 407 (added)
    - Aluminium ibuprofen
    - Sodium ibuprofen dihydrate
    - Dexibuprofen (S(+) ibuprofen)
    """
    description = str(row.get('description', '')).lower() if 'description' in row else ''
    brand = str(row.get('brand', '')).lower() if 'brand' in row else ''
    compound = str(row.get('compound', '')).lower() if 'compound' in row else ''
    formulation = str(row.get('formulation', '')).lower() if 'formulation' in row else ''
    
    # Combine text fields for more comprehensive searching
    text = f"{description} {brand} {compound} {formulation}"
    
    # Check for specific formulation types in the combined text
    if any(term in text for term in ['lysine', 'lysinate', 'lys ']):
        return 'Ibuprofen lysine'
    elif any(term in text for term in ['arginine', 'arginate', 'arg ']):
        return 'Ibuprofen arginine'
    elif any(term in text for term in ['amorphous', 'amorph']):
        return 'Amorphous ibuprofen'
    elif any(term in text for term in ['poloxamer 407', 'poloxamer407', 'ploxamer', 'poloxa']):
        return 'Ibuprofen poloxamer 407'
    elif any(term in text for term in ['aluminium', 'aluminum', 'al ']):
        return 'Aluminium ibuprofen'
    elif any(term in text for term in ['sodium', 'natrium', 'na ']) and any(term in text for term in ['dihydrate']):
        return 'Sodium ibuprofen dihydrate'
    elif any(term in text for term in ['dexibuprofen', 's(+)', 's-ibuprofen', 's+', 'dex', 'dexibuprofeno']):
        return 'Dexibuprofen'
    elif any(term in text for term in ['sodium', 'natrium', 'na ']):
        # If just sodium is mentioned without dihydrate, still classify as sodium dihydrate 
        # as that's the common form of sodium ibuprofen
        return 'Sodium ibuprofen dihydrate'
    else:
        # Default to standard acid form if no specific salt or formulation is mentioned
        return 'Ibuprofen (acid)'

def classify_dosage_form(row):
    """
    Classify the dosage form based on the description:
    - Tablet
    - Oral suspension
    - Soft gel capsule (all capsules are classified as soft gel)
    - Effervescent tablet
    - Oral solution
    - Chewable tablet
    - Granules
    - Other
    
    If unspecified, defaults to Tablet.
    """
    description = str(row.get('description', '')).lower() if 'description' in row else ''
    formulation = str(row.get('formulation', '')).lower() if 'formulation' in row else ''
    brand = str(row.get('brand', '')).lower() if 'brand' in row else ''
    
    # Combine text fields for more comprehensive searching
    text = f"{description} {formulation} {brand}"
    
    # Check for specific dosage forms in the combined text
    if any(term in text for term in ['effervescent', 'fizzy', 'dissolving']):
        return 'Effervescent tablet'
    elif any(term in text for term in ['chewable', 'chew']):
        return 'Chewable tablet'
    # All capsules are now classified as soft gel capsules
    elif any(term in text for term in ['capsule', 'cap ', 'soft gel', 'softgel', 'soft-gel', 'liquid cap', 'liquid-filled']):
        return 'Soft gel capsule'
    elif any(term in text for term in ['susp', 'suspension']):
        return 'Oral suspension'
    elif any(term in text for term in ['syrup', 'solution', 'liquid', 'oral sol']):
        return 'Oral solution'
    elif any(term in text for term in ['granule', 'powder', 'sachet']):
        return 'Granules'
    elif any(term in text for term in ['tablet', 'tab ', 'tabs', 'caplet', 'film-coated']):
        return 'Tablet'
    else:
        # Default to Tablet if no specific dosage form is identified
        return 'Tablet'

def load_and_preprocess_data(file_path='matched_pk_data_2.csv'):
    """Load and preprocess the data from CSV or Excel file"""
    print("\nLoading matched PK data...")
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded data with {df.shape[0]} rows and {df.shape[1]} columns")
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        print("Attempting to load Excel file instead...")
        try:
            df = pd.read_excel(file_path)
            print(f"Successfully loaded Excel data with {df.shape[0]} rows and {df.shape[1]} columns")
        except Exception as e:
            print(f"Error loading Excel file: {str(e)}")
            exit()
    
    # Display column names to help with debugging
    print("\nAvailable columns in the dataset:")
    print(df.columns.tolist())
    
    # Convert data to numeric with special handling
    print("\nConverting data to numeric format with special value handling...")
    numeric_columns = ['tmax', 'cmax', 'auc', 't1_2', 'dose']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_special_numeric)
            print(f"Column {col}: {df[col].notna().sum()} non-missing values")
    
    # Print basic data statistics
    print("\nBasic data statistics:")
    print(df[numeric_columns].describe())
    
    # Classify formulation types based on tmax
    print("\nClassifying formulation types based on tmax values...")
    df['Formulation Type'] = df.apply(classify_formulation, axis=1)
    print(f"Formulation Type distribution:")
    print(df['Formulation Type'].value_counts())
    
    # Classify formulation principles
    print("\nClassifying formulation principles based on description and related fields...")
    df['Formulation Principle'] = df.apply(classify_formulation_principle, axis=1)
    print(f"Formulation Principle distribution:")
    print(df['Formulation Principle'].value_counts())
    
    # Classify dosage forms
    print("\nClassifying dosage forms based on description and related fields...")
    df['Dosage Form'] = df.apply(classify_dosage_form, axis=1)
    print(f"Dosage Form distribution:")
    print(df['Dosage Form'].value_counts())
    
    # Handle missing dose values
    typical_doses = {
        'Rapid': 400,
        'Standard': 400,
        'Extended Release': 800,
        'Excluded': 400
    }
    
    for form_type, typical_dose in typical_doses.items():
        mask = ((df['Formulation Type'] == form_type) & 
                (df['dose'].isna() | (df['dose'] == 0)))
        if mask.sum() > 0:
            df.loc[mask, 'dose'] = typical_dose
            print(f"Filled {mask.sum()} missing/zero doses for {form_type} with {typical_dose} mg")
    
    # Normalize Cmax and AUC by dose
    print("\nNormalizing Cmax and AUC by dose...")
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
    
    # Check for amorphous ibuprofen specifically
    print("\nSearching for Amorphous ibuprofen instances...")
    amorphous_mask = df['Formulation Principle'] == 'Amorphous ibuprofen'
    if amorphous_mask.sum() > 0:
        print(f"Found {amorphous_mask.sum()} records classified as Amorphous ibuprofen")
        print("Sample descriptions:")
        for idx, row in df[amorphous_mask].iterrows():
            print(f"- {row.get('description', 'N/A')}")
            
        # NEW: Check if amorphous samples have complete data
        amorphous_data = df[amorphous_mask]
        pk_columns = ['tmax', 'Cmax_normalized', 'AUC_normalized', 't1_2']
        print("\nAmorphous ibuprofen PK data:")
        print(amorphous_data[pk_columns])
        
        # Check for missing values that would cause filtering
        missing_values = amorphous_data[pk_columns].isna().sum(axis=1)
        if any(missing_values > 0):
            print("Warning: Amorphous samples have missing values that may cause filtering:")
            for idx, row in amorphous_data.iterrows():
                print(f"Sample ID {idx}: Missing {missing_values[idx]} values")
                print(row[pk_columns].isna())
    else:
        print("No records were classified as Amorphous ibuprofen.")
        print("Checking for 'amorph' keyword in text fields:")
        text_fields = ['description', 'brand', 'compound', 'formulation']
        for field in text_fields:
            if field in df.columns:
                amorphous_keyword = df[field].astype(str).str.contains('amorph', case=False, na=False)
                if amorphous_keyword.sum() > 0:
                    print(f"Found {amorphous_keyword.sum()} records with 'amorph' in {field} field")
                    print("Sample values:")
                    for val in df.loc[amorphous_keyword, field].head(5).values:
                        print(f"- {val}")
    
    # Check for poloxamer 407 specifically
    print("\nSearching for Ibuprofen poloxamer 407 instances...")
    poloxamer_mask = df['Formulation Principle'] == 'Ibuprofen poloxamer 407'
    if poloxamer_mask.sum() > 0:
        print(f"Found {poloxamer_mask.sum()} records classified as Ibuprofen poloxamer 407")
        print("Sample descriptions:")
        for idx, row in df[poloxamer_mask].iterrows():
            print(f"- {row.get('description', 'N/A')}")
            
        # Check if poloxamer samples have complete data
        poloxamer_data = df[poloxamer_mask]
        pk_columns = ['tmax', 'Cmax_normalized', 'AUC_normalized', 't1_2']
        print("\nIbuprofen poloxamer 407 PK data:")
        print(poloxamer_data[pk_columns])
        
        # Check for missing values that would cause filtering
        missing_values = poloxamer_data[pk_columns].isna().sum(axis=1)
        if any(missing_values > 0):
            print("Warning: Poloxamer samples have missing values that may cause filtering:")
            for idx, row in poloxamer_data.iterrows():
                print(f"Sample ID {idx}: Missing {missing_values[idx]} values")
                print(row[pk_columns].isna())
    else:
        print("No records were classified as Ibuprofen poloxamer 407.")
        print("Checking for 'poloxamer' keyword in text fields:")
        text_fields = ['description', 'brand', 'compound', 'formulation']
        for field in text_fields:
            if field in df.columns:
                poloxamer_keyword = df[field].astype(str).str.contains('poloxamer|poloxa', case=False, na=False)
                if poloxamer_keyword.sum() > 0:
                    print(f"Found {poloxamer_keyword.sum()} records with 'poloxamer' in {field} field")
                    print("Sample values:")
                    for val in df.loc[poloxamer_keyword, field].head(5).values:
                        print(f"- {val}")
    
    return df

def create_pair_plots(df_filtered, pk_columns, color_by='Formulation Type'):
    """
    Create PK parameter pair plots colored by specified column
    
    Parameters:
    -----------
    df_filtered : pandas.DataFrame
        Filtered dataframe containing PK parameters
    pk_columns : list
        List of PK parameter column names to include in the plot
    color_by : str
        Column name to use for coloring points ('Formulation Type', 'Formulation Principle', or 'Dosage Form')
    """
    print(f"\nCreating PK parameter pair plot colored by {color_by}...")
    
    # Check for special formulations
    has_amorphous = 'Amorphous ibuprofen' in df_filtered['Formulation Principle'].values
    has_poloxamer = 'Ibuprofen poloxamer 407' in df_filtered['Formulation Principle'].values
    
    if has_amorphous:
        print(f"Pair plot includes {df_filtered['Formulation Principle'].eq('Amorphous ibuprofen').sum()} amorphous samples")
    if has_poloxamer:
        print(f"Pair plot includes {df_filtered['Formulation Principle'].eq('Ibuprofen poloxamer 407').sum()} poloxamer 407 samples")
    
    # Select color palette based on the grouping variable
    if color_by == 'Formulation Type':
        palette = FORMULATION_COLORS
    elif color_by == 'Formulation Principle':
        palette = PRINCIPLE_COLORS
    else:  # Dosage Form
        palette = DOSAGE_COLORS
    
    # Create a DataFrame with renamed columns for better plot readability
    plot_df = df_filtered[pk_columns].copy()
    plot_df.columns = [PARAM_LABELS.get(col, col) for col in plot_df.columns]
    
    # Add grouping variable for coloring
    plot_df[color_by] = df_filtered[color_by]
    
    # Create the pair plot with custom figure size to accommodate legend
    pair_plot = sns.pairplot(
        plot_df, 
        hue=color_by,
        palette=palette,
        diag_kind='kde',
        plot_kws={'alpha': 0.6, 's': 80, 'edgecolor': 'w'},
        diag_kws={'alpha': 0.5, 'linewidth': 2},
        height=3,
        aspect=1
    )
    
    # Move legend outside the plot
    pair_plot._legend.remove()  # Remove the original legend
    plt.subplots_adjust(right=0.85)  # Make room for legend on right
    pair_plot.fig.legend(
        handles=pair_plot._legend_data.values(),
        labels=pair_plot._legend_data.keys(),
        title=color_by,
        loc='center right',
        bbox_to_anchor=(1.15, 0.5),
        frameon=True
    )
    
    # Remove grid from all subplots
    for ax in pair_plot.axes.flatten():
        ax.grid(False)
    
    # Tighten layout and save
    plt.tight_layout()
    filename = f"pk_parameter_pairplot_by_{color_by.lower().replace(' ', '_')}.png"
    pair_plot.savefig(filename, dpi=600, bbox_inches='tight')
    print(f"Saved PK parameter pair plot as {filename}")

def create_correlation_heatmap(df_filtered, pk_columns):
    """Create correlation heatmap of PK parameters without headings or grid"""
    print("\nCalculating parameter correlations...")
    
    # Create a DataFrame with renamed columns for better plot readability
    plot_df = df_filtered[pk_columns].copy()
    plot_df.columns = [PARAM_LABELS.get(col, col) for col in plot_df.columns]
    
    # Get correlation matrix for PK parameters
    correlation_matrix = plot_df.corr()
    
    # Plot correlation heatmap
    plt.figure(figsize=(10, 8))
    
    # Create heatmap without grid
    sns.heatmap(
        correlation_matrix, 
        annot=True, 
        cmap='coolwarm', 
        vmin=-1, 
        vmax=1, 
        fmt='.2f', 
        linewidths=0.5,
        cbar_kws={"shrink": 0.8}
    )
    
    # No title as requested
    plt.tight_layout()
    plt.savefig('pk_parameter_correlation_heatmap.png', dpi=600)
    print("Saved PK parameter correlation heatmap")

def perform_pca_analysis(df_filtered, pk_columns, color_by='Formulation Type'):
    """
    Perform Principal Component Analysis on the PK parameters and create
    visualizations colored by the specified column.
    
    Parameters:
    -----------
    df_filtered : pandas.DataFrame
        Filtered dataframe containing PK parameters
    pk_columns : list
        List of PK parameter column names to include in the PCA
    color_by : str
        Column name to use for coloring points ('Formulation Type', 'Formulation Principle', or 'Dosage Form')
    
    Returns:
    --------
    tuple
        (pca_model, pca_result, explained_variance_ratio)
    """
    print(f"\nPerforming Principal Component Analysis with {color_by} classification...")
    
    # Check for special formulations
    has_amorphous = 'Amorphous ibuprofen' in df_filtered['Formulation Principle'].values
    has_poloxamer = 'Ibuprofen poloxamer 407' in df_filtered['Formulation Principle'].values
    
    if has_amorphous:
        print(f"PCA analysis includes {df_filtered['Formulation Principle'].eq('Amorphous ibuprofen').sum()} amorphous samples")
    if has_poloxamer:
        print(f"PCA analysis includes {df_filtered['Formulation Principle'].eq('Ibuprofen poloxamer 407').sum()} poloxamer 407 samples")
    
    # Select color palette based on the grouping variable
    if color_by == 'Formulation Type':
        palette = FORMULATION_COLORS
    elif color_by == 'Formulation Principle':
        palette = PRINCIPLE_COLORS
    else:  # Dosage Form
        palette = DOSAGE_COLORS
    
    # Extract numerical data for PCA
    X = df_filtered[pk_columns].copy()
    
    # Standardize the features (important for PCA)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Perform PCA
    pca = PCA()
    pca_result = pca.fit_transform(X_scaled)
    
    # Calculate relative contribution (explained variance ratio)
    explained_variance_ratio = pca.explained_variance_ratio_
    cumulative_variance = np.cumsum(explained_variance_ratio)
    
    # Print the variance explained by each component
    print("\nRelative contribution of each principal component:")
    for i, var_ratio in enumerate(explained_variance_ratio):
        print(f"PC{i+1}: {var_ratio:.4f} ({var_ratio*100:.2f}% of total variance)")
    
    print(f"\nPC1 and PC2 combined explain {(explained_variance_ratio[0] + explained_variance_ratio[1])*100:.2f}% of total variance")
    
    # Plot the explained variance
    plt.figure(figsize=(10, 6))
    
    # Plot individual and cumulative explained variance
    plt.bar(range(1, len(explained_variance_ratio) + 1), explained_variance_ratio, alpha=0.7, 
            color='#440154', label='Individual explained variance')
    plt.step(range(1, len(cumulative_variance) + 1), cumulative_variance, where='mid',
             color='#21918c', label='Cumulative explained variance')
    
    plt.axhline(y=0.95, color='#5ec962', linestyle='--', alpha=0.7, label='95% threshold')
    plt.ylabel('Explained variance ratio')
    plt.xlabel('Principal component')
    plt.xticks(range(1, len(explained_variance_ratio) + 1))
    plt.legend(loc='best')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save explained variance plot only once (for the first color_by option)
    if color_by == 'Formulation Type':
        plt.savefig('pca_explained_variance.png', dpi=600)
        print("Saved PCA explained variance plot")
    
    # Plot PCA projection (first two components)
    plt.figure(figsize=(10, 8))
    
    # Create a scatter plot colored by the specified column
    unique_values = df_filtered[color_by].unique()
    for value in unique_values:
        mask = df_filtered[color_by] == value
        if mask.sum() > 0:  # Only plot if there are data points for this value
            # Special handling for amorphous and poloxamer samples
            is_amorphous = (value == 'Amorphous ibuprofen')
            is_poloxamer = (value == 'Ibuprofen poloxamer 407')
            
            # Set marker and size based on formulation type
            if is_amorphous:
                marker = 'D'  # Diamond for amorphous
                size = 120
                edge_color = 'black'
                line_width = 1
                z_order = 10
            elif is_poloxamer:
                marker = 's'  # Square for poloxamer
                size = 120
                edge_color = 'black'
                line_width = 1
                z_order = 9
            else:
                marker = 'o'  # Circle for all others
                size = 80
                edge_color = 'w'
                line_width = 0.5
                z_order = 1
            
            plt.scatter(
                pca_result[mask, 0], 
                pca_result[mask, 1],
                alpha=0.7,
                s=size,
                marker=marker,
                edgecolor=edge_color,
                linewidth=line_width,
                color=palette.get(value, '#777777'),
                label=value,
                zorder=z_order
            )
            
            # Add annotations for special formulations
            if is_amorphous:
                for i, (x, y) in enumerate(zip(pca_result[mask, 0], pca_result[mask, 1])):
                    plt.annotate(
                        "A",  # A for Amorphous
                        (x, y),
                        xytext=(5, 5),
                        textcoords='offset points',
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", alpha=0.7),
                        fontsize=8,
                        fontweight='normal',
                        zorder=11
                    )
            elif is_poloxamer:
                for i, (x, y) in enumerate(zip(pca_result[mask, 0], pca_result[mask, 1])):
                    plt.annotate(
                        "B",  # B for poloxamer as requested
                        (x, y),
                        xytext=(5, 5),
                        textcoords='offset points',
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", alpha=0.7),
                        fontsize=8,
                        fontweight='normal',
                        zorder=11
                    )
    
    # Add feature vectors
    feature_vectors = pca.components_.T
    feature_names = [PARAM_LABELS.get(col, col) for col in pk_columns]
    
    # Calculate scaling factor to fit vectors on plot
    scaling_factor = 5
    
    # Plot vectors and labels
    for i, (vec, name) in enumerate(zip(feature_vectors, feature_names)):
        plt.arrow(0, 0, vec[0]*scaling_factor, vec[1]*scaling_factor, 
                 color='k', alpha=0.7, head_width=0.2)
        plt.text(vec[0]*scaling_factor*1.15, vec[1]*scaling_factor*1.15, name, 
                color='k', ha='center', va='center', fontsize=12)
    
    # Add axis labels with variance explained
    plt.xlabel(f'PC1 ({explained_variance_ratio[0]:.2%} explained variance)')
    plt.ylabel(f'PC2 ({explained_variance_ratio[1]:.2%} explained variance)')
    
    # Add legend
    plt.legend(title=color_by, title_fontsize=12)
    
    # Add equal aspect ratio for proper vector visualization
    plt.axis('equal')
    
    # Add origin lines
    plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
    
    plt.tight_layout()
    filename = f"pca_biplot_by_{color_by.lower().replace(' ', '_')}.png"
    plt.savefig(filename, dpi=600)
    print(f"Saved PCA biplot as {filename}")
    
    # Create a DataFrame with PCA results for potential further analysis
    pca_df = pd.DataFrame(
        data=pca_result[:, :2],
        columns=['PC1', 'PC2']
    )
    pca_df[color_by] = df_filtered[color_by].values
    
    # Save PCA results to CSV
    csv_filename = f"pca_results_by_{color_by.lower().replace(' ', '_')}.csv"
    pca_df.to_csv(csv_filename, index=False)
    print(f"Saved PCA results to {csv_filename}")
    
    return pca, pca_result, explained_variance_ratio
