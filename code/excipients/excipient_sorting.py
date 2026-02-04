
import pandas as pd
import re

def standardize_excipient_names(excipient_name):
    """
    Standardize excipient names to resolve duplications and inconsistencies
    while ensuring specific excipient types remain separate
    """
    if pd.isna(excipient_name) or excipient_name == '' or excipient_name == 'n/a':
        return None
    
    # Original name for exact matching
    original_name = str(excipient_name).strip()
    name_lower = original_name.lower()
    
    # PRESERVE EXACT MATCHES FOR SPECIFIC ENTRIES
    # Special case 1: Preserve "Maltitol liquid" exactly as is
    if name_lower == 'maltitol liquid':
        return original_name
        
    # Special case 2: If the original entry contains "(unspecified)", preserve it exactly as is
    if "(unspecified)" in original_name:
        return original_name
    
    # Special case for Potato starch hydrogenperodizied
    if 'potato starch hydrogenperodizied' in name_lower:
        return "Potato starch (hydrogenperodizied)"  # Return with parentheses
    
    # Starch variations - handle specific modifiers and pre-gelatinisation
    if 'starch' in name_lower:
        # Define modifiers to look for and convert to parenthesized format
        modifiers = [
            'hydrogenperoxidised', 'hydrogenperoxidized', 'oxidized', 'oxidised', 
            'acetylated', 'acetylised', 'modified', 'hydrolyzed', 'hydrolysed',
            'crosslinked', 'cross-linked', 'substituted'
        ]
        
        # Check if already properly formatted with parentheses
        if any(f"({mod})" in name_lower for mod in modifiers) or "oxidized and acetylated" in name_lower:
            # Already has parenthesized modifier, just ensure proper capitalization
            words = name_lower.split()
            if words:
                words[0] = words[0].capitalize()
            return ' '.join(words)
        
        # Check for non-parenthesized modifiers
        found_modifier = None
        for mod in modifiers:
            if mod in name_lower and "(" not in name_lower:
                found_modifier = mod
                break
        
        # If a modifier was found but not in parentheses, reformat
        if found_modifier:
            # Extract the starch type
            starch_type = None
            if 'potato' in name_lower:
                starch_type = 'Potato'
            elif 'maize' in name_lower or 'corn' in name_lower:
                starch_type = 'Maize'
            elif 'rice' in name_lower:
                starch_type = 'Rice'
            elif 'wheat' in name_lower:
                starch_type = 'Wheat'
            else:
                starch_type = 'Starch'
            
            # Format with parenthesized modifier
            return f"{starch_type} starch ({found_modifier})"
        
        # Check if it's pre-gelatinised
        is_pregelatinised = any(term in name_lower for term in [
            'pre-gelatinised', 'pregelatinised', 'pre-gelatinized', 
            'pregelatinized', 'pregelatin'
        ])
        
        # Sodium starch glycolate - special case
        if 'sodium' in name_lower:
            return 'Sodium starch glycolate'
        
        # Handle specific starch types
        starch_type = None
        if 'corn' in name_lower or 'maize' in name_lower:
            starch_type = 'maize'
        elif 'potato' in name_lower:
            starch_type = 'potato'
        elif 'rice' in name_lower:
            starch_type = 'rice'
        elif 'wheat' in name_lower:
            starch_type = 'wheat'
        
        # Build the standardized name
        if is_pregelatinised:
            prefix = 'Pre-gelatinised'
            if starch_type:
                result = f"{prefix} {starch_type} starch"
            else:
                result = f"{prefix} starch"
            return result
        
        # Regular starch (not pre-gelatinised)
        if starch_type:
            result = f"{starch_type.capitalize()} starch"
            return result
        
        # Generic starch
        return "Starch"
    
    # Povidone variations - group together as requested
    if 'povidone' in name_lower or 'pvp' in name_lower or 'polyvinylpyrrolidone' in name_lower:
        if 'crospovidone' in name_lower:
            return 'Crospovidone'
        if 'copovidone' in name_lower:
            return 'Copovidone'
        # Extract K-value if present
        k_values = re.findall(r'k[-\s]?(\d+)', name_lower, re.IGNORECASE)
        if k_values:
            return f'Povidone K-{k_values[0]}'
        return 'Povidone'
    
    # Gelatin - keep separate from any starch types
    if name_lower == 'gelatin' or (('gelatin' in name_lower) and not ('pregelatin' in name_lower) and not ('starch' in name_lower)):
        return 'Gelatin'
    
    # Cellulose variations - keep each type separate as requested
    if 'cellulose' in name_lower:
        if 'microcrystalline' in name_lower or 'avicel' in name_lower:
            return 'Microcrystalline cellulose'
        if 'hydroxypropyl' in name_lower and 'methyl' not in name_lower:
            return 'Hydroxypropyl cellulose'
        if 'ethyl' in name_lower:
            return 'Ethylcellulose'
        if 'carboxy' in name_lower:
            if 'sodium' in name_lower:
                return 'Croscarmellose sodium'
            return 'Carboxymethylcellulose'
        return 'Cellulose'
    
    # Hypromellose - keep as its own entity
    if 'hypromellose' in name_lower or 'hydroxypropyl methyl' in name_lower:
        if 'film' in name_lower:
            return 'Hypromellose film'
        return 'Hypromellose'
    
    # Glycerides and glycerin - KEEP SPECIFIC ORIGINAL ENTRIES
    # Only standardize generic or common cases
    if name_lower == 'glycerin':
        return 'Glycerin'
    if name_lower == 'glycerol':
        return 'Glycerol'
    if name_lower == 'propylene glycol':
        return 'Propylene glycol'
    if name_lower == 'medium-chain triglycerides' or name_lower == 'medium chain triglycerides':
        return 'Medium-chain triglycerides'
    
    # For other glyceride variations, preserve the original entry with proper capitalization (first word only)
    if 'glyceride' in name_lower or 'triglyceride' in name_lower:
        # Capitalize only the first word
        words = name_lower.split()
        if words:
            words[0] = words[0].capitalize()
        return ' '.join(words)
    
    # Macrogol variations - KEEP SPECIFIC ORIGINAL ENTRIES
    if 'macrogol' in name_lower or 'peg' in name_lower or 'polyethylene glycol' in name_lower:
        # Standardize PEG and polyethylene glycol to macrogol format
        if 'peg' in name_lower or 'polyethylene glycol' in name_lower:
            # Extract number if present
            numbers = re.findall(r'(\d+)', name_lower)
            if numbers and int(numbers[0]) > 0:
                return f'Macrogol {numbers[0]}'
            else:
                return 'Macrogol (unspecified)'
        
        # For existing macrogol entries, preserve them but ensure proper capitalization
        words = name_lower.split()
        if words:
            words[0] = words[0].capitalize()
        return ' '.join(words)
    
    # Titanium dioxide
    if 'titanium dioxide' in name_lower or 'titanium oxide' in name_lower:
        return 'Titanium dioxide'
    
    # Sodium-containing compounds - keep each separate as requested
    if 'sodium' in name_lower:
        if 'lauryl' in name_lower and ('sulfate' in name_lower or 'sulphate' in name_lower):
            return 'Sodium lauryl sulfate'
        if 'starch' in name_lower:
            return 'Sodium starch glycolate'
        if 'croscarmellose' in name_lower:
            return 'Croscarmellose sodium'
        if 'carbonate' in name_lower:
            return 'Sodium hydrogen carbonate'
        if 'stearate' in name_lower:
            return 'Sodium stearate'
        # Keep other sodium compounds with their original name but ensure first word capitalization
        words = name_lower.split()
        if words:
            words[0] = words[0].capitalize()
        return ' '.join(words)
    
    # Stearate variations
    if 'stearate' in name_lower:
        if 'magnesium' in name_lower:
            return 'Magnesium stearate'
        if 'calcium' in name_lower:
            return 'Calcium stearate'
        if 'sodium' in name_lower:
            return 'Sodium stearate'
        if 'zinc' in name_lower:
            return 'Zinc stearate'
        return 'Stearate'
    
    # Stearic acid
    if 'stearic acid' in name_lower:
        return 'Stearic acid'
    
    # Lactose variations
    if 'lactose' in name_lower:
        if 'monohydrate' in name_lower:
            return 'Lactose monohydrate'
        if 'anhydrous' in name_lower:
            return 'Lactose anhydrous'
        if 'spray' in name_lower and 'dried' in name_lower:
            return 'Spray-dried lactose'
        return 'Lactose'
    
    # Iron oxide variations
    if 'iron oxide' in name_lower:
        for color in ['yellow', 'red', 'black', 'brown']:
            if color in name_lower:
                return f'Iron oxide {color}'
        return 'Iron oxide'
    
    # Erythrosine
    if 'erythrosine' in name_lower:
        return 'Erythrosine'
    
    # Talc
    if 'talc' in name_lower:
        return 'Talc'
    
    # Polyols
    if 'sorbitol' in name_lower:
        if 'partially dehydrated' in name_lower:
            return 'Sorbitol partially dehydrated'
        return 'Sorbitol'
    if 'mannitol' in name_lower:
        return 'Mannitol'
    if 'maltitol' in name_lower:
        # Special case: preserve "Maltitol liquid" exactly
        if 'liquid' in name_lower:
            # Keep original capitalization
            words = original_name.split()
            return ' '.join(words)
        if '500' in name_lower:
            return 'Maltitol 500'
        return 'Maltitol'
    if 'isomalt' in name_lower:
        return 'Isomalt'
    if 'xylitol' in name_lower:
        return 'Xylitol'
    
    # For unhandled cases, ensure only first word is capitalized
    words = name_lower.split()
    if words:
        words[0] = words[0].capitalize()
    return ' '.join(words)

