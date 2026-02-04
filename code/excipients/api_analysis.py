
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Set matplotlib parameters for better visualization
plt.rcParams['savefig.dpi'] = 600  # Default DPI for all figures
plt.rcParams['figure.dpi'] = 600  # Screen display DPI
plt.rcParams['font.size'] = 18  # Default font size
plt.rcParams['axes.titlesize'] = 20  # Title font size (though we'll remove titles)
plt.rcParams['axes.labelsize'] = 18  # Axis label font size
plt.rcParams['xtick.labelsize'] = 18  # X-axis tick label size
plt.rcParams['ytick.labelsize'] = 18  # Y-axis tick label size

def standardize_api_name(api_name):
    """
    Standardize API names while preserving salt forms and variants
    
    Parameters:
    -----------
    api_name : str
        The original API name
        
    Returns:
    --------
    str : Standardized API name that preserves distinct chemical entities
    """
    if pd.isna(api_name) or api_name == '' or api_name == 'n/a':
        return None
    
    # Convert to string and strip whitespace
    name = str(api_name).strip()
    
    # Normalize whitespace (replace multiple spaces with single space)
    name = ' '.join(name.split())
    
    # Standardize capitalization (first letter of each word capitalized)
    name = name.title()
    
    # Standardize common abbreviations
    abbreviations = {
        " Hcl": " HCl",
        " Hbr": " HBr",
        " Xr": " XR",
        " Cr": " CR",
        " Sr": " SR",
        " Er": " ER",
        " Ir": " IR",
        " Cd": " CD",
    }
    
    for abbr, replacement in abbreviations.items():
        if abbr in name:
            name = name.replace(abbr, replacement)
    
    # Special case for ibuprofen - explicitly label the acid form
    if name.lower() == "ibuprofen":
        name = "Ibuprofen (acid)"
    
    # Special case for paracetamol
    if name.lower() == "paracetamol":
        name = "Paracetamol (Acetaminophen)"
    
    # Special case for aspirin
    if name.lower() == "aspirin":
        name = "Aspirin (Acetylsalicylic acid)"
    
    # Handle other acid forms of common drugs that might not be explicitly labeled
    common_acids = {
        "Naproxen": "Naproxen (acid)",
        "Diclofenac": "Diclofenac (acid)",
        "Ketoprofen": "Ketoprofen (acid)"
    }
    
    for base, labeled in common_acids.items():
        if name.lower() == base.lower():
            name = labeled
    
    return name

def analyze_api_distribution(df):
    """
    Analyze API distribution across formulations and create visualizations
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
        
    Returns:
    --------
    pandas.DataFrame : API distribution by dosage form
    """
    print("\nAnalyzing API distribution across formulations...")
    
    # Identify API-related columns
    api_columns = [col for col in df.columns if 'API' in str(col) or 'Active' in str(col)]
    
    # If no specific API columns are found, look for alternative naming
    if not api_columns:
        potential_api_cols = [col for col in df.columns if 'Drug' in str(col) or 'Ingredient' in str(col)]
        api_columns.extend(potential_api_cols)
    
    print(f"Identified {len(api_columns)} API-related columns: {', '.join(api_columns)}")
    
    # Extract API information
    all_apis = []
    
    for _, row in df.iterrows():
        form = row.get('Form', 'Unknown') if pd.notna(row.get('Form', 'Unknown')) else 'Unknown'
        
        for col in api_columns:
            if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                # Standardize API names while preserving distinct variants
                api_name = standardize_api_name(row[col])
                if api_name:
                    all_apis.append({
                        'API': api_name,
                        'Dosage_Form': form
                    })
    
    if not all_apis:
        print("No API information found in the dataset")
        return None
    
    # Create a DataFrame for APIs
    api_df = pd.DataFrame(all_apis)
    print(f"Found {len(set(api_df['API']))} unique APIs across {len(set(api_df['Dosage_Form']))} dosage forms")
    
    # Show some examples of standardized API names
    print("\nExamples of standardized API names:")
    for i, api in enumerate(sorted(set(api_df['API']))[:10]):
        print(f"{i+1}. {api}")
    if len(set(api_df['API'])) > 10:
        print(f"... and {len(set(api_df['API'])) - 10} more")
    
    # Create distribution chart
    create_api_distribution_chart(api_df)
    
    # Create heatmap of APIs by dosage form
    api_heatmap = create_api_dosage_form_heatmap(api_df)
    
    # Analyze API dose distribution if dose information is available
    if 'API dose (mg /mL)' in df.columns or 'Dose_numeric' in df.columns:
        analyze_api_dose_distribution(df)
    
    # Create an API classification table to show all standardized names
    create_api_classification_table(all_apis)
    
    return api_heatmap

