"""
COT DATA RESEARCH LAB — Authoritative Data Dictionary (CFTC Aligned)
"""

import pandas as pd

DISAGGREGATED_FIELD_DEFS = [
    # 1. Identification
    {
        "category": "1. Identification",
        "column": "Market_and_Exchange_Names",
        "label": "Market & Exchange Name",
        "trader_group": "Metadata",
        "type": "String",
        "unit": "Text",
        "definition": "Official CFTC contract market name followed by exchange name.",
        "formula": "None",
        "interpretation": "Identifies the underlying futures and options market.",
        "pitfall": "Market names can change historically while contract codes remain continuous (e.g. Copper in Feb 2022)."
    },
    {
        "category": "1. Identification",
        "column": "CFTC_Contract_Market_Code",
        "label": "Contract Market Code",
        "trader_group": "Metadata",
        "type": "String",
        "unit": "Code",
        "definition": "Permanent CFTC 6-digit identifier for the contract market.",
        "formula": "None",
        "interpretation": "The primary immutable identifier for stitching market histories.",
        "pitfall": "Do not treat leading zeros as numeric truncation (e.g. 085692 must not become 85692)."
    },
    {
        "category": "1. Identification",
        "column": "Report_Date_as_YYYY-MM-DD",
        "label": "Report Date (As-Of)",
        "trader_group": "Metadata",
        "type": "Date",
        "unit": "YYYY-MM-DD",
        "definition": "The Tuesday closing date on which positions were measured.",
        "formula": "None",
        "interpretation": "Measurement timestamp. Note that public release occurs on Friday afternoon.",
        "pitfall": "Assuming data was publicly available on Tuesday causes fatal lookahead bias."
    },
    
    # 2. Open Interest
    {
        "category": "2. Open Interest",
        "column": "Open_Interest_All",
        "label": "Total Open Interest (All)",
        "trader_group": "Market Aggregate",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Total number of outstanding futures contracts plus delta-equivalent options contracts.",
        "formula": "Sum of all long (or short) positions across all contract months",
        "interpretation": "Measures total capital commitment and market breadth.",
        "pitfall": "Open interest represents one side of the market (Longs = Shorts = OI), do not sum long + short to get OI."
    },
    
    # 3. Long Positions
    {
        "category": "3. Long Positions",
        "column": "Prod_Merc_Positions_Long_All",
        "label": "Producer/Merchant Long (All)",
        "trader_group": "Producer/Merchant",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross long positions held by physical producers, merchants, processors, or commercial handlers.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Commercial entities locking in input costs or hedging physical commitments.",
        "pitfall": "Assuming commercials are always net short; processors often maintain substantial long hedges."
    },
    {
        "category": "3. Long Positions",
        "column": "Swap_Positions_Long_All",
        "label": "Swap Dealer Long (All)",
        "trader_group": "Swap Dealers",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross long positions held by swap dealers to offset OTC commodity swap exposures.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Often mirrors investor interest in long-only commodity index funds (ETFs/Notes).",
        "pitfall": "Confusing swap dealers with directional hedge funds; swap dealers hedge OTC client flows."
    },
    {
        "category": "3. Long Positions",
        "column": "M_Money_Positions_Long_All",
        "label": "Managed Money Long (All)",
        "trader_group": "Managed Money",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross long positions held by CTAs, CPOs, and registered investment managers.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Professional speculative capital expressing bullish directional trend views.",
        "pitfall": "Assuming Managed Money is always 'smart'; they are prone to crowded trade squeezes at extremes."
    },
    {
        "category": "3. Long Positions",
        "column": "Other_Rept_Positions_Long_All",
        "label": "Other Reportables Long (All)",
        "trader_group": "Other Reportables",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross long positions meeting reportable limits that do not fit the other commercial/spec categories.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Diverse institutional entities including corporate treasuries and non-swap dealers.",
        "pitfall": "Over-interpreting this heterogeneous residual group."
    },
    {
        "category": "3. Long Positions",
        "column": "NonRept_Positions_Long_All",
        "label": "Nonreportable Long (All)",
        "trader_group": "Nonreportable",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross long positions held by small non-reporting retail and commercial participants.",
        "formula": "Open_Interest_All - Tot_Rept_Positions_Long_All",
        "interpretation": "Retail sentiment and small trader exposure.",
        "pitfall": "Assuming nonreportables are always wrong; their aggregate volume is often too small to move markets."
    },
    
    # 4. Short Positions
    {
        "category": "4. Short Positions",
        "column": "Prod_Merc_Positions_Short_All",
        "label": "Producer/Merchant Short (All)",
        "trader_group": "Producer/Merchant",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross short positions held by miners, farmers, and physical producers hedging inventory.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Primary commercial supply hedge. Rises during physical production surplus or high prices.",
        "pitfall": "Treating producer shorting as bearish speculative speculation; it is structural supply hedging."
    },
    {
        "category": "4. Short Positions",
        "column": "Swap__Positions_Short_All",
        "label": "Swap Dealer Short (All)",
        "trader_group": "Swap Dealers",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross short positions held by swap dealers (note: raw CFTC column has double underscore).",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Hedging exposure against clients who have taken short OTC positions.",
        "pitfall": "Typo in official CFTC CSV: 'Swap__Positions_Short_All' contains two underscores."
    },
    {
        "category": "4. Short Positions",
        "column": "M_Money_Positions_Short_All",
        "label": "Managed Money Short (All)",
        "trader_group": "Managed Money",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross short positions held by CTAs, hedge funds, and trend followers.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Bearish speculative bets. High values indicate strong short consensus.",
        "pitfall": "Vulnerable to aggressive short-squeeze rallies when positioning is stretched."
    },
    {
        "category": "4. Short Positions",
        "column": "Other_Rept_Positions_Short_All",
        "label": "Other Reportables Short (All)",
        "trader_group": "Other Reportables",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross short positions of other reportable large traders.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Mixed commercial/institutional short positioning.",
        "pitfall": "Lacks specific mandate transparency compared to Managed Money."
    },
    {
        "category": "4. Short Positions",
        "column": "NonRept_Positions_Short_All",
        "label": "Nonreportable Short (All)",
        "trader_group": "Nonreportable",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross short positions held by small traders.",
        "formula": "Open_Interest_All - Tot_Rept_Positions_Short_All",
        "interpretation": "Retail short sentiment.",
        "pitfall": "Can be distorted by small local commercial hedges."
    },
    
    # 5. Spreading Positions
    {
        "category": "5. Spreading",
        "column": "M_Money_Positions_Spread_All",
        "label": "Managed Money Spreading (All)",
        "trader_group": "Managed Money",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Equal long and short positions held in different contract months by Managed Money.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Calendar spread and curve roll strategies (contango/backwardation plays).",
        "pitfall": "Spreading must be evaluated separately; adding it to outright long/short distorts directional net metrics."
    },
    
    # 6. Changes
    {
        "category": "6. Position Changes",
        "column": "Change_in_M_Money_Long_All",
        "label": "Change in Managed Money Long",
        "trader_group": "Managed Money",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Week-over-week change in Managed Money gross long contracts.",
        "formula": "Reported value (validated via M_Money_Long_t - M_Money_Long_{t-1})",
        "interpretation": "New long capital entering or exiting the market.",
        "pitfall": "Failing to check whether an increase in net position is driven by new longs vs short covering."
    },
    
    # 7. Percentage of Open Interest
    {
        "category": "7. Percentage of OI",
        "column": "Pct_of_OI_M_Money_Long_All",
        "label": "% of OI: Managed Money Long",
        "trader_group": "Managed Money",
        "type": "Float",
        "unit": "%",
        "definition": "Gross long positions of Managed Money divided by total Open Interest.",
        "formula": "(M_Money_Long / Open_Interest) * 100",
        "interpretation": "Normalized measure of speculative market ownership.",
        "pitfall": "Does not account for spreading; compare against gross outright open interest."
    },
    
    # 8. Trader Counts
    {
        "category": "8. Trader Counts",
        "column": "Traders_M_Money_Long_All",
        "label": "Trader Count: Managed Money Long",
        "trader_group": "Managed Money",
        "type": "Integer",
        "unit": "Count",
        "definition": "Number of distinct reporting entities in the Managed Money Long category.",
        "formula": "Count of unique CFTC filing entities",
        "interpretation": "Breadth of participation. High contracts with low trader count indicates extreme concentration.",
        "pitfall": "Assuming each trader has equal capital size."
    },
    
    # 9. Concentration
    {
        "category": "9. Concentration",
        "column": "Conc_Gross_LE_4_TDR_Long_All",
        "label": "Top 4 Traders Gross Long Share",
        "trader_group": "Concentration",
        "type": "Float",
        "unit": "%",
        "definition": "Percentage of total gross long Open Interest held by the largest 4 individual reporting traders.",
        "formula": "(Sum of 4 largest long positions / Total Open Interest) * 100",
        "interpretation": "Structural vulnerability to liquidation by dominant market participants.",
        "pitfall": "Confusing gross concentration with net concentration (net concentration nets out multi-month hedges)."
    }
]

