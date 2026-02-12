
import pandas as pd
import numpy as np
import re
import excipient_sorting

def load_and_preprocess_data(file_path="data_excipient.xlsx"):
    """
    Load and preprocess the data from Excel file
    
    Parameters:
    -----------
    file_path : str
        Path to the Excel file containing formulation data
    
    Returns:
    --------
    df : pandas.DataFrame
        The preprocessed formulation data
    excipient_data : dict
        Dictionary containing excipient frequency data organized by type
    excipient_columns : list
        List of column names related to excipients
    """
    # Load data
    print(f"Loading data from {file_path}...")
    df = pd.read_excel(file_path)
    
    # Display initial data information
    print(f"\nInitial data overview: {len(df)} rows, {len(df.columns)} columns")
    
    # Clean up column names if needed
    df.columns = [col.strip() for col in df.columns]
    
    # Handle dose information if available
    if 'API dose (mg /mL)' in df.columns:
        # Extract numeric values from dose column
        df['Dose_numeric'] = df['API dose (mg /mL)'].apply(
            lambda x: extract_numeric_dose(x) if pd.notna(x) else np.nan)
        print("\nDose conversion summary:")
        print(df[['API dose (mg /mL)', 'Dose_numeric']].head())
    
    # Process excipient columns
    excipient_columns = identify_excipient_columns(df)
    print(f"\nIdentified {len(excipient_columns)} excipient-related columns")
    
    # Organize excipients by type
    excipient_data = organize_excipients(df, excipient_columns)
    print("\nOrganized excipients by type")
    
    return df, excipient_data, excipient_columns

def extract_numeric_dose(dose_value):
    """
    Extract numeric dose value from different formats
    
    Parameters:
    -----------
    dose_value : str, float, or int
        The dose value to extract from
    
    Returns:
    --------
    float or np.nan : The extracted numeric dose value
    """
    if pd.isna(dose_value):
        return np.nan
    
    if isinstance(dose_value, (int, float)):
        return dose_value
    
    if isinstance(dose_value, str):
        # Try to extract numbers from the string
        numbers = re.findall(r'(\d+\.?\d*)', dose_value)
        if numbers:
            return float(numbers[0])
    
    return np.nan

def identify_excipient_columns(df):
    """
    Identify all columns related to excipients
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The formulation data
    
    Returns:
    --------
    list : List of column names related to excipients
    """
    # Updated to include Surfactant/solubilizer
    excipient_types = [
        'Bulking agent', 'Binder', 'Super-disintegrant', 
        'Glidant', 'Lubricant', 'pH-adjuster', 
        'Surfactant', 'Solubilizer', 'Coating', 'Colorant'
    ]
    
    excipient_columns = []
    for col in df.columns:
        if any(excip_type in col for excip_type in excipient_types):
            excipient_columns.append(col)
    
    # Add additional checks for specific excipients that might be missed
    for col in df.columns:
        col_str = str(col).lower()
        if 'iron oxide' in col_str or 'erythrosine' in col_str or 'colorant' in col_str or 'pigment' in col_str:
            if col not in excipient_columns:
                excipient_columns.append(col)
    
    # Check unnamed columns for potential excipient data
    unnamed_columns = [col for col in df.columns if 'unnamed' in str(col).lower()]
    for col in unnamed_columns:
        # Check if this column contains any known excipients
        sample_values = df[col].dropna().astype(str).str.lower()
        if any(sample_values.str.contains('iron oxide')) or any(sample_values.str.contains('erythrosine')):
            if col not in excipient_columns:
                excipient_columns.append(col)
                print(f"Added column {col} containing iron oxide or erythrosine")
    
    return excipient_columns

def identify_excipient_columns_by_type(df, excip_type):
    """
    Identify columns related to a specific excipient type
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The dataframe containing excipient data
    excip_type : str
        The excipient type to identify columns for
    
    Returns:
    --------
    list : List of column names related to the specified excipient type
    """
    # Special case for Surfactant/solubilizer
    if excip_type == 'Surfactant/solubilizer':
        excipient_columns = []
        for col in df.columns:
            col_lower = str(col).lower()
            if 'surfactant' in col_lower or 'solubilizer' in col_lower or 'solubiliser' in col_lower:
                excipient_columns.append(col)
        return excipient_columns
    
    # Special case for Colorant - check coating columns and unnamed columns too
    if excip_type == 'Colorant':
        excipient_columns = [col for col in df.columns if 'colorant' in str(col).lower() or 'pigment' in str(col).lower()]
        # Add coating columns
        coating_columns = [col for col in df.columns if 'coating' in str(col).lower()]
        excipient_columns.extend(coating_columns)
        # Add unnamed columns that might contain colorants
        for col in df.columns:
            if 'unnamed' in str(col).lower():
                excipient_columns.append(col)
        return excipient_columns
    
    # Find columns related to this excipient type
    excip_type_for_match = excip_type.split('/')[0]
    return [col for col in df.columns if excip_type_for_match.lower() in str(col).lower()]

