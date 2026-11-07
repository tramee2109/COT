"""
COT DATA RESEARCH LAB — Institutional Knowledge Base & Methodological Handbook
"""

KNOWLEDGE_TOPICS = [
    {
        "id": "sentiment",
        "title": "1. Market Sentiment & Positioning Aggregation",
        "concept": "Aggregate positioning provides an empirical balance sheet of real capital commitments across commercial and speculative agents, moving beyond opinion surveys.",
        "rationale": "Positioning reflects financial skin in the game. When market participants establish large futures commitments, capital constraints and margin limits anchor their ability to absorb adverse price moves.",
        "fields": "Prod_Merc_Positions_Long/Short, M_Money_Positions_Long/Short, Open_Interest_All",
        "methodology": "Calculate Net Position standardized by Open Interest. Track the percentage of total open contracts held by speculative vs commercial entities.",
        "charts": "Net Position Time Series, Composition Bar Charts, % of OI Area Curves",
        "strengths": "Direct measurement of financial exposure; legally mandatory reporting backed by CFTC regulatory oversight.",
        "limitations": "Weekly reporting frequency; positions measured Tuesday close and released Friday afternoon (inherent delay).",
        "pitfalls": "Confusing opinion sentiment surveys (e.g. AAII, Investor Intelligence) with actual balance-sheet positioning."
    },
    {
        "id": "speculation",
        "title": "2. Speculative Positioning (Managed Money / Leveraged Funds)",
        "concept": "Managed Money represents trend-following CTAs, hedge funds, and discretionary speculative capital.",
        "rationale": "Speculators take on price risk that commercial hedgers seek to transfer. Their flows amplify momentum during trend expansion and face severe liquidation pressure at extreme crowding.",
        "fields": "M_Money_Positions_Long_All, M_Money_Positions_Short_All, M_Money_Positions_Spread_All",
        "methodology": "Compute Net Speculative Position, 3-year rolling Z-score, and historical percentile. Decompose changes into new buying vs short covering.",
        "charts": "Managed Money Long vs Short, Rolling Z-Score bands (+/-2 sigma), 4-Week Flow Velocity",
        "strengths": "High sensitivity to macroeconomic shifts, interest rates, and commodity super-cycle momentum.",
        "limitations": "Speculators can remain heavily positioned in persistent macro trends for extended multi-month windows.",
        "pitfalls": "Assuming speculators are 'dumb money' that must immediately reverse when reaching high percentiles."
    },
    {
        "id": "hedging",
        "title": "3. Commercial Hedging Behavior (Producers & Merchants)",
        "concept": "Commercial participants produce, process, or merchandise physical commodities. They hedge physical inventory and forward sales.",
        "rationale": "Producers hedge future physical extraction (e.g. copper mining, silver refining). As prices rise into high-margin territory, producers expand short hedges to lock in revenue.",
        "fields": "Prod_Merc_Positions_Long_All, Prod_Merc_Positions_Short_All",
        "methodology": "Track Producer Net Position against commodity cost curves and historical inventory cycles.",
        "charts": "Producer Net Position vs Settlement Price, Commercial Hedging Pressure Gauge",
        "strengths": "Unrivaled insight into physical supply-side economics and corporate forward revenue management.",
        "limitations": "Commercial hedging is structurally asymmetric (producers typically hold large net short hedges in contango markets).",
        "pitfalls": "Treating commercial shorting as a speculative bearish bet; it is standard risk transfer for physical producers."
    },
    {
        "id": "crowding",
        "title": "4. Crowded Trade Analysis & Liquidity Fragility",
        "concept": "A crowded trade occurs when one participant group holds an overwhelmingly one-sided position relative to available market liquidity.",
        "rationale": "When speculative long crowding reaches extreme percentiles (>90%), marginal buyers are exhausted. Any minor liquidity shock triggers rapid cascading stop-losses (Long Squeeze).",
        "fields": "M_Money_Long / (M_Money_Long + M_Money_Short), Conc_Gross_LE_4_TDR",
        "methodology": "Compute Crowding Ratio and compare with 3-year historical distribution. Flag simultaneous high concentration.",
        "charts": "Crowding Index Area Chart with 30%/70% Thresholds, Concentration Matrix",
        "strengths": "Identifies asymmetric risk-reward regimes where market fragility is elevated.",
        "limitations": "Crowding can persist and become even more crowded during supply shocks or monetary debasement.",
        "pitfalls": "Fading a crowded trade prematurely without confirming price action weakness or momentum exhaustion."
    },
    {
        "id": "trend_confirmation",
        "title": "5. Trend Confirmation Research & Open Interest Expansion",
        "concept": "Evaluating whether a price trend is supported by organic capital inflows (rising OI) or merely short covering.",
        "rationale": "A healthy bullish expansion requires fresh long capital (Price up + OI up + Spec Longs up). If price rises while OI falls, the move is driven by short liquidation.",
        "fields": "Change_in_Open_Interest_All, Change_in_M_Money_Long_All, Change_in_M_Money_Short_All",
        "methodology": "Matrix comparison of week-over-week price changes against OI and speculative net flows.",
        "charts": "Price vs OI Dual-Axis, 4-Quadrant Flow-Volume Regime Scatter Plot",
        "strengths": "Filters out hollow short-squeeze rallies that lack institutional follow-through.",
        "limitations": "Quarterly futures roll dates cause temporary non-directional drops in Open Interest.",
        "pitfalls": "Ignoring contract roll windows (e.g. March, May, July, September, December in COMEX metals)."
    },
    {
        "id": "reversal",
        "title": "6. Reversal Research & Extreme Squeeze Regimes",
        "concept": "Investigating empirical return distributions following extreme positioning deviations (|Z| > 2.0).",
        "rationale": "Extreme short positioning by Managed Money often coincides with max bearish sentiment, setting up explosive short squeezes.",
        "fields": "COT_ZScore_156W, Percentile_156W, Forward_Returns (1W to 13W)",
        "methodology": "Rigorous event-study analysis tracking forward price trajectories across 5-day to 65-day horizons.",
        "charts": "Forward Return Distribution Histograms, Event Study Trajectory Curves",
        "strengths": "Provides quantified historical probabilities rather than subjective chart opinions.",
        "limitations": "Small event sample size (N events usually between 15 and 45 per decade).",
        "pitfalls": "Claiming statistical significance guarantees tradable execution profit after transaction costs and slip."
    },
    {
        "id": "market_regimes",
        "title": "7. Market Regime Classification",
        "concept": "Partitioning market history into distinct structural states: Trend Expansion, Crowded Overextension, Mean Reversion, Consolidation.",
        "rationale": "Commodity models behave differently depending on the positioning regime. Momentum strategies thrive in Trend Expansion but suffer drawdowns in Crowded regimes.",
        "fields": "Z-Score, Flow Momentum (1W, 4W), OI Velocity",
        "methodology": "Multi-conditional rule-based regime assignment updated weekly.",
        "charts": "Historical Regime Timeline, State Transition Probability Matrix",
        "strengths": "Enables adaptive risk allocation and parameter adjustments for macro research.",
        "limitations": "Regimes can shift abruptly around geopolitical announcements or unexpected USDA/OPEC reports.",
        "pitfalls": "Overfitting regime definitions with too many arbitrary parameters."
    },
    {
        "id": "cross_commodity",
        "title": "8. Cross-Commodity Relative Positioning",
        "concept": "Comparing positioning percentiles across structurally related commodities (e.g. Copper, Silver, Platinum, Gold).",
        "rationale": "Precious and industrial metals share macro drivers (USD, real yields, global PMI) but differ in physical supply dynamics. Divergences reveal relative mispricings.",
        "fields": "Standardized Net % of OI across Copper (085692), Silver (084691), Platinum (076651)",
        "methodology": "Pairwise spread analysis of positioning percentiles; correlation matrix of weekly flows.",
        "charts": "Cross-Commodity Normalized Positioning Overlay, Relative Positioning Ratio Charts",
        "strengths": "Isolates commodity-specific supply/demand fundamentals from broad macro dollar movements.",
        "limitations": "Contract sizes and commercial structures vary across exchanges (COMEX vs NYMEX vs LME).",
        "pitfalls": "Comparing raw contract counts directly (e.g. Copper contracts vs Silver contracts) without normalizing by OI."
    },
    {
        "id": "divergence",
        "title": "9. Positioning Divergence Research",
        "concept": "Identifying divergence between price action and institutional positioning trends.",
        "rationale": "When price reaches a new multi-month high but Managed Money Net Longs fail to exceed previous highs, momentum is waning.",
        "fields": "Price Rolling High/Low vs Speculative Net Position Rolling High/Low",
        "methodology": "Scan for Bearish Divergence (higher price high + lower COT high) and Bullish Divergence (lower price low + higher COT low).",
        "charts": "Divergence Marking Indicator on Dual Price-COT Chart",
        "strengths": "Provides early lead-lag warnings before technical chart breakdowns occur.",
        "limitations": "Divergences can persist for weeks before triggering a reversal.",
        "pitfalls": "Treating divergence as an immediate timing trigger rather than an early structural warning."
    },
    {
        "id": "concentration",
        "title": "10. Concentration & Systemic Structural Risk",
        "concept": "Analyzing the percentage of open contracts held by the largest 4 and 8 traders.",
        "rationale": "High concentration indicates that a few dominant players control the marginal supply. If one dominant entity unwinds, market depth is severely impaired.",
        "fields": "Conc_Gross_LE_4_TDR_Long, Conc_Gross_LE_4_TDR_Short, Conc_Net_LE_4_TDR",
        "methodology": "Monitor Top 4 Gross and Net Concentration metrics relative to 5-year averages.",
        "charts": "Top 4 vs Top 8 Concentration Bar Comparison, Historical Concentration Time Series",
        "strengths": "Reveals structural illiquidity and systemic fragility hidden beneath aggregate Open Interest.",
        "limitations": "CFTC does not disclose individual entity identities for privacy and regulatory compliance.",
        "pitfalls": "Confusing gross concentration (across all contracts) with net concentration (which offsets calendar spreads)."
    }
]

