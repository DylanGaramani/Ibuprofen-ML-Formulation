
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import custom modules for consistent excipient handling
import excipient_sorting
from excipient_sorting import standardize_excipient_names, get_excipient_sort_key
import data_processing

def analyze_formulation_compositions(df, excipient_data):
    """
    Analyze formulation compositions and generate visualizations
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
    excipient_data : dict
        Dictionary containing excipient frequency data organized by type
    
    Returns:
    --------
    None, but saves visualization files
    """
    # 1. Count formulations by dosage form
    if 'Form' in df.columns:
        dosage_forms = df['Form'].value_counts()
        print("\nDosage form distribution:")
        print(dosage_forms)
        
        # Create bar chart of dosage forms with increased DPI (without title)
        plt.figure(figsize=(12, 6))
        dosage_forms.plot(kind='bar', color='skyblue')
        plt.xlabel('Dosage Form')
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('dosage_form_distribution.png', dpi=600)
        plt.close()
    
    # 2. Visualize excipient usage by excipient type
    for excip_type, counts in excipient_data.items():
        if not counts.empty and len(counts) > 0:
            # Ensure consistent sorting using the excipient_sorting module
            counts_plot = excipient_sorting.sort_excipients(counts)
            
            plt.figure(figsize=(14, max(6, len(counts_plot) * 0.4)))  # Dynamic figure height
            counts_plot.plot(kind='bar', color='lightgreen')
            
            plt.xlabel(excip_type)
            plt.ylabel('Frequency')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f'{excip_type.lower().replace(" ", "_").replace("/", "_")}_frequency.png', dpi=600)
            plt.close()
            
            print(f"Created frequency chart for {excip_type}s")
    
    # 3. Analyze relationship between dosage form and excipients
    create_dosage_form_heatmaps(df, excipient_data)
    
    print("Formulation composition analysis complete")

def create_dosage_form_heatmaps(df, excipient_data):
    """
    Create heatmaps showing excipient usage by dosage form
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
    excipient_data : dict
        Dictionary containing excipient frequency data organized by type
    
    Returns:
    --------
    None, but saves visualization files
    """
    if 'Form' not in df.columns:
        print("No 'Form' column found, skipping dosage form heatmaps")
        return
    
    # Define critical excipients by category - maintained for backward compatibility
    critical_excipients_by_type = {
        'Coating': ["Gelatin", "Hypromellose", "Titanium dioxide"],
        'Bulking agent': ["Microcrystalline cellulose", "Lactose monohydrate", "Isomalt"],
        'Lubricant': ["Magnesium stearate"],
        'Surfactant/solubilizer': ["Sodium lauryl sulfate", "Polysorbate 80"],
        'Super-disintegrant': ["Croscarmellose sodium", "Crospovidone"],
        'Glidant': ["Colloidal anhydrous silica", "Talc"]
    }
    
    # For each excipient type, analyze usage by dosage form
    for excip_type in excipient_data.keys():
        # Skip if no excipients for this type
        if excipient_data[excip_type].empty:
            print(f"No {excip_type}s found, skipping heatmap")
            continue
            
        # Identify relevant columns based on excipient type
        excipient_columns = data_processing.identify_excipient_columns_by_type(df, excip_type)
        
        # Skip if no related columns
        if not excipient_columns:
            print(f"No columns found for {excip_type}, skipping heatmap")
            continue
        
        # Create a count matrix: rows=excipients, columns=dosage forms
        form_excipient_matrix = {}
        
        # Iterate through each dosage form
        for form in df['Form'].unique():
            if pd.isna(form):
                continue
            
            # Filter rows for this dosage form
            form_df = df[df['Form'] == form]
            
            # Count excipients used in this dosage form
            excipient_counts = {}
            for _, row in form_df.iterrows():
                for col in excipient_columns:
                    if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                        # Apply category-specific filtering
                        if data_processing.should_include_excipient(row[col], excip_type, form):
                            # Use standardized excipient name
                            excip = standardize_excipient_names(row[col])
                            if excip:
                                if excip in excipient_counts:
                                    excipient_counts[excip] += 1
                                else:
                                    excipient_counts[excip] = 1
            
            form_excipient_matrix[form] = excipient_counts
        
        # Convert to dataframe
        if form_excipient_matrix:
            form_excip_df = pd.DataFrame(form_excipient_matrix).fillna(0)
            
            # Print all excipients found for debugging
            print(f"\nAll {excip_type}s found for heatmap:", form_excip_df.index.tolist())
            
            # Include critical excipients specific to this category
            include_critical_excipients(form_excip_df, excip_type, critical_excipients_by_type, excipient_data)
            
            # Sort excipients using our custom sorting function
            form_excip_df = excipient_sorting.sort_excipient_dataframe(form_excip_df)
            
            # Create heatmap with increased DPI (without title)
            plt.figure(figsize=(14, max(10, len(form_excip_df) * 0.5)))  # Dynamic size
            sns.heatmap(form_excip_df, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5)
            plt.ylabel(excip_type)
            plt.xlabel('Dosage Form')
            plt.tight_layout()
            plt.savefig(f'{excip_type.lower().replace(" ", "_").replace("/", "_")}_by_form_complete.png', dpi=600)
            plt.close()
            
            # Also save the data for this heatmap
            form_excip_df.to_csv(f'{excip_type.lower().replace(" ", "_").replace("/", "_")}_by_form_complete_data.csv')
            
            print(f"Created heatmap for {excip_type}s by dosage form")