def organize_excipients(df, excipient_columns):
    """
    Organize excipients by type and count frequencies
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The formulation data
    excipient_columns : list
        List of column names related to excipients
    
    Returns:
    --------
    dict : Dictionary containing excipient frequency data organized by type
    """
    excipient_data = {}
    
    # Define excipient types to look for - Updated to include Surfactant/solubilizer
    excipient_types = [
        'Bulking agent', 'Binder', 'Super-disintegrant', 
        'Glidant', 'Lubricant', 'pH-adjuster', 
        'Surfactant/solubilizer', 'Coating', 'Colorant'
    ]
    
    # For each excipient type, collect all non-empty values
    for excip_type in excipient_types:
        # Get related columns for this excipient type
        related_columns = identify_excipient_columns_by_type(df, excip_type)
        
        all_excipients = []
        # For each row in the dataframe
        for _, row in df.iterrows():
            # Extract non-empty excipients of this type
            for col in related_columns:
                if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                    # Apply category-specific filtering
                    if should_include_excipient(row[col], excip_type, row.get('Form', 'Unknown')):
                        standardized_name = excipient_sorting.standardize_excipient_names(row[col])
                        if standardized_name:
                            all_excipients.append(standardized_name)
        
        # Count frequencies
        if all_excipients:
            excipient_counts = pd.Series(all_excipients).value_counts()
            
            # Sort excipients to group similar ones together
            excipient_counts = excipient_sorting.sort_excipients(excipient_counts)
            
            excipient_data[excip_type] = excipient_counts
        else:
            excipient_data[excip_type] = pd.Series()
            
        # Print the excipients found for debugging
        if not excipient_data[excip_type].empty:
            print(f"\nFound {len(excipient_data[excip_type])} unique {excip_type}s (grouped by type):")
            print(excipient_data[excip_type])
    
    return excipient_data

def should_include_excipient(excipient_value, excip_type, dosage_form):
    """
    Determine if an excipient should be included in a specific category
    
    Parameters:
    -----------
    excipient_value : str
        The excipient value from the dataframe
    excip_type : str
        The excipient type category being analyzed
    dosage_form : str
        The dosage form being analyzed
    
    Returns:
    --------
    bool : Whether the excipient should be included
    """
    excip_value = str(excipient_value).lower()
    
    # Category-specific filtering logic
    if excip_type == 'Colorant':
        return ('iron oxide' in excip_value or 'erythrosine' in excip_value or 
                'color' in excip_value or 'pigment' in excip_value)
    
    elif excip_type == 'Coating':
        # Special handling for gelatin to ensure it's only associated with appropriate forms
        if 'gelatin' in excip_value:
            # Allow gelatin for soft gel capsules or other gel/capsule forms
            if ('soft gel' in str(dosage_form).lower() or 'softgel' in str(dosage_form).lower() or
                'gel' in str(dosage_form).lower() or 'capsule' in str(dosage_form).lower()):
                return True
            return False
        return True
    
    elif excip_type == 'Bulking agent':
        # Skip gelatin as a bulking agent to prevent miscategorization
        if 'gelatin' in excip_value and 'starch' not in excip_value and 'pregelatin' not in excip_value:
            print(f"⚠ WARNING: Gelatin found in bulking agent. Skipping.")
            return False
        return True
    
    # Default case - include the excipient
    return True