TFF_FIELD_DEFS = [
    {
        "category": "1. Identification",
        "column": "Market_and_Exchange_Names",
        "label": "Market & Exchange Name",
        "trader_group": "Metadata",
        "type": "String",
        "unit": "Text",
        "definition": "Official CFTC financial contract market and exchange name.",
        "formula": "None",
        "interpretation": "Financial futures contract identification (rates, equities, FX, crypto).",
        "pitfall": "TFF is distinct from Disaggregated and applies to financial derivatives."
    },
    {
        "category": "3. Long Positions",
        "column": "Dealer_Positions_Long_All",
        "label": "Dealer/Intermediary Long (All)",
        "trader_group": "Dealer/Intermediary",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross long positions held by commercial banks and financial dealers.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Structural hedging and liquidity provision.",
        "pitfall": "Dealers are typically market makers taking the opposite side of client flows."
    },
    {
        "category": "3. Long Positions",
        "column": "Asset_Mgr_Positions_Long_All",
        "label": "Asset Manager Long (All)",
        "trader_group": "Asset Manager",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross long positions held by mutual funds, endowments, and pension managers.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Long-term institutional asset allocation and benchmark rebalancing.",
        "pitfall": "Asset managers move slowly; changes reflect strategic portfolio shifts."
    },
    {
        "category": "3. Long Positions",
        "column": "Lev_Money_Positions_Long_All",
        "label": "Leveraged Money Long (All)",
        "trader_group": "Leveraged Money",
        "type": "Float",
        "unit": "Contracts",
        "definition": "Gross long positions held by hedge funds and opportunistic speculative accounts.",
        "formula": "Direct CFTC Report Value",
        "interpretation": "Tactical, high-turnover speculative long positioning.",
        "pitfall": "Do not treat Leveraged Money as identical to Managed Money in Disaggregated COT."
    }
]

def get_data_dictionary(report_family):
    if "Disaggregated" in report_family:
        return pd.DataFrame(DISAGGREGATED_FIELD_DEFS)
    else:
        return pd.DataFrame(TFF_FIELD_DEFS)

