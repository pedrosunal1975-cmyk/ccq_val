# File: core/name_normalizer.py
# Path: core/name_normalizer.py

"""
Name Normalizer
===============

Generates entity name variations for fuzzy matching in file discovery.

Handles common entity name patterns:
- Space/underscore/hyphen variations
- Case variations (lowercase, title case)
- Punctuation variations (periods, commas)
- Common suffix removal (Inc, Corp, LLC, etc.)
"""

from typing import List


class NameNormalizer:
    """
    Generates entity name variations for fuzzy directory matching.
    
    Helps find files when entity names have different formatting
    in directory structures vs. configuration.
    """
    
    # Common corporate suffixes to try removing
    CORPORATE_SUFFIXES = [
        ' Inc', ' Inc.', ' Corp', ' Corp.', ' LLC', ' Ltd', ' Ltd.',
        ' Co', ' Co.', ' Company', ' Corporation', ' Limited'
    ]
    
    @staticmethod
    def generate_variations(entity_name: str) -> List[str]:
        """
        Generate common variations of entity name.
        
        Args:
            entity_name: Original entity name (e.g., "Apple Inc" or "VISA_INC.")
            
        Returns:
            List of name variations in order of likelihood
            
        Examples:
            "VISA_INC." -> [
                "VISA_INC.",
                "VISA_INC_",     # Period to underscore (CCQ common pattern)
                "VISA_INC",       # Period removed
                "visa_inc.",
                "visa_inc_",
                "visa_inc",
                ...
            ]
        """
        variations = []
        
        # 1. Original name
        variations.append(entity_name)
        
        # 2. CRITICAL: Punctuation variations (BEFORE other transformations)
        # This handles: VISA_INC. -> VISA_INC_ (CCQ pattern)
        if '.' in entity_name:
            # Replace period with underscore
            variations.append(entity_name.replace('.', '_'))
            # Remove period entirely
            variations.append(entity_name.replace('.', ''))
        
        if ',' in entity_name:
            # Remove commas
            variations.append(entity_name.replace(',', ''))
            # Replace comma with underscore
            variations.append(entity_name.replace(',', '_'))
            # Replace comma+space with underscore (common pattern)
            variations.append(entity_name.replace(',_', '_'))
            variations.append(entity_name.replace(', ', '_'))
            # CRITICAL: Replace comma+underscore with double underscore (CCQ pattern)
            # "Companies,_Inc." -> "Companies__Inc."
            variations.append(entity_name.replace(',_', '__'))
        
        # Handle combined punctuation (period AND comma)
        if '.' in entity_name and ',' in entity_name:
            # CCQ pattern: "Companies,_Inc." -> "Companies__Inc_"
            temp = entity_name.replace(',_', '__').replace('.', '_')
            variations.append(temp)
        
        # 3. Common separator variations (preserve case)
        variations.append(entity_name.replace(' ', '_'))
        variations.append(entity_name.replace(' ', ''))
        variations.append(entity_name.replace(' ', '-'))
        
        # 4. Lowercase variations
        lower_name = entity_name.lower()
        variations.append(lower_name)
        variations.append(lower_name.replace(' ', '-'))
        variations.append(lower_name.replace(' ', '_'))
        variations.append(lower_name.replace(' ', ''))
        
        # Lowercase with punctuation variations
        if '.' in entity_name:
            variations.append(lower_name.replace('.', '_'))
            variations.append(lower_name.replace('.', ''))
        if ',' in entity_name:
            variations.append(lower_name.replace(',', ''))
            variations.append(lower_name.replace(',', '_'))
        
        # 5. Title case variations
        title_name = entity_name.title()
        variations.append(title_name)
        variations.append(title_name.replace(' ', '_'))
        variations.append(title_name.replace(' ', ''))
        
        # Title case with punctuation variations
        if '.' in entity_name:
            variations.append(title_name.replace('.', '_'))
            variations.append(title_name.replace('.', ''))
        
        # 6. Variations without corporate suffixes
        for suffix in NameNormalizer.CORPORATE_SUFFIXES:
            if entity_name.endswith(suffix):
                base_name = entity_name[:-len(suffix)].strip()
                
                # Add base variations
                variations.append(base_name)
                variations.append(base_name.replace(' ', '_'))
                variations.append(base_name.replace(' ', ''))
                variations.append(base_name.lower().replace(' ', '_'))
                variations.append(base_name.lower().replace(' ', ''))
                
                # Add base with punctuation variations
                if '.' in base_name:
                    variations.append(base_name.replace('.', '_'))
                    variations.append(base_name.replace('.', ''))
                    variations.append(base_name.lower().replace('.', '_'))
                    variations.append(base_name.lower().replace('.', ''))
        
        # 7. Remove duplicates while preserving order
        return NameNormalizer._deduplicate_preserving_order(variations)
    
    @staticmethod
    def normalize_for_comparison(name: str) -> str:
        """
        Normalize name for fuzzy comparison.
        
        Removes all separators and punctuation, then lowercases
        for maximum flexibility in matching.
        
        Removes: spaces, underscores, hyphens, periods, commas, parentheses
        
        Args:
            name: Entity name
            
        Returns:
            Normalized name for comparison
            
        Examples:
            "Apple_Inc." -> "appleinc"
            "Albertsons_Companies,_Inc." -> "albertsonscompaniesinc"
            "Visa Inc." -> "visainc"
            "Company (USA)" -> "companyusa"
        """
        return (
            name.lower()
            .replace(' ', '')
            .replace('_', '')
            .replace('-', '')
            .replace('.', '')
            .replace(',', '')
            .replace('(', '')
            .replace(')', '')
            .replace("'", '')
            .replace('"', '')
        )
    
    @staticmethod
    def fuzzy_match(name1: str, name2: str) -> bool:
        """
        Check if two names match after normalization.
        
        Args:
            name1: First entity name
            name2: Second entity name
            
        Returns:
            True if names match after normalization
        """
        norm1 = NameNormalizer.normalize_for_comparison(name1)
        norm2 = NameNormalizer.normalize_for_comparison(name2)
        
        # Match if one contains the other (handles suffix variations)
        return norm1 in norm2 or norm2 in norm1
    
    @staticmethod
    def _deduplicate_preserving_order(items: List[str]) -> List[str]:
        """
        Remove duplicates while preserving order.
        
        Args:
            items: List with potential duplicates
            
        Returns:
            List with duplicates removed, order preserved
        """
        seen = set()
        unique_items = []
        for item in items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)
        return unique_items


__all__ = ['NameNormalizer']