def create_api_classification_table(api_data):
    """
    Create a table showing all unique API names
    
    Parameters:
    -----------
    api_data : list
        List of dictionaries containing API information
    
    Returns:
    --------
    None, but saves classification table to file
    """
    # Extract unique APIs
    unique_apis = sorted(set([item['API'] for item in api_data]))
    
    # Create a DataFrame for the classification table
    api_table = pd.DataFrame({'API': unique_apis})
    
    # Add columns for API base and form
    api_table['Base_Compound'] = api_table['API'].apply(extract_base_compound)
    api_table['Form_or_Salt'] = api_table['API'].apply(extract_form_or_salt)
    
    # Count occurrences of each API
    api_counts = pd.Series([item['API'] for item in api_data]).value_counts()
    api_table['Occurrence_Count'] = api_table['API'].map(api_counts)
    
    # Sort by base compound and then by occurrence count
    api_table = api_table.sort_values(['Base_Compound', 'Occurrence_Count'], ascending=[True, False])
    
    # Save to CSV
    api_table.to_csv('api_classification_table.csv', index=False)
    print(f"Created API classification table with {len(api_table)} entries")
    return api_table

def extract_base_compound(api_name):
    """Extract the base compound name from a full API name"""
    # Handle already labeled acid forms
    if '(acid)' in api_name:
        return api_name.split(' (')[0]
    
    # This is a simplified approach - in a real system you might want 
    # a more sophisticated chemical name parser
    parts = api_name.split()
    if len(parts) == 1:
        return api_name
    
    # Check for common salt indicators
    salt_indicators = ['sodium', 'potassium', 'calcium', 'magnesium', 
                      'hydrochloride', 'hcl', 'sulfate', 'maleate',
                      'tartrate', 'citrate', 'phosphate', 'nitrate',
                      'mesylate', 'besylate', 'tosylate', 'dihydrate',
                      'monohydrate', 'anhydrous', 'hydrate', 'trihydrate',
                      'lysine', 'arginine']
    
    # Handle parenthesized terms (like in "Ibuprofen (acid)")
    paren_match = re.search(r'(.*?)\s*\([^)]*\)', api_name)
    if paren_match:
        return paren_match.group(1).strip()
    
    base_words = []
    for word in parts:
        word_lower = word.lower()
        if word_lower in salt_indicators:
            break
        base_words.append(word)
    
    if not base_words:
        return api_name
    
    return ' '.join(base_words)

def extract_form_or_salt(api_name):
    """Extract the salt form or variant information from a full API name"""
    # Handle explicitly labeled acid forms
    if '(acid)' in api_name:
        return "Acid Form"
        
    base = extract_base_compound(api_name)
    if base == api_name:
        # Check for parenthesized forms
        paren_match = re.search(r'\((.*?)\)', api_name)
        if paren_match:
            return paren_match.group(1)
        return "Base Form"
    
    # Remove the base compound to get the salt/form
    remainder = api_name.replace(base, '').strip()
    if not remainder:
        return "Base Form"
    
    return remainder

def create_api_distribution_chart(api_df):
    """
    Create a distribution chart showing frequency of different APIs
    
    Parameters:
    -----------
    api_df : pandas.DataFrame
        DataFrame containing API information
        
    Returns:
    --------
    None, but saves visualization file
    """
    # Count API frequencies
    api_counts = api_df['API'].value_counts()
    
    # For visualization clarity, limit to top 20 if there are many APIs
    if len(api_counts) > 20:
        print(f"Limiting distribution chart to top 20 APIs out of {len(api_counts)} total")
        api_counts = api_counts.head(20)
    
    # Create bar chart (without title)
    plt.figure(figsize=(14, 8))
    api_counts.plot(kind='bar', color='skyblue')
    plt.xlabel('API')
    plt.ylabel('Frequency')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('api_distribution.png', dpi=600)
    plt.close()
    
    # Also save the data
    api_counts.to_csv('api_distribution_data.csv')
    print("Created API distribution chart")
    
    # Create a second chart showing base compounds
    base_compounds = api_df['API'].apply(extract_base_compound)
    base_counts = base_compounds.value_counts()
    
    if len(base_counts) > 20:
        base_counts = base_counts.head(20)
    
    plt.figure(figsize=(14, 8))
    base_counts.plot(kind='bar', color='lightgreen')
    plt.xlabel('Base Compound')
    plt.ylabel('Frequency')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('api_base_distribution.png', dpi=600)
    plt.close()
    
    base_counts.to_csv('api_base_distribution_data.csv')
    print("Created API base compound distribution chart")