def get_excipient_sort_key(excipient_name):
    """
    Generate a sort key for excipients to ensure similar types are grouped together
    while keeping specified categories separate
    """
    excipient_lower = excipient_name.lower()
    
    # Define specific order of excipient classes (this controls the overall grouping)
    excipient_classes = {
        # Starches - regular and pre-gelatinised variants as separate categories
        'Starch': 10,
        'Starch (unspecified)': 10,
        'Maize starch': 11,
        'Potato starch': 12,
        'Rice starch': 13,
        'Wheat starch': 14,
        'Pre-gelatinised starch': 15,
        'Pre-gelatinised starch (unspecified)': 15,  # Exact match for this specific entry
        'Pre-gelatinised maize starch': 16,
        'Pre-gelatinised potato starch': 17,
        'Pre-gelatinised rice starch': 18,
        'Pre-gelatinised wheat starch': 19,
        
        # Base sorting categories for starch with modifiers
        'potato starch hydro': 25,  # Base for various hydrogenated/oxidized potato starches
        'potato starch (hydro': 25,  # Parenthesized version
        'potato starch (hydrogenperodizied)': 25,  # Exact match for special case
        'maize starch hydro': 26,   # Base for modified maize starches
        'maize starch (hydro': 26,   # Parenthesized version
        'modified starch': 27,      # Base for other modified starches
        
        # Cellulose compounds - keep each type separate
        'Cellulose': 30,
        'Microcrystalline cellulose': 31,
        'Hydroxypropyl cellulose': 32,
        'Ethylcellulose': 33,
        'Methylcellulose': 34,
        'Carboxymethylcellulose': 35,
        
        # Hypromellose - separate from other cellulose types
        'Hypromellose': 40,
        'Hypromellose film': 41,
        
        # Gelatin - separate category
        'Gelatin': 50,
        
        # Glycerin/glycerides group - for sorting purposes only
        'Glycerin': 60,
        'Glycerol': 61,
        'Propylene glycol': 62,
        'glyceride': 63,  # Base key for glycerides - lowercase for matching
        'triglyceride': 64,  # Base key for triglycerides - lowercase for matching
        'Medium-chain triglycerides': 65,
        
        # Sodium compounds - keep each distinct
        'Sodium lauryl sulfate': 70,
        'Sodium starch glycolate': 71,
        'Croscarmellose sodium': 72,
        'Sodium hydrogen carbonate': 73,
        'Sodium stearate': 74,
        
        # Lactose types
        'Lactose': 80,
        'Lactose monohydrate': 81,
        'Lactose anhydrous': 82,
        'Spray-dried lactose': 83,
        
        # Polyols
        'Mannitol': 90,
        'Sorbitol': 91,
        'Xylitol': 92,
        'Maltitol': 93,
        'Maltitol liquid': 93,  # Add exact entry for Maltitol liquid to maintain grouping
        'Isomalt': 94,
        
        # Povidone group - cluster these together
        'Povidone': 100,
        'Povidone K-': 100,  # Base for K-values
        'Crospovidone': 101, 
        'Copovidone': 102,
        
        # Lubricants and stearates
        'Magnesium stearate': 110,
        'Calcium stearate': 111,
        'Zinc stearate': 112,
        'Stearate': 113,
        'Stearic acid': 114,
        
        # Colorants
        'Titanium dioxide': 120,
        'Iron oxide': 121,
        'Iron oxide red': 122,
        'Iron oxide yellow': 123,
        'Iron oxide black': 124,
        'Iron oxide brown': 125,
        'Erythrosine': 126,
        
        # Coating materials
        'Talc': 130,
        'Opadry': 131,
        'Polyvinyl alcohol': 132,
        'Polyvinyl-alcohol film': 133,
        
        # Waxes
        'Carnauba wax': 140,
        'Beeswax': 141,
        'Montanglycol wax': 142,
        
        # Macrogols - base sort category
        'macrogol': 150,  # lowercase for matching
        
        # Other common excipients
        'Sucrose': 160,
        'Purified water': 170,
    }
    
    # Handle special cases first
    
    # Special case: "Maltitol liquid" - exact match
    if excipient_lower == 'maltitol liquid':
        return (93, 1, excipient_name)  # Group with Maltitol but distinguish as variant
    
    # Special case: "Pre-gelatinised starch (unspecified)" - exact match
    if excipient_lower == 'pre-gelatinised starch (unspecified)':
        return (15, 0, excipient_name)
    
    # Special case: Modified starches (preserve specific variants but group them)
    if 'starch' in excipient_lower:
        # Check for both parenthesized and non-parenthesized modifiers
        has_modifier = False
        for mod in [
            'hydrogenperoxidised', 'hydrogenperoxidized', 'oxidized', 'oxidised', 
            'acetylated', 'acetylised', 'modified', 'hydrolyzed', 'hydrolysed'
        ]:
            if mod in excipient_lower or f"({mod})" in excipient_lower:
                has_modifier = True
                break
        
        # Handle special case for hydrogenperodizied (with alternative spelling)
        if 'hydrogenperodizied' in excipient_lower:
            has_modifier = True
        
        if has_modifier:
            if 'potato' in excipient_lower:
                return (25, 0, excipient_name)
            if 'maize' in excipient_lower or 'corn' in excipient_lower:
                return (26, 0, excipient_name)
            return (27, 0, excipient_name)
    
    # Special handling for Macrogols to group them together while preserving specific types
    if 'macrogol' in excipient_lower or 'peg' in excipient_lower or 'polyethylene glycol' in excipient_lower:
        # Extract number if present for sub-sorting
        numbers = re.findall(r'(\d+)', excipient_lower)
        if numbers:
            try:
                number = int(numbers[0])
                return (150, number, excipient_name)  # Sort by molecular weight
            except ValueError:
                pass
        # For unspecified macrogols, sort at the beginning of the macrogol section
        if 'unspecified' in excipient_lower:
            return (150, 0, excipient_name)
        # For other macrogols without a number or with non-numeric identifier
        return (150, 999, excipient_name)
    
    # Special handling for glycerides to group them together while preserving specific types
    if 'glyceride' in excipient_lower:
        if 'triglyceride' in excipient_lower:
            if 'medium-chain' in excipient_lower or 'medium chain' in excipient_lower:
                return (65, 0, excipient_name)
            return (64, 0, excipient_name)  # Sort with other triglycerides
        return (63, 0, excipient_name)  # Sort with other glycerides
    
    # Exact match for entries with (unspecified) in our classes dictionary
    if '(unspecified)' in excipient_lower:
        for key, value in excipient_classes.items():
            if excipient_lower == key.lower():
                return (value, 0, excipient_name)
    
    # Check if the excipient is in our predefined classes
    for key, value in excipient_classes.items():
        if excipient_lower == key.lower():
            return (value, 0, excipient_name)
    
    # Handle excipients with (unspecified) qualifier
    if '(unspecified)' in excipient_lower:
        # Strip off (unspecified) for matching purposes
        base_name = excipient_lower.replace('(unspecified)', '').strip()
        for key, value in excipient_classes.items():
            if base_name == key.lower() or base_name.startswith(key.lower()):
                return (value, 1, excipient_name)  # 1 indicates it's a variant
    
    # Handle partially matching excipients
    for key, value in excipient_classes.items():
        if excipient_lower.startswith(key.lower()):
            return (value, 1, excipient_name)  # 1 indicates it's a variant of a known type
    
    # Default sorting for unknown excipients (alphabetical)
    return (999, 0, excipient_name)

