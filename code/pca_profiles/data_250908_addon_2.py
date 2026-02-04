
# Import all functions from the first file
from ibuprofen_functions import *

def main():
    """Main function to run selected visualizations and analysis"""
    print("===== IBUPROFEN FORMULATION ANALYSIS =====")
    
    # Load and preprocess data
    df = load_and_preprocess_data('matched_pk_data_2.xlsx')
    
    # Define parameters to analyze
    pk_columns = ['tmax', 'Cmax_normalized', 'AUC_normalized', 't1_2']
    
    # Check for amorphous samples before filtering
    amorphous_before = df[df['Formulation Principle'] == 'Amorphous ibuprofen']
    print(f"\nAmorphous samples before filtering: {len(amorphous_before)}")
    if not amorphous_before.empty:
        print("Amorphous samples details:")
        relevant_columns = ['tmax', 'cmax', 'auc', 't1_2', 'dose', 'Cmax_normalized', 'AUC_normalized', 'Formulation Type']
        print(amorphous_before[relevant_columns])
    
    # Original filtering logic (modified to exclude Extended Release)
    df_filtered_orig = df[df['tmax'].notna() & 
                        ((df['Cmax_normalized'].notna()) | 
                         (df['AUC_normalized'].notna()) | 
                         (df['t1_2'].notna()))]
    
    # Filter out 'Unknown', 'Excluded', and 'Extended Release' formulation types
    df_filtered_orig = df_filtered_orig[~df_filtered_orig['Formulation Type'].isin(['Unknown', 'Excluded', 'Extended Release'])]
    
    # NEW: Check if the original filtering removes amorphous samples
    amorphous_after_orig = df_filtered_orig[df_filtered_orig['Formulation Principle'] == 'Amorphous ibuprofen']
    print(f"\nAmorphous samples after initial filtering: {len(amorphous_after_orig)}")
    
    # MODIFIED: Use the modified filtering logic to preserve amorphous samples
    # First, create a filter mask that would exclude amorphous samples or Extended Release
    exclude_mask = (df['tmax'].isna() | 
                   (~df['Cmax_normalized'].notna() & 
                    ~df['AUC_normalized'].notna() & 
                    ~df['t1_2'].notna()) |
                   df['Formulation Type'].isin(['Unknown', 'Excluded', 'Extended Release']))  # Added 'Extended Release'
    
    # Then, modify the mask to keep amorphous samples regardless
    amorphous_mask = df['Formulation Principle'] == 'Amorphous ibuprofen'
    final_mask = (~exclude_mask) | amorphous_mask
    
    # Apply the modified filter
    df_filtered = df[final_mask]
    
    # Make sure Extended Release is excluded except for amorphous samples
    extended_release_mask = (df_filtered['Formulation Type'] == 'Extended Release') & (df_filtered['Formulation Principle'] != 'Amorphous ibuprofen')
    if extended_release_mask.any():
        print(f"Removing {extended_release_mask.sum()} Extended Release samples (keeping any amorphous ones)")
        df_filtered = df_filtered[~extended_release_mask]
    
    # Check if we've preserved amorphous samples
    amorphous_after = df_filtered[df_filtered['Formulation Principle'] == 'Amorphous ibuprofen']
    print(f"Amorphous samples after modified filtering: {len(amorphous_after)}")
    
    # NEW: Impute missing values for amorphous samples if needed
    if not amorphous_after.empty:
        for col in pk_columns:
            missing_mask = (df_filtered['Formulation Principle'] == 'Amorphous ibuprofen') & df_filtered[col].isna()
            if missing_mask.any():
                # Determine the formulation type to use for imputation
                if amorphous_after['Formulation Type'].iloc[0] in ['Rapid', 'Standard']:
                    form_type = amorphous_after['Formulation Type'].iloc[0]
                else:
                    form_type = 'Standard'  # Default to Standard if unknown
                
                # Calculate median from that formulation type (excluding amorphous)
                median_mask = (df_filtered['Formulation Type'] == form_type) & (df_filtered['Formulation Principle'] != 'Amorphous ibuprofen')
                if median_mask.any():
                    median_val = df_filtered.loc[median_mask, col].median()
                    df_filtered.loc[missing_mask, col] = median_val
                    print(f"Imputed missing {col} for amorphous sample with median {median_val} from {form_type} formulation")
    
    print(f"\nDataset after filtering: {df_filtered.shape[0]} samples")
    print("Formulation Type distribution:")
    print(df_filtered['Formulation Type'].value_counts())
    print("\nFormulation Principle distribution:")
    print(df_filtered['Formulation Principle'].value_counts())
    print("\nDosage Form distribution:")
    print(df_filtered['Dosage Form'].value_counts())
    
    # Create pair plots by all three classification methods
    create_pair_plots(df_filtered, pk_columns, color_by='Formulation Type')
    create_pair_plots(df_filtered, pk_columns, color_by='Formulation Principle')
    create_pair_plots(df_filtered, pk_columns, color_by='Dosage Form')
    
    # Create correlation heatmap
    create_correlation_heatmap(df_filtered, pk_columns)
    
    # For PCA, we need to ensure all required columns have values
    # This is particularly important for amorphous samples that might have missing values
    df_pca_complete = df_filtered.copy()
    
    # Impute any remaining missing values for amorphous samples before PCA
    for col in pk_columns:
        # Check for missing values in amorphous samples
        amorphous_missing = (df_pca_complete['Formulation Principle'] == 'Amorphous ibuprofen') & df_pca_complete[col].isna()
        
        if amorphous_missing.any():
            # Get the formulation type of the amorphous sample
            if 'Formulation Type' in df_pca_complete.columns:
                form_type = df_pca_complete.loc[amorphous_missing, 'Formulation Type'].iloc[0]
                if form_type not in ['Rapid', 'Standard']:
                    form_type = 'Standard'  # Default if not recognized
            else:
                form_type = 'Standard'  # Default if column not present
            
            # Calculate median from that formulation type for imputation
            median_mask = (df_pca_complete['Formulation Type'] == form_type) & (df_pca_complete['Formulation Principle'] != 'Amorphous ibuprofen')
            if median_mask.any() and df_pca_complete.loc[median_mask, col].notna().any():
                median_val = df_pca_complete.loc[median_mask, col].median()
                df_pca_complete.loc[amorphous_missing, col] = median_val
                print(f"Imputed missing {col} for amorphous sample with median {median_val} from {form_type} formulation")
            else:
                # If no samples of this formulation type, use overall median
                overall_median = df_pca_complete[col].median()
                df_pca_complete.loc[amorphous_missing, col] = overall_median
                print(f"Imputed missing {col} for amorphous sample with overall median {overall_median}")
    
    # Create a version for PCA with no missing values
    df_pca = df_pca_complete[pk_columns].dropna()
    df_pca_with_type = df_pca_complete.loc[df_pca.index]
    
    # Double-check if amorphous samples are retained after dropping NaNs
    amorphous_for_pca = df_pca_with_type[df_pca_with_type['Formulation Principle'] == 'Amorphous ibuprofen']
    print(f"\nAmorphous samples for PCA analysis: {len(amorphous_for_pca)}")
    
    if len(amorphous_for_pca) == 0 and len(amorphous_after) > 0:
        print("WARNING: Amorphous samples were lost during preparation for PCA.")
        print("This likely means they still had missing values in required columns.")
        
        # Let's force keep amorphous samples by filling all missing values
        # First, identify rows with amorphous ibuprofen
        amorphous_indices = df_pca_complete[df_pca_complete['Formulation Principle'] == 'Amorphous ibuprofen'].index
        
        if len(amorphous_indices) > 0:
            print("Forcing retention of amorphous samples by imputing any remaining missing values...")
            
            # For each amorphous sample
            for idx in amorphous_indices:
                # Check if it has any missing values in required columns
                row = df_pca_complete.loc[idx, pk_columns]
                if row.isna().any():
                    # Fill missing values with median from appropriate formulation type
                    form_type = df_pca_complete.loc[idx, 'Formulation Type']
                    
                    for col in pk_columns:
                        if pd.isna(row[col]):
                            # Try to get median from same formulation type
                            median_mask = (df_pca_complete['Formulation Type'] == form_type) & df_pca_complete[col].notna()
                            if median_mask.any():
                                median_val = df_pca_complete.loc[median_mask, col].median()
                            else:
                                # Fall back to overall median
                                median_val = df_pca_complete[col].median()
                            
                            # Apply imputation
                            df_pca_complete.loc[idx, col] = median_val
                            print(f"Forced imputation of {col} with value {median_val} for amorphous sample {idx}")
            
            # Recreate PCA dataset with imputed values
            df_pca = df_pca_complete[pk_columns].dropna()
            df_pca_with_type = df_pca_complete.loc[df_pca.index]
            
            # Verify amorphous samples are now included
            amorphous_for_pca = df_pca_with_type[df_pca_with_type['Formulation Principle'] == 'Amorphous ibuprofen']
            print(f"Amorphous samples for PCA analysis after forced imputation: {len(amorphous_for_pca)}")
    
    print(f"\nDataset after dropping NaN values for PCA: {df_pca.shape[0]} samples")
    print("Formulation Type distribution for PCA analysis:")
    print(df_pca_with_type['Formulation Type'].value_counts())
    print("\nFormulation Principle distribution for PCA analysis:")
    print(df_pca_with_type['Formulation Principle'].value_counts())
    print("\nDosage Form distribution for PCA analysis:")
    print(df_pca_with_type['Dosage Form'].value_counts())
    
    # Perform PCA analysis with all three classification methods
    pca_type, pca_result_type, explained_variance_ratio = perform_pca_analysis(
        df_pca_with_type, pk_columns, color_by='Formulation Type')
    
    pca_principle, pca_result_principle, _ = perform_pca_analysis(
        df_pca_with_type, pk_columns, color_by='Formulation Principle')
    
    pca_dosage, pca_result_dosage, _ = perform_pca_analysis(
        df_pca_with_type, pk_columns, color_by='Dosage Form')
    
    print("\n===== ANALYSIS COMPLETE =====")
    print("All visualizations saved as high-resolution (600 DPI) PNG files")
    
    return pca_type, pca_result_type, explained_variance_ratio

if __name__ == "__main__":
    pca, pca_result, explained_variance_ratio = main()
