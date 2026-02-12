
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

# Ensure the current directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our custom modules
import excipient_sorting
import data_processing
from visualization import analyze_formulation_compositions, analyze_all_dosage_forms, analyze_special_categories
from api_analysis import analyze_api_distribution, analyze_api_excipient_relationships

def main():
    """
    Main function to run the entire analysis with proper module integration
    
    This function orchestrates the complete workflow for excipient and API analysis,
    from data loading and preprocessing to visualization generation,
    ensuring consistent application of standardization and sorting
    methodologies across all analytical steps.
    """
    # Set matplotlib parameters for better visualization
    plt.rcParams['savefig.dpi'] = 600  # Default DPI for all figures
    plt.rcParams['figure.dpi'] = 600  # Screen display DPI
    plt.rcParams['font.size'] = 14  # Default font size
    plt.rcParams['axes.titlesize'] = 18  # Title font size
    plt.rcParams['axes.labelsize'] = 14  # Axis label font size
    
    # Set file path
    file_path = "data_excipient.xlsx"
    print(f"Using file: {file_path}")
    
    # Load and preprocess data using data_processing module
    df, excipient_data, excipient_columns = data_processing.load_and_preprocess_data(file_path)
    
    # Verify excipient categorization
    data_processing.verify_excipient_categories(df)
    
    # Create standardization table for excipients
    std_table = data_processing.create_excipient_standardization_table(df, excipient_columns)
    print(f"Created standardization table with {len(std_table)} unique excipients")
    
    # Analyze formulation compositions with consistent standardization and sorting
    print("\nAnalyzing formulation compositions with improved grouping...")
    analyze_formulation_compositions(df, excipient_data)
    
    # Create comprehensive analysis of all dosage forms
    print("\nCreating comprehensive analysis of all dosage forms...")
    all_excipients_df = analyze_all_dosage_forms(df)
    
    # Analyze special categories with improved integration
    print("\nAnalyzing special excipient categories...")
    analyze_special_categories(df)
    
    # NEW: Analyze API distribution
    print("\nAnalyzing API distribution...")
    api_distribution = analyze_api_distribution(df)
    
    # NEW: Analyze API-excipient relationships
    print("\nAnalyzing API-excipient relationships...")
    analyze_api_excipient_relationships(df, excipient_columns)
    
    print("\nAnalysis complete. All visualization plots saved as PNG files at 600 DPI.")
    print("The following improvements were implemented:")
    print("1. Consistent excipient standardization across all analyses using excipient_sorting module")
    print("2. Enhanced grouping of similar excipients (e.g., povidone variants clustered together)")
    print("3. Improved handling of categorical excipients with 'Surfactant/solubilizer' classification")
    print("4. Uniform high-resolution output (600 DPI) for all visualizations")
    print("5. Modular design with proper integration between preprocessing and visualization")
    print("6. Enhanced gelatin categorization to prevent misclassification between coating and bulking roles")
    print("7. Special handling for critical excipients to ensure they appear in relevant visualizations")
    print("8. NEW: Comprehensive API analysis with distribution charts and heatmaps")
    print("9. NEW: API-excipient relationship analysis for formulation insights")

if __name__ == "__main__":
    main()
