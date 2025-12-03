"""
Validation Constants
====================

Shared constants for validation engines including taxonomy concept mappings.
These mappings are used for exact matching of XBRL concepts across validation checks.
"""

# Taxonomy concept mappings for exact matching
# Maps validation concept names to actual XBRL taxonomy concept names

BALANCE_SHEET_CONCEPTS = {
    'Assets': ['Assets'],
    'Liabilities': ['Liabilities'],
    'StockholdersEquity': [
        'StockholdersEquity',
        'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'
    ],
    'AssetsCurrent': ['AssetsCurrent'],
    'LiabilitiesCurrent': ['LiabilitiesCurrent'],
    'CashAndCashEquivalentsAtCarryingValue': [
        'CashAndCashEquivalentsAtCarryingValue',
        'Cash',
        'CashAndCashEquivalents'
    ],
    'PropertyPlantAndEquipmentNet': [
        'PropertyPlantAndEquipmentNet'
    ],
}

INCOME_STATEMENT_CONCEPTS = {
    'Revenues': [
        'Revenues',
        'RevenueFromContractWithCustomerExcludingAssessedTax',
        'RevenueFromContractWithCustomerIncludingAssessedTax',
        'SalesRevenueNet'
    ],
    'CostOfRevenue': [
        'CostOfRevenue',
        'CostOfGoodsAndServicesSold'
    ],
    'GrossProfit': ['GrossProfit'],
    'OperatingExpenses': [
        'OperatingExpenses',
        'OperatingExpensesExcludingCostOfSales'
    ],
    'OperatingIncomeLoss': ['OperatingIncomeLoss'],
    'NetIncomeLoss': [
        'NetIncomeLoss',
        'ProfitLoss'
    ],
    'ResearchAndDevelopmentExpense': [
        'ResearchAndDevelopmentExpense'
    ],
    'SellingGeneralAndAdministrativeExpense': [
        'SellingGeneralAndAdministrativeExpense'
    ],
}

CASH_FLOW_CONCEPTS = {
    'NetCashProvidedByUsedInOperatingActivities': [
        'NetCashProvidedByUsedInOperatingActivities'
    ],
    'NetCashProvidedByUsedInInvestingActivities': [
        'NetCashProvidedByUsedInInvestingActivities'
    ],
    'NetCashProvidedByUsedInFinancingActivities': [
        'NetCashProvidedByUsedInFinancingActivities'
    ],
    'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect': [
        'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect',
        'CashAndCashEquivalentsPeriodIncreaseDecrease'
    ],
    'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents': [
        'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents',
        'CashAndCashEquivalentsAtCarryingValue'
    ],
    'NetIncomeLoss': [
        'NetIncomeLoss',
        'ProfitLoss'
    ],
}

# Combined concept map for convenience
ALL_CONCEPTS = {
    **BALANCE_SHEET_CONCEPTS,
    **INCOME_STATEMENT_CONCEPTS,
    **CASH_FLOW_CONCEPTS
}

# Concepts that must be positive (for anomaly detection)
MUST_BE_POSITIVE_CONCEPTS = {
    'Assets',
    'AssetsCurrent',
    'PropertyPlantAndEquipmentNet',
    'Revenues',
    'RevenueFromContractWithCustomerExcludingAssessedTax',
}

# Concepts that must be negative after normalization (expenses)
MUST_BE_NEGATIVE_CONCEPTS = {
    'CostOfRevenue',
    'OperatingExpenses',
    'ResearchAndDevelopmentExpense',
    'SellingGeneralAndAdministrativeExpense',
}

__all__ = [
    'BALANCE_SHEET_CONCEPTS',
    'INCOME_STATEMENT_CONCEPTS',
    'CASH_FLOW_CONCEPTS',
    'ALL_CONCEPTS',
    'MUST_BE_POSITIVE_CONCEPTS',
    'MUST_BE_NEGATIVE_CONCEPTS',
]