def include_critical_excipients(dataframe, excip_type, critical_excipients_by_type, excipient_data):
    """
    Ensure critical excipients are included in the visualization if present in the data
    
    Parameters:
    -----------
    dataframe : pandas.DataFrame
        The dataframe containing excipient data
    excip_type : str
        The excipient type category being analyzed
    critical_excipients_by_type : dict
        Dictionary mapping excipient types to lists of critical excipients
    excipient_data : dict
        Dictionary containing excipient frequency data organized by type
    
    Returns:
    --------
    None, modifies dataframe in place
    """
    critical_for_this_type = critical_excipients_by_type.get(excip_type, [])
    
    if critical_for_this_type:
        for critical_excip in critical_for_this_type:
            # Check if the critical excipient exists in the original data
            if critical_excip in excipient_data.get(excip_type, pd.Series()).index:
                # If it's not already in the dataframe, add it
                if critical_excip not in dataframe.index:
                    print(f"Adding critical excipient to visualization: {critical_excip}")
                    dataframe.loc[critical_excip] = 0

def analyze_all_dosage_forms(df):
    """
    Create a comprehensive visualization of all excipients across all dosage forms
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
    
    Returns:
    --------
    pandas.DataFrame : Combined dataframe of all excipients by all dosage forms
    """
    print("\nAnalyzing all dosage forms...")
    
    # Identify columns containing excipients using the data_processing module
    excipient_columns = data_processing.identify_excipient_columns(df)
    
    # Get all unique dosage forms
    all_forms = df['Form'].dropna().unique()
    print(f"Found {len(all_forms)} unique dosage forms: {', '.join(map(str, all_forms))}")
    
    # For each dosage form, collect all excipients
    form_excipients = {}
    for form in all_forms:
        form_df = df[df['Form'] == form]
        
        excipients = []
        for _, row in form_df.iterrows():
            for col in excipient_columns:
                if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                    standardized = standardize_excipient_names(row[col])
                    if standardized:
                        excipients.append(standardized)
        
        form_excipients[form] = pd.Series(excipients).value_counts()
    
    # Create a combined dataframe for all dosage forms
    all_excipients = set()
    for excips in form_excipients.values():
        all_excipients.update(excips.index)
    
    combined_df = pd.DataFrame(index=list(all_excipients), columns=all_forms)
    
    for form, excips in form_excipients.items():
        for excip, count in excips.items():
            combined_df.loc[excip, form] = count
    
    # Fill NaN values with 0
    combined_df = combined_df.fillna(0)
    
    # Sort rows using the excipient_sorting module
    combined_df = excipient_sorting.sort_excipient_dataframe(combined_df)
    
    # Save this comprehensive data
    combined_df.to_csv('all_excipients_by_all_forms.csv')
    
    # Create visualization with increased DPI (without title)
    plt.figure(figsize=(max(16, len(all_forms) * 2), max(20, len(all_excipients) * 0.3)))
    sns.heatmap(combined_df, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5)
    plt.ylabel('Excipient')
    plt.xlabel('Dosage Form')
    plt.tight_layout()
    plt.savefig('all_excipients_by_all_forms.png', dpi=600, bbox_inches='tight')
    plt.close()
    
    print("Comprehensive analysis of all excipients by all dosage forms completed")
    return combined_df

