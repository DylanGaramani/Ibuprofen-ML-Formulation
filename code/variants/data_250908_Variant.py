
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import warnings
warnings.filterwarnings('ignore')

# Set up basic plotting parameters for publication quality
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['axes.grid'] = False
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10

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
            val = re.search(r'<\s*(\d*\.?\d+)', str_val)
            if val:
                return float(val.group(1)) / 2
            return np.nan
        except:
            return np.nan
    
    # Handle "greater than" values (e.g., ">10")
    elif '>' in str_val:
        try:
            val = re.search(r'>\s*(\d*\.?\d+)', str_val)
            if val:
                return float(val.group(1)) * 1.5
            return np.nan
        except:
            return np.nan
    
    # Handle approximately values (e.g., "~10")
    elif '~' in str_val:
        try:
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
    if any(term in description for term in ['topical', 'cream', 'gel', 'ointment']):
        return 'Excluded'
    
    # Classification rules based ONLY on tmax thresholds
    if tmax_val > 3.5:
        return 'Extended Release'
    elif tmax_val < 0.83:
        return 'Rapid'
    else:
        return 'Standard'

def identify_dosage_form(description):
    """Identify dosage form from description with specific grouping"""
    if pd.isna(description):
        return "Tablet"  # Default to Tablet if no description
        
    description = str(description).lower()
    
    # Filter out topical and rectal formulations
    if any(term in description for term in ['rectal', 'suppository', 'topical', 'cream', 'ointment']):
        return "Excluded"
    
    # Check for different dosage forms based on specified groups
    if any(term in description for term in ['tablet', 'tab.', 'tabs']):
        return "Tablet"
    
    # Soft gel capsule detection
    elif any(term in description for term in ['soft gel', 'softgel', 'soft-gel', 'sgc', ' sc ', 'soft capsule']):
        return "Soft Gel Capsule"
    
    # Regular capsule becomes tablet as per requirements
    elif any(term in description for term in ['capsule', 'cap.', 'caps']):
        return "Tablet"
    
    # Oral suspension
    elif any(term in description for term in ['suspension', 'susp.']):
        if 'sachet' in description:
            return "Oral Suspension (Sachet)"
        else:
            return "Oral Suspension"
    
    # Solution/Liquid
    elif any(term in description for term in ['liquid', 'solution', 'syrup']):
        return "Solution/Liquid"
    
    # Granules
    elif 'granule' in description:
        return "Granules"
    
    # As requested, if undefined, consider it a tablet
    else:
        return "Tablet"

def identify_formulation_principle(row):
    """Identify formulation principle from description with specific grouping"""
    if pd.isna(row['description']):
        return "Ibuprofen (acid)"  # Changed from "Ibuprofen Acid" to "Ibuprofen (acid)"
        
    description = str(row['description']).lower()
    brand = str(row.get('brand', '')).lower() if pd.notna(row.get('brand', '')) else ''
    
    # Add dexibuprofen detection
    if any(term in description or term in brand for term in ['dexibuprofen', 's(+)', 's-ibuprofen', 's+ibuprofen', 's-isomer']):
        return "Dexibuprofen (S(+) ibuprofen)"
    
    elif any(term in description or term in brand for term in ['sodium', 'na+', 'na salt', 'na-salt', 'ibu-na', 'ibuna']):
        return "Ibuprofen Sodium Dihydrate"
    
    elif any(term in description or term in brand for term in ['lysine', 'lys', 'ibu-lys', 'ibulys', 'lysinate']):
        return "Ibuprofen Lysine"
    
    elif any(term in description or term in brand for term in ['arginine', 'arg', 'ibu-arg', 'ibuarg', 'arginate']):
        return "Ibuprofen Arginine"
    
    elif any(term in description or term in brand for term in ['aluminum', 'aluminium', 'al salt']):
        return "Ibuprofen Aluminium"
    
    elif any(term in description or term in brand for term in ['amorphous', 'amorph']):
        return "Amorphous Ibuprofen"
    
    elif any(term in description or term in brand for term in ['extended release', 'extended-release', 'er', 'slow release', 'controlled release', 'cr']):
        return "Extended Release"
    
    else:
        return "Ibuprofen (acid)"  # Changed from "Ibuprofen Acid" to "Ibuprofen (acid)"

def load_and_preprocess_data(file_path):
    """Load and preprocess the data from CSV or Excel file"""
    print(f"\nLoading matched PK data from {file_path}...")
    try:
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        print(f"Successfully loaded data with {df.shape[0]} rows and {df.shape[1]} columns")
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        exit()
    
    # Convert data to numeric with special handling
    print("\nConverting data to numeric format with special value handling...")
    numeric_columns = ['tmax', 'cmax', 'auc', 't1_2', 'dose']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_special_numeric)
    
    # Classify formulation types
    print("\nClassifying formulation types based on tmax values...")
    df['Formulation Type'] = df.apply(classify_formulation, axis=1)
    
    # Apply the dosage form identification function
    print("\nIdentifying dosage forms...")
    df['Dosage Form'] = df['description'].apply(identify_dosage_form)
    
    # Apply the formulation principle identification function
    print("\nIdentifying formulation principles...")
    df['Formulation Principle'] = df.apply(identify_formulation_principle, axis=1)
    
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
    
    return df