def verify_excipient_categories(df):
    """
    Verify that excipients are correctly categorized and report any potential issues
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The formulation data
    
    Returns:
    --------
    None, prints verification results
    """
    print("\nVerifying excipient categorization...")
    
    # Look for potential miscategorizations
    coating_columns = [col for col in df.columns if 'coating' in str(col).lower()]
    bulking_columns = [col for col in df.columns if 'bulking' in str(col).lower()]
    
    # Check for gelatin specifically
    gelatin_in_coatings = False
    gelatin_in_bulking = False
    
    # Check coating columns for gelatin
    for col in coating_columns:
        if df[col].astype(str).str.contains('gelatin', case=False, na=False).any():
            gelatin_in_coatings = True
            print(f"✓ Gelatin correctly found in coating column: {col}")
            
            # Check which forms use gelatin as coating
            gelatin_forms = df[df[col].astype(str).str.contains('gelatin', case=False, na=False)]['Form'].unique()
            print(f"  Forms using gelatin as coating: {', '.join(map(str, gelatin_forms))}")
    
    # Check bulking columns for gelatin
    for col in bulking_columns:
        if df[col].astype(str).str.contains('gelatin', case=False, na=False).any():
            # Check if it's actually pregelatinized starch
            pregelatin_entries = df[df[col].astype(str).str.contains('pregelatin|pregelatinized', case=False, na=False)]
            if len(pregelatin_entries) > 0:
                print(f"✓ Pregelatinized starch correctly found in bulking agent column: {col}")
            
            # Check for actual gelatin (not pregelatinized starch)
            pure_gelatin = df[(df[col].astype(str).str.contains('gelatin', case=False, na=False)) & 
                             (~df[col].astype(str).str.contains('pregelatin|pregelatinized|starch', case=False, na=False))]
            
            if len(pure_gelatin) > 0:
                gelatin_in_bulking = True
                print(f"⚠ WARNING: Gelatin incorrectly found in bulking agent column: {col}")
                print(f"  Entries: {pure_gelatin[col].tolist()}")
    
    # Report findings
    if not gelatin_in_coatings:
        print("⚠ WARNING: Gelatin not found in any coating columns")
    
    if not gelatin_in_bulking:
        print("✓ Correctly verified: Gelatin not found in bulking agent columns")
    
    # Check for pregelatinized starch
    pregelatin_found = False
    for col in bulking_columns:
        if df[col].astype(str).str.contains('pregelatin', case=False, na=False).any():
            pregelatin_found = True
            print(f"✓ Pregelatinized starch correctly found in bulking agent column: {col}")
    
    if not pregelatin_found:
        print("ℹ️ Note: No pregelatinized starch found in bulking agent columns")
    
    # Check for povidone variants
    print("\nChecking for povidone variants...")
    povidone_types = {}
    
    for col in df.columns:
        for pov_type in ['povidone', 'crospovidone', 'copovidone']:
            if df[col].astype(str).str.contains(pov_type, case=False, na=False).any():
                if pov_type not in povidone_types:
                    povidone_types[pov_type] = []
                povidone_types[pov_type].append(col)
    
    for pov_type, columns in povidone_types.items():
        print(f"Found {pov_type} in columns: {', '.join(columns)}")
    
    print("Excipient categorization verification complete")

def create_excipient_standardization_table(df, excipient_columns):
    """
    Create a standardization mapping table for excipients to help resolve duplicate entities
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The formulation data
    excipient_columns : list
        List of column names related to excipients
    
    Returns:
    --------
    pandas.DataFrame : Standardization table with original and standardized names
    """
    all_excipients = []
    
    # Collect all excipients from the relevant columns
    for col in excipient_columns:
        values = df[col].dropna().tolist()
        all_excipients.extend([v for v in values if v != '' and v != 'n/a'])
    
    # Create a DataFrame with original and standardized names
    std_table = pd.DataFrame({
        'Original_Name': all_excipients,
        'Standardized_Name': [excipient_sorting.standardize_excipient_names(e) for e in all_excipients]
    })
    
    # Remove duplicates
    std_table = std_table.drop_duplicates()
    
    # Sort by our custom sorting function to group similar excipients
    std_table['sort_key'] = [excipient_sorting.get_excipient_sort_key(name) for name in std_table['Standardized_Name']]
    std_table = std_table.sort_values('sort_key')
    std_table = std_table.drop('sort_key', axis=1)
    
    # Save to Excel
    std_table.to_excel('excipient_standardization_table.xlsx', index=False)
    
    print("\nExcipient standardization table created and saved to 'excipient_standardization_table.xlsx'")
    print("Similar excipients are now grouped together while keeping specific categories separate")
    return std_table

# Simple test if run directly
if __name__ == "__main__":
    print("Processing module loaded successfully!")