def analyze_special_categories(df):
    """
    Create specialized analyses for specific excipient categories
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
    
    Returns:
    --------
    None, but calls specialized analysis functions
    """
    # 1. Analyze colorants
    analyze_colorants(df)
    
    # 2. Analyze coatings
    analyze_coatings(df)
    
    # 3. Analyze soft gel capsules
    analyze_soft_gel_capsules(df)
    
    # 4. Analyze povidone group
    analyze_povidone_group(df)

def analyze_colorants(df):
    """
    Create a focused analysis of colorants across all dosage forms
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
    
    Returns:
    --------
    pandas.DataFrame or None : Colorant pivot table if colorants found
    """
    print("\nCreating specialized analysis for colorants...")
    
    # Identify potential columns containing colorants
    colorant_columns = data_processing.identify_excipient_columns_by_type(df, 'Colorant')
    
    # Extract colorants
    all_colorants = []
    colorant_keywords = ['iron oxide', 'erythrosine', 'color', 'pigment', 'dye', 'lake', 
                         'titanium dioxide', 'yellow', 'red', 'blue', 'quinoline']
    
    for _, row in df.iterrows():
        form = row['Form'] if 'Form' in row and pd.notna(row['Form']) else 'Unknown'
        
        for col in colorant_columns:
            if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                value = str(row[col]).lower()
                if any(keyword in value for keyword in colorant_keywords):
                    std_name = standardize_excipient_names(row[col])
                    if std_name:
                        all_colorants.append({
                            'Colorant': std_name,
                            'Dosage_Form': form
                        })
    
    # Create a DataFrame for colorants
    if all_colorants:
        colorant_df = pd.DataFrame(all_colorants)
        print(f"Found {len(set(colorant_df['Colorant']))} unique colorants across {len(set(colorant_df['Dosage_Form']))} dosage forms")
        
        # Count by dosage form
        colorant_pivot = pd.pivot_table(
            colorant_df, 
            index='Colorant',
            columns='Dosage_Form',
            aggfunc='size',
            fill_value=0
        )
        
        # Sort rows using the excipient_sorting module
        colorant_pivot = excipient_sorting.sort_excipient_dataframe(colorant_pivot)
        
        # Create visualization with increased DPI (without title)
        plt.figure(figsize=(max(14, len(colorant_pivot.columns) * 1.5), 
                          max(10, len(colorant_pivot) * 0.5)))
        sns.heatmap(colorant_pivot, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5)
        plt.ylabel('Colorant')
        plt.xlabel('Dosage Form')
        plt.tight_layout()
        plt.savefig('colorants_by_form.png', dpi=600, bbox_inches='tight')
        plt.close()
        
        # Save the colorant data
        colorant_pivot.to_csv('colorants_by_form_data.csv')
        print("Created specialized colorant analysis")
        return colorant_pivot
    else:
        print("No colorants found in the dataset")
        return None