def create_api_dosage_form_heatmap(api_df):
    """
    Create a heatmap showing API usage by dosage form
    
    Parameters:
    -----------
    api_df : pandas.DataFrame
        DataFrame containing API information
        
    Returns:
    --------
    pandas.DataFrame : Pivot table of APIs by dosage form
    """
    # Create pivot table: rows=APIs, columns=dosage forms
    api_pivot = pd.pivot_table(
        api_df,
        index='API',
        columns='Dosage_Form',
        aggfunc='size',
        fill_value=0
    )
    
    # For visualization clarity, limit to top APIs if there are many
    if len(api_pivot) > 30:
        print(f"Limiting heatmap to top 30 APIs by frequency out of {len(api_pivot)} total")
        # Get the most frequently occurring APIs
        top_apis = api_df['API'].value_counts().head(30).index
        api_pivot = api_pivot.loc[top_apis]
    
    # Create heatmap (without title)
    plt.figure(figsize=(max(14, len(api_pivot.columns) * 1.5), 
                      max(10, len(api_pivot) * 0.5)))
    
    # Explicitly set annotation font size to match the surfactant plot
    sns.heatmap(api_pivot, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5, 
                annot_kws={'size': 14})  # Explicitly set annotation font size
    
    plt.ylabel('API')
    plt.xlabel('Dosage Form')
    plt.tight_layout()
    plt.savefig('api_by_dosage_form.png', dpi=600, bbox_inches='tight')
    plt.close()
    
    # Save the data
    api_pivot.to_csv('api_by_dosage_form_data.csv')
    print("Created heatmap of APIs by dosage form")
    
    # Create a second heatmap for base compounds if there are many distinct API forms
    if len(set(api_df['API'])) > len(set(api_df['API'].apply(extract_base_compound))) + 5:
        # Add base compound to the dataframe
        api_df_with_base = api_df.copy()
        api_df_with_base['Base_Compound'] = api_df_with_base['API'].apply(extract_base_compound)
        
        # Create pivot table for base compounds
        base_pivot = pd.pivot_table(
            api_df_with_base,
            index='Base_Compound',
            columns='Dosage_Form',
            aggfunc='size',
            fill_value=0
        )
        
        # Limit to top base compounds if there are many
        if len(base_pivot) > 30:
            top_bases = api_df_with_base['Base_Compound'].value_counts().head(30).index
            base_pivot = base_pivot.loc[top_bases]
        
        # Create heatmap (without title)
        plt.figure(figsize=(max(14, len(base_pivot.columns) * 1.5), 
                          max(10, len(base_pivot) * 0.5)))
        
        # Explicitly set annotation font size
        sns.heatmap(base_pivot, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5,
                    annot_kws={'size': 14})  # Explicitly set annotation font size
        
        plt.ylabel('Base Compound')
        plt.xlabel('Dosage Form')
        plt.tight_layout()
        plt.savefig('api_base_by_dosage_form.png', dpi=600, bbox_inches='tight')
        plt.close()
        
        # Save the data
        base_pivot.to_csv('api_base_by_dosage_form_data.csv')
        print("Created heatmap of base API compounds by dosage form")
    
    return api_pivot