def sort_excipients(excipient_list_or_series):
    """
    Sort a list or pandas Series of excipients to group similar types together
    """
    if isinstance(excipient_list_or_series, pd.Series):
        # For a Series, reindex with sorted indices
        sorted_index = sorted(excipient_list_or_series.index, key=get_excipient_sort_key)
        return excipient_list_or_series.reindex(sorted_index)
    else:
        # For a list, just sort directly
        return sorted(excipient_list_or_series, key=get_excipient_sort_key)

def sort_excipient_dataframe(df, axis=0):
    """
    Sort a DataFrame with excipients as indices or columns
    """
    if axis == 0:  # Sort rows (excipients as index)
        sorted_index = sorted(df.index, key=get_excipient_sort_key)
        return df.reindex(sorted_index)
    else:  # Sort columns (excipients as columns)
        sorted_columns = sorted(df.columns, key=get_excipient_sort_key)
        return df[sorted_columns]

# Simple test if run directly
if __name__ == "__main__":
    print("Sorting module loaded successfully!")
    # Test with the specific examples mentioned
    test_excipients = [
        "Starch", 
        "Starch (unspecified)",
        "Pre-gelatinised starch", 
        "Pre-gelatinised starch (unspecified)",
        "Maize starch", 
        "Pre-gelatinised maize starch",
        "Potato starch",
        "Potato starch (oxidized and acetylated)",
        "Potato starch hydrogenperoxidized",  # Without parentheses
        "Potato starch hydrogenperodizied",   # Special case with alternative spelling
        "Potato starch (hydrogenperoxidized)", # With parentheses
        "Potato starch (acetylated)",
        "Glycerin",
        "Glycerol",
        "Acetylated Monoglyceride",
        "Distilled Monoglycerides",
        "Medium-chain triglycerides",
        "Macrogol (unspecified)",
        "Macrogol 400",
        "Macrogol 600", 
        "Macrogol 3350",
        "Macrogol 6000",
        "PEG 400",
        "Polyethylene glycol 3350",
        "Maltitol",
        "Maltitol liquid",  # New test case
    ]
    sorted_excipients = sort_excipients(test_excipients)
    print(f"Test sorted excipients: {sorted_excipients}")
    
    # Print each standardized excipient to verify preservation of originals
    print("\nStandardized excipients:")
    for excip in test_excipients:
        standardized = standardize_excipient_names(excip)
        print(f"{excip} → {standardized}")