def analyze_coatings(df):
    """
    Create a focused analysis of coating materials across all dosage forms
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
    
    Returns:
    --------
    pandas.DataFrame or None : Coating pivot table if coatings found
    """
    print("\nCreating specialized analysis for coating materials...")
    
    # Identify coating columns
    coating_columns = [col for col in df.columns if 'coating' in str(col).lower()]
    
    # Extract all coatings
    all_coatings = []
    
    for _, row in df.iterrows():
        form = row['Form'] if 'Form' in row and pd.notna(row['Form']) else 'Unknown'
        
        for col in coating_columns:
            if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                # Apply gelatin filtering for appropriate dosage forms
                if data_processing.should_include_excipient(row[col], 'Coating', form):
                    std_name = standardize_excipient_names(row[col])
                    if std_name:
                        all_coatings.append({
                            'Coating': std_name,
                            'Dosage_Form': form
                        })
    
    # Create a DataFrame for coatings
    if all_coatings:
        coating_df = pd.DataFrame(all_coatings)
        print(f"Found {len(set(coating_df['Coating']))} unique coating materials across {len(set(coating_df['Dosage_Form']))} dosage forms")
        
        # Count by dosage form
        coating_pivot = pd.pivot_table(
            coating_df, 
            index='Coating',
            columns='Dosage_Form',
            aggfunc='size',
            fill_value=0
        )
        
        # Sort rows using the excipient_sorting module
        coating_pivot = excipient_sorting.sort_excipient_dataframe(coating_pivot)
        
        # Create visualization with increased DPI (without title)
        plt.figure(figsize=(max(14, len(coating_pivot.columns) * 1.5), 
                          max(10, len(coating_pivot) * 0.5)))
        sns.heatmap(coating_pivot, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5)
        plt.ylabel('Coating Material')
        plt.xlabel('Dosage Form')
        plt.tight_layout()
        plt.savefig('all_coatings_by_all_forms.png', dpi=600, bbox_inches='tight')
        plt.close()
        
        # Save the coating data
        coating_pivot.to_csv('all_coatings_by_all_forms_data.csv')
        print("Created specialized coating analysis")
        return coating_pivot
    else:
        print("No coating materials found in the dataset")
        return None

def analyze_povidone_group(df):
    """
    Create a focused analysis of povidone, crospovidone, and copovidone across all dosage forms
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
    
    Returns:
    --------
    pandas.DataFrame or None : Povidone pivot table if povidone variants found
    """
    print("\nCreating specialized analysis for povidone group (povidone, crospovidone, copovidone)...")
    
    # Identify columns that might contain povidone variants
    povidone_columns = []
    keywords = ['povidone', 'pvp', 'crospovidone', 'copovidone', 'polyvinylpyrrolidone', 'binder', 'disintegrant']
    
    for col in df.columns:
        col_str = str(col).lower()
        if any(keyword in col_str for keyword in keywords):
            povidone_columns.append(col)
    
    # Extract all povidone variants
    all_povidones = []
    
    for _, row in df.iterrows():
        form = row['Form'] if 'Form' in row and pd.notna(row['Form']) else 'Unknown'
        
        for col in povidone_columns:
            if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                value = str(row[col]).lower()
                if any(keyword in value for keyword in ['povidone', 'pvp', 'crospovidone', 'copovidone', 'polyvinylpyrrolidone']):
                    std_name = standardize_excipient_names(row[col])
                    if std_name:
                        all_povidones.append({
                            'Povidone': std_name,
                            'Dosage_Form': form
                        })
    
    # Create a DataFrame for povidones
    if all_povidones:
        povidone_df = pd.DataFrame(all_povidones)
        print(f"Found {len(set(povidone_df['Povidone']))} unique povidone variants across {len(set(povidone_df['Dosage_Form']))} dosage forms")
        
        # Count by dosage form
        povidone_pivot = pd.pivot_table(
            povidone_df, 
            index='Povidone',
            columns='Dosage_Form',
            aggfunc='size',
            fill_value=0
        )
        
        # Sort rows using the excipient_sorting module
        povidone_pivot = excipient_sorting.sort_excipient_dataframe(povidone_pivot)
        
        # Create visualization with increased DPI (without title)
        plt.figure(figsize=(max(14, len(povidone_pivot.columns) * 1.5), 
                          max(6, len(povidone_pivot) * 0.8)))
        sns.heatmap(povidone_pivot, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5)
        plt.ylabel('Povidone Type')
        plt.xlabel('Dosage Form')
        plt.tight_layout()
        plt.savefig('povidone_variants_by_form.png', dpi=600, bbox_inches='tight')
        plt.close()
        
        # Save the povidone data
        povidone_pivot.to_csv('povidone_variants_by_form_data.csv')
        print("Created specialized povidone group analysis")
        return povidone_pivot
    else:
        print("No povidone variants found in the dataset")
        return None

