
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

# Set matplotlib parameters for better visualization
plt.rcParams['savefig.dpi'] = 600  # Default DPI for all figures
plt.rcParams['figure.dpi'] = 600  # Screen display DPI
plt.rcParams['font.size'] = 14  # Default font size
plt.rcParams['axes.titlesize'] = 18  # Title font size (though we'll remove titles)
plt.rcParams['axes.labelsize'] = 14  # Axis label font size
plt.rcParams['xtick.labelsize'] = 14  # X-axis tick label size
plt.rcParams['ytick.labelsize'] = 14  # Y-axis tick label size

def analyze_ibuprofen_excipient_cooccurrence(file_path):
    """
    Create heatmaps showing co-occurrence counts between ibuprofen variants and 
    functional excipients, with specific focus on surfactants/solubilizers and pH adjusters.
    """
    print(f"Loading data from {file_path}...")
    
    # Load the data
    df = pd.read_excel(file_path)
    print(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Identify the API column
    api_col = "API"
    if api_col not in df.columns:
        for col in df.columns:
            if col.lower() == "api":
                api_col = col
                break
    
    # Print a sample of API values to debug
    print("\nSample API values in the dataset:")
    api_sample = df[api_col].dropna().unique()[:10]
    for api in api_sample:
        print(f"  - {api}")
    
    # Define the ibuprofen variants we're looking for with updated display names
    # IMPORTANT: "Ibuprofen" should be interpreted as "Ibuprofen (acid)"
    variant_mapping = {
        'ibuprofen': 'Ibuprofen (acid)',
        'ibuprofen acid': 'Ibuprofen (acid)',
        'ibuprofen lysine': 'Ibuprofen Lysine',
        'sodium ibuprofen dihydrate': 'Sodium Ibuprofen Dihydrate',
        'dexibuprofen': 'Dexibrofen (S(+) Ibuprofen)'
    }
    
    # Find all rows containing ibuprofen variants
    variant_masks = {}
    variant_dfs = {}
    
    # Check exact and partial matches for all variants
    for search_term, display_name in variant_mapping.items():
        # Try exact match first
        mask = df[api_col].astype(str).str.lower() == search_term.lower()
        # If no exact matches, try contains
        if mask.sum() == 0:
            mask = df[api_col].astype(str).str.lower().str.contains(search_term.lower(), regex=False, na=False)
        
        if mask.sum() > 0:
            if display_name not in variant_masks:
                variant_masks[display_name] = mask
                variant_dfs[display_name] = df[mask]
            else:
                # Combine with existing mask if we already have this display name
                variant_masks[display_name] |= mask
                variant_dfs[display_name] = df[variant_masks[display_name]]
    
    # If we still don't find enough matches, look for any ibuprofen
    if not variant_masks or len(variant_masks) < 2:
        print("Looking for any ibuprofen entries...")
        ibu_mask = df[api_col].astype(str).str.contains('ibuprofen', case=False, na=False)
        
        if ibu_mask.sum() > 0:
            # Analyze unique values to see what variants might be present
            ibu_values = df[ibu_mask][api_col].unique()
            print(f"Found {len(ibu_values)} unique API values containing 'ibuprofen':")
            for val in ibu_values:
                print(f"  - {val}")
            
            # Try to match each to a known variant or categorize as "Ibuprofen (acid)" if just "Ibuprofen"
            for val in ibu_values:
                val_lower = str(val).lower()
                assigned = False
                
                # Check if it's already assigned to a variant
                already_assigned = False
                for existing_mask in variant_masks.values():
                    if df[existing_mask & (df[api_col] == val)].shape[0] > 0:
                        already_assigned = True
                        break
                
                if already_assigned:
                    continue
                
                # Try to match to a specific variant
                if 'acid' in val_lower:
                    display_name = 'Ibuprofen (acid)'
                    assigned = True
                elif 'lysine' in val_lower:
                    display_name = 'Ibuprofen Lysine'
                    assigned = True
                elif 'sodium' in val_lower or 'dihydrate' in val_lower:
                    display_name = 'Sodium Ibuprofen Dihydrate'
                    assigned = True
                elif 'dex' in val_lower:
                    display_name = 'Dexibrofen (S(+) Ibuprofen)'
                    assigned = True
                elif val_lower == 'ibuprofen' or val_lower.strip() == 'ibuprofen':
                    display_name = 'Ibuprofen (acid)'  # Treat plain "Ibuprofen" as "Ibuprofen (acid)"
                    assigned = True
                
                if assigned:
                    mask = df[api_col] == val
                    if display_name not in variant_masks:
                        variant_masks[display_name] = mask
                        variant_dfs[display_name] = df[mask]
                    else:
                        variant_masks[display_name] |= mask
                        variant_dfs[display_name] = df[variant_masks[display_name]]
    
    # Check if we found ibuprofen acid (either explicitly or as plain "Ibuprofen")
    ibu_acid_found = False
    for display_name in variant_masks.keys():
        if display_name == 'Ibuprofen (acid)':
            ibu_acid_found = True
            break
    
    # If we didn't find ibuprofen acid explicitly, look for plain "Ibuprofen"
    if not ibu_acid_found:
        plain_ibu_mask = df[api_col].astype(str).str.lower() == 'ibuprofen'
        if plain_ibu_mask.sum() > 0:
            print("Found plain 'Ibuprofen' entries, treating as 'Ibuprofen (acid)'")
            variant_masks['Ibuprofen (acid)'] = plain_ibu_mask
            variant_dfs['Ibuprofen (acid)'] = df[plain_ibu_mask]
    
    # Print found variants
    print("\nIbuprofen variants found in dataset:")
    for variant, df_subset in variant_dfs.items():
        print(f"  - {variant}: {len(df_subset)} formulations")
    
    # Set target variants to be the ones we actually found, in a consistent order
    target_variants = ['Ibuprofen (acid)', 'Ibuprofen Lysine', 'Sodium Ibuprofen Dihydrate', 'Dexibrofen (S(+) Ibuprofen)']
    target_variants = [v for v in target_variants if v in variant_dfs]
    
    # Add any other variants we might have found
    for v in variant_dfs.keys():
        if v not in target_variants:
            target_variants.append(v)
    
    print(f"\nAnalyzing {len(target_variants)} ibuprofen variants: {', '.join(target_variants)}")
    
    # Identify the functional excipient columns (including numbered ones)
    surfactant_cols = []
    ph_adjuster_cols = []
    
    for col in df.columns:
        col_str = str(col).lower()
        # Match surfactant/solubilizer columns with optional numbering
        if re.search(r'surfactant|solubilizer', col_str):
            surfactant_cols.append(col)
        # Match pH-adjuster columns with optional numbering
        elif re.search(r'ph.?adj', col_str):
            ph_adjuster_cols.append(col)
    
    print("\nIdentified functional excipient columns:")
    print(f"  Surfactant/Solubilizer columns ({len(surfactant_cols)}): {surfactant_cols}")
    print(f"  pH Adjuster columns ({len(ph_adjuster_cols)}): {ph_adjuster_cols}")
    
    # Function to extract all unique excipients from specific columns
    def get_unique_excipients(column_list):
        excipients = set()
        for col in column_list:
            # Convert to string and handle NaN values
            values = df[col].fillna('').astype(str)
            # Filter out empty strings and whitespace-only strings
            values = [v.strip() for v in values if v.strip() and v.lower() != 'nan']
            excipients.update(values)
        return sorted(list(excipients))
    
    # Get all unique excipients by category
    surfactants = get_unique_excipients(surfactant_cols)
    ph_adjusters = get_unique_excipients(ph_adjuster_cols)
    
    print(f"\nFound {len(surfactants)} unique surfactants/solubilizers")
    print(f"Found {len(ph_adjusters)} unique pH adjusters")
    
    # Print the surfactants for debugging
    print("\nSurfactants/solubilizers found:")
    for s in surfactants:
        print(f"  - {s}")
    
    # Print the pH adjusters for debugging
    print("\npH adjusters found:")
    for p in ph_adjusters:
        print(f"  - {p}")
    
    # Create co-occurrence matrices for each excipient category
    def create_cooccurrence_matrix(excipients, columns):
        # Initialize matrix with zeros
        matrix = pd.DataFrame(0, index=excipients, columns=target_variants)
        
        # Fill in co-occurrence counts
        for variant in target_variants:
            # Handling variants without newline characters now
            lookup_variant = variant
            for orig_variant, df_subset in variant_dfs.items():
                if orig_variant == lookup_variant:
                    # For each excipient column in this category
                    for col in columns:
                        if col in df_subset.columns:
                            # Count occurrences of each excipient with this variant
                            for excipient in excipients:
                                # Convert column to string, handle NaN, and do case-insensitive comparison
                                values = df_subset[col].fillna('').astype(str)
                                # Check for exact matches (case-insensitive)
                                count = sum(values.str.lower() == excipient.lower())
                                matrix.loc[excipient, variant] += count
        
        return matrix
    
    # Create co-occurrence matrices
    surfactant_matrix = create_cooccurrence_matrix(surfactants, surfactant_cols)
    ph_adjuster_matrix = create_cooccurrence_matrix(ph_adjusters, ph_adjuster_cols)
    
    # Create output directory
    output_dir = "ibuprofen_analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # Function to create and save a heatmap with improved excipient ordering
    def create_heatmap(matrix, title, filename):
        # Sort matrix by total counts (summing across variants)
        matrix['Total'] = matrix.sum(axis=1)
        sorted_matrix = matrix.sort_values('Total', ascending=False)
        sorted_matrix = sorted_matrix.drop('Total', axis=1)
        
        # Filter out rows with all zeros
        non_zero_mask = sorted_matrix.sum(axis=1) > 0
        filtered_matrix = sorted_matrix[non_zero_mask]
        
        if len(filtered_matrix) == 0:
            print(f"Warning: No non-zero entries found for {title}")
            return
            
        # If we have many excipients, focus on the top ones
        if len(filtered_matrix) > 20:
            filtered_matrix = filtered_matrix.head(20)
        
        # Improved ordering for related excipients
        if 'surfactant' in filename.lower():
            # Group related surfactants/solubilizers
            
            # Get indices list to reorder
            indices = list(filtered_matrix.index)
            
            # Define groups to keep together (in preferred order within each group)
            polysorbate_group = [idx for idx in indices if 'polysorbate' in idx.lower()]
            lecithin_group = [idx for idx in indices if 'lecithin' in idx.lower()]
            glyceride_group = [idx for idx in indices if any(term in idx.lower() for term in ['glyceride', 'triglyceride'])]
            
            # Remove these groups from original indices
            for idx in polysorbate_group + lecithin_group + glyceride_group:
                if idx in indices:
                    indices.remove(idx)
                    
            # Sort the groups internally by total counts
            polysorbate_group.sort(key=lambda x: filtered_matrix.loc[x].sum(), reverse=True)
            lecithin_group.sort(key=lambda x: filtered_matrix.loc[x].sum(), reverse=True)
            glyceride_group.sort(key=lambda x: filtered_matrix.loc[x].sum(), reverse=True)
            
            # Create a new ordered list with groups kept together
            # The logic here is to insert each group at a reasonable position based on their highest count member
            new_order = []
            
            if polysorbate_group:
                highest_poly = max(polysorbate_group, key=lambda x: filtered_matrix.loc[x].sum())
                for i, idx in enumerate(indices):
                    if filtered_matrix.loc[idx].sum() < filtered_matrix.loc[highest_poly].sum():
                        new_order.extend(indices[:i])
                        new_order.extend(polysorbate_group)
                        new_order.extend(indices[i:])
                        break
                else:
                    new_order = indices + polysorbate_group
            else:
                new_order = indices.copy()
                
            if lecithin_group:
                indices = new_order.copy()
                new_order = []
                highest_lec = max(lecithin_group, key=lambda x: filtered_matrix.loc[x].sum())
                for i, idx in enumerate(indices):
                    if filtered_matrix.loc[idx].sum() < filtered_matrix.loc[highest_lec].sum():
                        new_order.extend(indices[:i])
                        new_order.extend(lecithin_group)
                        new_order.extend(indices[i:])
                        break
                else:
                    new_order = indices + lecithin_group
            
            if glyceride_group:
                indices = new_order.copy()
                new_order = []
                highest_glyc = max(glyceride_group, key=lambda x: filtered_matrix.loc[x].sum())
                for i, idx in enumerate(indices):
                    if filtered_matrix.loc[idx].sum() < filtered_matrix.loc[highest_glyc].sum():
                        new_order.extend(indices[:i])
                        new_order.extend(glyceride_group)
                        new_order.extend(indices[i:])
                        break
                else:
                    new_order = indices + glyceride_group
            
            # Apply the new ordering
            filtered_matrix = filtered_matrix.loc[new_order]
        
        # Create figure (size scales with number of excipients)
        # Increase figure width to accommodate longer x-axis labels
        plt.figure(figsize=(14, max(8, len(filtered_matrix) * 0.4)))  # Increased width for longer variant names
        
        # Create heatmap with adjusted font sizes
        ax = sns.heatmap(filtered_matrix, annot=True, fmt="d", cmap="YlGnBu", linewidths=0.5,
                        annot_kws={'size': 14}, cbar_kws={'label': 'Co-occurrence Count'})
        
        plt.xlabel('Ibuprofen Variant', fontsize=16)
        plt.ylabel('Excipient', fontsize=16)
        
        # Adjust x-axis labels to prevent overlap with the longer variant names
        plt.xticks(rotation=15, fontsize=14)  # Slight rotation to prevent overlap
        
        # Adjust y-axis label font size
        plt.yticks(fontsize=14)
        
        # Adjust layout to prevent cutting off labels
        plt.tight_layout()
        
        # Save the plot
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=600)
        plt.close()
        print(f"Saved heatmap to {filepath}")
        
        # Save the data
        csv_path = os.path.join(output_dir, filename.replace('.png', '.csv'))
        matrix.to_csv(csv_path)
        print(f"Saved co-occurrence data to {csv_path}")
        
        return filtered_matrix
    
    # Create heatmaps for each excipient category
    surfactant_filtered = create_heatmap(surfactant_matrix, 'Surfactant/Solubilizer Co-occurrence with Ibuprofen Variants', 
                  'surfactant_cooccurrence.png')
    
    ph_adjuster_filtered = create_heatmap(ph_adjuster_matrix, 'pH Adjuster Co-occurrence with Ibuprofen Variants',
                  'ph_adjuster_cooccurrence.png')
    
    # Look for sodium lauryl sulfate in our surfactants list
    sls_excipients = []
    for surfactant in surfactants:
        if any(term in surfactant.lower() for term in ['sodium lauryl sulfate', 'lauryl sulfate', 'sls']):
            sls_excipients.append(surfactant)
    
    # If we found SLS, create a focused visualization
    if sls_excipients:
        print(f"\nFound sodium lauryl sulfate excipients: {sls_excipients}")
        
        # Create a matrix just for SLS
        sls_matrix = surfactant_matrix.loc[sls_excipients]
        
        # Create a heatmap for SLS
        create_heatmap(sls_matrix, 'Sodium Lauryl Sulfate Usage Across Ibuprofen Variants',
                      'sodium_lauryl_sulfate_comparison.png')
        
        # Create a bar chart for each SLS variant
        for sls in sls_excipients:
            plt.figure(figsize=(14, 6))  # Wider figure for longer variant names
            counts = surfactant_matrix.loc[sls]
            bars = plt.bar(counts.index, counts.values, color='skyblue')
            
            plt.xlabel('Ibuprofen Variant', fontsize=14)
            plt.ylabel('Co-occurrence Count', fontsize=14)
            plt.xticks(fontsize=14, rotation=15)  # Slight rotation for longer labels
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        str(int(height)), ha='center', va='bottom', fontsize=14)
            
            plt.tight_layout()
            safe_filename = sls.replace(' ', '_').replace('/', '_').lower()
            plt.savefig(os.path.join(output_dir, f'{safe_filename}_bar.png'), dpi=600)
            plt.close()
            print(f"Saved bar chart to {os.path.join(output_dir, f'{safe_filename}_bar.png')}")
    else:
        print("\nNo sodium lauryl sulfate or similar excipients found in the dataset.")
    
    # Create a combined matrix for selected key excipients from both categories
    try:
        # Get the top excipients from each category if we have them
        top_surfactants = []
        top_ph_adjusters = []
        
        if surfactant_filtered is not None and len(surfactant_filtered) > 0:
            top_surfactants = surfactant_filtered.index.tolist()[:5]  # Top 5
        
        if ph_adjuster_filtered is not None and len(ph_adjuster_filtered) > 0:
            top_ph_adjusters = ph_adjuster_filtered.index.tolist()[:5]  # Top 5
        
        # Make sure SLS is included if it exists
        for sls in sls_excipients:
            if sls not in top_surfactants:
                top_surfactants.append(sls)
        
        # Create list of key excipients
        key_excipients = [('Surfactant', s) for s in top_surfactants] + \
                         [('pH Adjuster', p) for p in top_ph_adjusters]
        
        # If we have key excipients, create a combined visualization
        if key_excipients:
            # Limit to a reasonable number to avoid overcrowding
            if len(key_excipients) > 15:
                key_excipients = key_excipients[:15]
            
            # Create combined matrix
            excipient_labels = [f"{category}: {excipient}" for category, excipient in key_excipients]
            combined_matrix = pd.DataFrame(0, index=excipient_labels, columns=target_variants)
            
            # Fill in the matrix with values from the respective category matrices
            for i, (category, excipient) in enumerate(key_excipients):
                row_label = excipient_labels[i]
                if category == 'Surfactant' and excipient in surfactant_matrix.index:
                    for variant in target_variants:
                        if variant in surfactant_matrix.columns:
                            combined_matrix.loc[row_label, variant] = surfactant_matrix.loc[excipient, variant]
                elif category == 'pH Adjuster' and excipient in ph_adjuster_matrix.index:
                    for variant in target_variants:
                        if variant in ph_adjuster_matrix.columns:
                            combined_matrix.loc[row_label, variant] = ph_adjuster_matrix.loc[excipient, variant]
            
            # Create the heatmap
            create_heatmap(combined_matrix, 'Key Functional Excipients Co-occurrence with Ibuprofen Variants',
                        'key_excipients_cooccurrence.png')
    except Exception as e:
        print(f"Error creating combined matrix: {str(e)}")
    
    # Create a special comparative visualization for surfactants vs pH adjusters
    try:
        # Count how many of each category are used with each variant
        category_counts = pd.DataFrame(index=['Surfactants', 'pH Adjusters'], columns=target_variants)
        
        for variant in target_variants:
            if variant in surfactant_matrix.columns:
                # Count distinct surfactants used with this variant
                surf_count = sum(surfactant_matrix[variant] > 0)
                category_counts.loc['Surfactants', variant] = surf_count
            
            if variant in ph_adjuster_matrix.columns:
                # Count distinct pH adjusters used with this variant
                ph_count = sum(ph_adjuster_matrix[variant] > 0)
                category_counts.loc['pH Adjusters', variant] = ph_count
        
        # Create a grouped bar chart
        plt.figure(figsize=(16, 6))  # Wider figure for longer variant names
        category_counts.T.plot(kind='bar', figsize=(16, 6))
        
        plt.xlabel('Ibuprofen Variant', fontsize=14)
        plt.ylabel('Count of Unique Excipients', fontsize=14)
        plt.legend(title='Excipient Category', fontsize=12)
        plt.xticks(rotation=15, fontsize=14)  # Slight rotation for longer labels
        plt.tight_layout()
        
        # Save the chart
        count_path = os.path.join(output_dir, 'category_count_comparison.png')
        plt.savefig(count_path, dpi=600)
        plt.close()
        print(f"Saved category count comparison to {count_path}")
        
    except Exception as e:
        print(f"Error creating category comparison: {str(e)}")
    
    print("\nAnalysis complete! Co-occurrence heatmaps have been created in the '{output_dir}' directory.")

if __name__ == "__main__":
    # Try to find the Excel file
    file_path = "Dylan_data_excipient.xlsx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        # Look for files with similar names
        excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and ('dylan' in f.lower() or 'excip' in f.lower())]
        
        if excel_files:
            file_path = excel_files[0]
            print(f"Using alternative file: {file_path}")
        else:
            file_path = input("Please enter the path to your Excel file: ")
    
    analyze_ibuprofen_excipient_cooccurrence(file_path)