def analyze_api_dose_distribution(df):
    """
    Analyze the distribution of API doses
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
        
    Returns:
    --------
    None, but saves visualization files
    """
    print("\nAnalyzing API dose distribution...")
    
    # Determine which dose column to use
    dose_col = 'Dose_numeric' if 'Dose_numeric' in df.columns else 'API dose (mg /mL)'
    
    # Filter out rows with missing dose information
    dose_df = df[pd.notna(df[dose_col])]
    
    if len(dose_df) == 0:
        print("No valid dose information found")
        return
    
    print(f"Found {len(dose_df)} formulations with valid dose information")
    
    # Create histogram of doses (without title)
    plt.figure(figsize=(12, 6))
    sns.histplot(dose_df[dose_col], kde=True, bins=20)
    plt.xlabel('Dose (mg/mL)')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig('api_dose_distribution.png', dpi=600)
    plt.close()
    
    # If dosage form information is available, create a boxplot by form
    if 'Form' in dose_df.columns:
        # Get top forms by frequency with at least 3 entries
        form_counts = dose_df['Form'].value_counts()
        top_forms = form_counts[form_counts >= 3].index
        
        if len(top_forms) > 0:
            plot_df = dose_df[dose_df['Form'].isin(top_forms)]
            
            # Create boxplot (without title)
            plt.figure(figsize=(14, 8))
            sns.boxplot(x='Form', y=dose_col, data=plot_df)
            plt.xlabel('Dosage Form')
            plt.ylabel('Dose (mg/mL)')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig('api_dose_by_form.png', dpi=600)
            plt.close()
            print("Created dose distribution boxplot by dosage form")
    
    # Create summary statistics for doses
    dose_stats = dose_df[dose_col].describe()
    print("\nAPI Dose Statistics:")
    print(dose_stats)
    
    # Save dose statistics
    dose_stats.to_csv('api_dose_statistics.csv')
    print("Saved API dose statistics")

def analyze_api_excipient_relationships(df, excipient_columns):
    """
    Analyze relationships between APIs and excipients
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
    excipient_columns : list
        List of column names related to excipients
        
    Returns:
    --------
    None, but saves visualization files
    """
    # This function requires both excipient_sorting and data_processing modules,
    # which would be imported in the main script
    
    print("\nAnalyzing API-excipient relationships...")
    
    # Import modules here to avoid circular imports
    import excipient_sorting
    from excipient_sorting import standardize_excipient_names
    
    # Identify API-related columns
    api_columns = [col for col in df.columns if 'API' in str(col) or 'Active' in str(col)]
    if not api_columns:
        potential_api_cols = [col for col in df.columns if 'Drug' in str(col) or 'Ingredient' in str(col)]
        api_columns.extend(potential_api_cols)
    
    if not api_columns:
        print("No API information found for relationship analysis")
        return
    
    # Extract standardized APIs and excipients
    all_api_excipient_pairs = []
    
    for _, row in df.iterrows():
        # Extract APIs for this formulation
        apis = []
        for col in api_columns:
            if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                api_name = standardize_api_name(row[col])
                if api_name:
                    apis.append(api_name)
        
        # Extract excipients for this formulation
        for col in excipient_columns:
            if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                excip_name = standardize_excipient_names(row[col])
                if excip_name:
                    # Create pairs of each API with each excipient
                    for api in apis:
                        all_api_excipient_pairs.append({
                            'API': api,
                            'Excipient': excip_name
                        })
    
    if not all_api_excipient_pairs:
        print("No API-excipient pairs found for analysis")
        return
    
    # Create a DataFrame for API-excipient pairs
    pairs_df = pd.DataFrame(all_api_excipient_pairs)
    
    # Count co-occurrences
    pair_counts = pairs_df.groupby(['API', 'Excipient']).size().reset_index(name='Count')
    
    # Create a pivot table for the heatmap
    # Limit to top APIs and excipients for visibility
    top_apis = pairs_df['API'].value_counts().head(15).index
    top_excipients = pairs_df['Excipient'].value_counts().head(20).index
    
    filtered_pairs = pair_counts[
        (pair_counts['API'].isin(top_apis)) & 
        (pair_counts['Excipient'].isin(top_excipients))
    ]
    
    # Create pivot table
    heatmap_data = filtered_pairs.pivot(index='API', columns='Excipient', values='Count').fillna(0)
    
    # Create heatmap (without title)
    plt.figure(figsize=(16, 10))
    
    # Explicitly set annotation font size
    sns.heatmap(heatmap_data, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5,
                annot_kws={'size': 14})  # Explicitly set annotation font size
    
    plt.ylabel('API')
    plt.xlabel('Excipient')
    plt.tight_layout()
    plt.savefig('api_excipient_relationship.png', dpi=600, bbox_inches='tight')
    plt.close()
    
    # Save the data
    heatmap_data.to_csv('api_excipient_relationship_data.csv')
    print("Created API-excipient relationship heatmap")
    
    # Also create a base compound version if there are many distinct API forms
    if len(set(pairs_df['API'])) > len(set(pairs_df['API'].apply(extract_base_compound))) + 5:
        # Add base compound
        pairs_df['Base_Compound'] = pairs_df['API'].apply(extract_base_compound)
        
        # Count co-occurrences by base compound
        base_counts = pairs_df.groupby(['Base_Compound', 'Excipient']).size().reset_index(name='Count')
        
        # Limit to top base compounds and excipients
        top_bases = pairs_df['Base_Compound'].value_counts().head(15).index
        filtered_base_pairs = base_counts[
            (base_counts['Base_Compound'].isin(top_bases)) & 
            (base_counts['Excipient'].isin(top_excipients))
        ]
        
        # Create pivot table
        base_heatmap = filtered_base_pairs.pivot(
            index='Base_Compound', 
            columns='Excipient', 
            values='Count'
        ).fillna(0)
        
        # Create heatmap (without title)
        plt.figure(figsize=(16, 10))
        
        # Explicitly set annotation font size
        sns.heatmap(base_heatmap, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5,
                    annot_kws={'size': 14})  # Explicitly set annotation font size
        
        plt.ylabel('Base API Compound')
        plt.xlabel('Excipient')
        plt.tight_layout()
        plt.savefig('api_base_excipient_relationship.png', dpi=600, bbox_inches='tight')
        plt.close()
        
        # Save the data
        base_heatmap.to_csv('api_base_excipient_relationship_data.csv')
        print("Created base API compound-excipient relationship heatmap")