def create_formulation_heatmap(df_filtered):
    """Create heatmap of formulation principles and dosage forms"""
    print("\nCreating formulation combination heatmap...")
    
    # First, filter out excluded dosage forms
    df_filtered = df_filtered[df_filtered['Dosage Form'] != 'Excluded']
    
    # Filter out Extended Release formulation types
    print(f"Samples before filtering Extended Release formulation types: {len(df_filtered)}")
    df_filtered = df_filtered[df_filtered['Formulation Type'] != 'Extended Release']
    print(f"Samples after filtering Extended Release formulation types: {len(df_filtered)}")
    
    # Filter out Extended Release formulation principles
    print(f"Samples before filtering Extended Release formulation principles: {len(df_filtered)}")
    df_filtered = df_filtered[df_filtered['Formulation Principle'] != 'Extended Release']
    print(f"Samples after filtering Extended Release formulation principles: {len(df_filtered)}")
    
    # Convert any "Undefined" dosage forms to "Tablet"
    df_filtered.loc[df_filtered['Dosage Form'] == 'Undefined', 'Dosage Form'] = 'Tablet'
    
    # Ensure we have only the specified dosage form groups
    valid_forms = ['Tablet', 'Soft Gel Capsule', 'Oral Suspension', 
                  'Solution/Liquid', 'Oral Suspension (Sachet)', 'Granules']
    
    # Map any non-standard forms to the closest valid form
    form_mapping = {
        'Film-Coated Tablet': 'Tablet',
        'Sugar-Coated Tablet': 'Tablet',
        'Capsule': 'Tablet',
        'Suspension': 'Oral Suspension',
        'Sachet': 'Oral Suspension (Sachet)'
    }
    
    # Apply form mapping
    for old_form, new_form in form_mapping.items():
        df_filtered.loc[df_filtered['Dosage Form'] == old_form, 'Dosage Form'] = new_form
    
    # Create crosstab with Formulation Principle on Y-axis and Dosage Form on X-axis
    combo_counts = pd.crosstab(df_filtered['Formulation Principle'], df_filtered['Dosage Form'])
    
    # Reorder columns to make "Tablet" the first column
    if 'Tablet' in combo_counts.columns:
        columns = ['Tablet'] + [col for col in combo_counts.columns if col != 'Tablet']
        combo_counts = combo_counts[columns]
    
    # Create figure with specified size
    plt.figure(figsize=(14, 10))
    
    # Use custom colormap with increased font size for annotations
    sns.heatmap(
        combo_counts, 
        annot=True, 
        fmt='d', 
        cmap="YlGnBu", 
        linewidths=0.5,
        annot_kws={"size": 14},  # Increased font size for numbers in cells
        cbar_kws={'label': 'Frequency'}
    )
    
    # No title as requested
    plt.ylabel('Formulation Principle', fontsize=14)  # Increased font size
    plt.xlabel('Dosage Form', fontsize=14)  # Increased font size
    plt.xticks(rotation=45, ha='right', fontsize=12)  # Increased font size for x-axis labels
    plt.yticks(fontsize=12)  # Increased font size for y-axis labels
    plt.tight_layout()
    plt.savefig('formulation_combination_heatmap_without_er.png', dpi=600)
    print("Saved formulation combination heatmap without Extended Release samples")

def main():
    """Main function to run only the heatmap analysis"""
    print("===== IBUPROFEN FORMULATION HEATMAP (WITHOUT EXTENDED RELEASE) =====")
    
    # Use the correct file path for the most updated source file
    data_file = 'matched_pk_data_2.xlsx'
    
    # Load and preprocess data with the updated file path
    df = load_and_preprocess_data(data_file)
    
    # Filter rows for analysis
    df_filtered = df[df['Formulation Type'].notna()]
    
    # Filter out 'Unknown' and 'Excluded' formulation types
    df_filtered = df_filtered[~df_filtered['Formulation Type'].isin(['Unknown', 'Excluded'])]
    
    print(f"\nDataset after filtering Unknown and Excluded: {df_filtered.shape[0]} samples")
    
    # Count Extended Release samples
    er_formulation_type_count = len(df_filtered[df_filtered['Formulation Type'] == 'Extended Release'])
    er_formulation_principle_count = len(df_filtered[df_filtered['Formulation Principle'] == 'Extended Release'])
    print(f"Number of samples with Extended Release formulation type: {er_formulation_type_count}")
    print(f"Number of samples with Extended Release formulation principle: {er_formulation_principle_count}")
    
    # Create formulation combination heatmap
    create_formulation_heatmap(df_filtered)
    
    print("\n===== ANALYSIS COMPLETE =====")
    print("Heatmap visualization saved as high-resolution (600 DPI) PNG file")

if __name__ == "__main__":
    main()