def analyze_soft_gel_capsules(df):
    """
    Specialized function to analyze soft gel capsule formulations
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The preprocessed formulation data
    
    Returns:
    --------
    pandas.DataFrame or None : Soft gel coating pivot table if applicable
    """
    # Find all soft gel capsule formulations
    soft_gel_df = df[df['Form'].str.contains('gel|capsule', case=False, na=False)]
    
    if len(soft_gel_df) == 0:
        print("No soft gel capsule formulations found in the dataset")
        return None
    
    print(f"\nFound {len(soft_gel_df)} soft gel capsule/gel formulations")
    
    # Extract coating components specifically for soft gel capsules
    coating_columns = [col for col in df.columns if 'coating' in str(col).lower()]
    
    soft_gel_coatings = []
    for _, row in soft_gel_df.iterrows():
        brand = row['Brand'] if 'Brand' in row and pd.notna(row['Brand']) else 'Unknown'
        form = row['Form'] if 'Form' in row and pd.notna(row['Form']) else 'Unknown'
        
        for col in coating_columns:
            if pd.notna(row[col]) and row[col] != '' and row[col] != 'n/a':
                coating = standardize_excipient_names(row[col])
                if coating:
                    soft_gel_coatings.append({
                        'Brand': brand,
                        'Form': form,
                        'Coating': coating
                    })
    
    if soft_gel_coatings:
        # Create DataFrame and save
        coatings_df = pd.DataFrame(soft_gel_coatings)
        print("\nSoft gel capsule/gel coating components:")
        print(coatings_df['Coating'].value_counts())
        
        # Create pivot table if we have enough data
        if len(coatings_df) > 1:
            pivot_df = pd.pivot_table(
                coatings_df,
                index='Coating',
                columns='Form',
                aggfunc='size',
                fill_value=0
            )
            
            # Sort rows using the excipient_sorting module
            pivot_df = excipient_sorting.sort_excipient_dataframe(pivot_df)
            
            # Create visualization with increased DPI (without title)
            plt.figure(figsize=(12, 8))
            sns.heatmap(pivot_df, cmap='YlGnBu', annot=True, fmt='.0f', linewidths=.5)
            plt.ylabel('Coating Component')
            plt.xlabel('Dosage Form')
            plt.tight_layout()
            plt.savefig('soft_gel_coatings.png', dpi=600)
            plt.close()
            
            # Save the data
            pivot_df.to_csv('soft_gel_coatings_data.csv')
            print("Created specialized visualization for soft gel/capsule coatings")
            return pivot_df
        else:
            print("Not enough data for a pivot table visualization of soft gel coatings")
            return None
    else:
        print("No coating components found for soft gel capsule formulations")
        return None

# Main function for testing if run directly
if __name__ == "__main__":
    print("Visualization module loaded successfully!")
    print("This module provides functions for analyzing and visualizing excipient data")
    print("To run a complete analysis, execute the main.py script")