def create_ibuprofen_specific_analysis(df):
    """
    Create a specialized analysis focusing on ibuprofen forms and their excipients
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
        
    Returns:
    --------
    None, but saves visualization files
    """
    print("\nCreating specialized analysis for ibuprofen forms...")
    
    # Import modules here to avoid circular imports
    import excipient_sorting
    from excipient_sorting import standardize_excipient_names
    
    # Identify API-related columns
    api_columns = [col for col in df.columns if 'API' in str(col) or 'Active' in str(col)]
    if not api_columns:
        potential_api_cols = [col for col in df.columns if 'Drug' in str(col) or 'Ingredient' in str(col)]
        api_columns.extend(potential_api_cols)
    
    # Identify ibuprofen formulations
    ibuprofen_forms = []
    
    for _, row in df.iterrows():
        for col in api_columns:
            if pd.notna(row[col]) and 'ibuprofen' in str(row[col]).lower():
                form = row.get('Form', 'Unknown') if pd.notna(row.get('Form', 'Unknown')) else 'Unknown'
                api_std = standardize_api_name(row[col])
                
                # Extract all excipients for this formulation
                excipient_columns = data_processing.identify_excipient_columns(df)
                excipients = []
                for ex_col in excipient_columns:
                    if pd.notna(row[ex_col]) and row[ex_col] != '' and row[ex_col] != 'n/a':
                        std_name = standardize_excipient_names(row[ex_col])
                        if std_name:
                            excipients.append(std_name)
                
                ibuprofen_forms.append({
                    'API': api_std,
                    'Dosage_Form': form,
                    'Excipients': '; '.join(excipients),
                    'Excipient_Count': len(excipients)
                })
    
    if not ibuprofen_forms:
        print("No ibuprofen formulations found in the dataset")
        return
    
    # Create a DataFrame for ibuprofen forms
    ibu_df = pd.DataFrame(ibuprofen_forms)
    print(f"Found {len(ibu_df)} ibuprofen formulations across {len(set(ibu_df['API']))} variants")
    
    # Create bar chart comparing ibuprofen variants (without title)
    plt.figure(figsize=(12, 6))
    sns.countplot(x='API', data=ibu_df, palette='viridis')
    plt.xlabel('Ibuprofen Variant')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('ibuprofen_variants.png', dpi=600)
    plt.close()
    
    # Create boxplot of excipient counts by ibuprofen variant (without title)
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='API', y='Excipient_Count', data=ibu_df, palette='viridis')
    plt.xlabel('Ibuprofen Variant')
    plt.ylabel('Number of Excipients')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('ibuprofen_excipient_counts.png', dpi=600)
    plt.close()
    
    # Save detailed ibuprofen data
    ibu_df.to_csv('ibuprofen_formulations.csv', index=False)
    print("Created specialized ibuprofen analysis with acid form explicitly labeled")

# Simple test if run directly
if __name__ == "__main__":
    print("API analysis module loaded successfully!")
    print("This module provides functions for analyzing and visualizing API data")
    print("To run a complete analysis, execute the main.py script")
