"""
COT Weekly Market Screener & Intelligence Generator
===================================================
Scans both TFF and Disaggregated COT reports to generate:
- Extreme Overbought (Long Squeeze Risk)
- Extreme Oversold (Short Squeeze Candidate)
- Top Institutional Capital Flows (Accumulation vs Distribution)
- Commercial Hedging vs Speculative Positioning Divergences
- Actionable Markdown & Terminal Intelligence Report
"""

import os
import pandas as pd
from datetime import datetime
from cot_quant_engine import load_tff_data, load_disaggregated_data, compute_quant_features

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Curated Key Commodities & Financial Assets for High-Relevance Monitoring
PRIORITY_MARKETS = [
    # Commodities - Agriculture & Softs
    "CORN - CHICAGO BOARD OF TRADE",
    "SOYBEANS - CHICAGO BOARD OF TRADE",
    "SOYBEAN MEAL - CHICAGO BOARD OF TRADE",
    "SOYBEAN OIL - CHICAGO BOARD OF TRADE",
    "WHEAT-SRW - CHICAGO BOARD OF TRADE",
    "WHEAT-HRW - CHICAGO BOARD OF TRADE",
    "COFFEE C - ICE FUTURES U.S.",
    "SUGAR NO. 11 - ICE FUTURES U.S.",
    "COTTON NO. 2 - ICE FUTURES U.S.",
    "COCOA - ICE FUTURES U.S.",
    # Commodities - Energy & Metals
    "GOLD - COMMODITY EXCHANGE INC.",
    "SILVER - COMMODITY EXCHANGE INC.",
    "COPPER-GRADE #1 - COMMODITY EXCHANGE INC.",
    "PLATINUM - NEW YORK MERCANTILE EXCHANGE",
    "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE",
    "NATURAL GAS - NEW YORK MERCANTILE EXCHANGE",
    # Financials & Currencies
    "USD INDEX - ICE FUTURES U.S.",
    "EURO FX - CHICAGO MERCANTILE EXCHANGE",
    "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",
    "BRITISH POUND - CHICAGO MERCANTILE EXCHANGE",
    "AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE",
    "NASDAQ-100 Consolidated - CHICAGO MERCANTILE EXCHANGE",
    "UST 10Y NOTE - CHICAGO BOARD OF TRADE",
    "BITCOIN - CHICAGO MERCANTILE EXCHANGE"
]

def run_screener():
    print("=" * 70)
    print("   CFTC COT QUANT SCREENER & INTELLIGENCE ENGINE")
    print("=" * 70)

    # 1. Load Data
    print("\n[1/3] Loading TFF and Disaggregated datasets...")
    df_tff = load_tff_data()
    df_disagg = load_disaggregated_data()

    print(f"  -> TFF records: {len(df_tff)}")
    print(f"  -> Disaggregated records: {len(df_disagg)}")

    dfs = []
    if not df_tff.empty:
        dfs.append(df_tff)
    if not df_disagg.empty:
        dfs.append(df_disagg)

    if not dfs:
        print("[ERROR] No data found. Please run cto.py and download_disaggregated.py first.")
        return

    full_df = pd.concat(dfs, ignore_index=True)

    # 2. Compute Features
    print("[2/3] Computing rolling quant features (COT Index, Z-Score, Flow)...")
    full_df = compute_quant_features(full_df)

    # 3. Filter Latest Week
    latest_date = full_df['Date'].max()
    print(f"[3/3] Generating report for latest CFTC release as of: {latest_date.strftime('%Y-%m-%d')}...")

    latest_df = full_df[full_df['Date'] == latest_date].copy()

    # Filter priority markets or major liquid contracts
    liquid_mask = latest_df['Market'].isin(PRIORITY_MARKETS) | (latest_df['Open_Interest_All'] > 20000)
    focus_df = latest_df[liquid_mask].drop_duplicates(subset=['Market']).copy()

    # Sorting
    extreme_longs = focus_df[focus_df['COT_ZScore_3Y'] >= 1.5].sort_values('COT_ZScore_3Y', ascending=False)
    extreme_shorts = focus_df[focus_df['COT_ZScore_3Y'] <= -1.5].sort_values('COT_ZScore_3Y', ascending=True)
    top_inflows = focus_df.sort_values('Flow_1W', ascending=False).head(10)
    top_outflows = focus_df.sort_values('Flow_1W', ascending=True).head(10)

    # Display in Console (ASCII safe for Windows CMD / PowerShell)
    print("\n" + "=" * 70)
    print("[!] TOP EXTREME LONG POSITIONS (Long Squeeze / Overbought Risk)")
    print("=" * 70)
    for _, r in extreme_longs.head(8).iterrows():
        print(f"* {r['Market'][:42]:<42} | Z-Score: {r['COT_ZScore_3Y']:+5.2f} | COT 3Y: {r['COT_Index_3Y']:5.1f}% | Crowding: {r['Crowding_Index']:5.1f}%")

    print("\n" + "=" * 70)
    print("[*] TOP EXTREME SHORT POSITIONS (Short Squeeze Candidates)")
    print("=" * 70)
    for _, r in extreme_shorts.head(8).iterrows():
        print(f"* {r['Market'][:42]:<42} | Z-Score: {r['COT_ZScore_3Y']:+5.2f} | COT 3Y: {r['COT_Index_3Y']:5.1f}% | Crowding: {r['Crowding_Index']:5.1f}%")

    print("\n" + "=" * 70)
    print("[+] TOP INSTITUTIONAL CAPITAL INFLOWS THIS WEEK (Accumulation)")
    print("=" * 70)
    for _, r in top_inflows.head(8).iterrows():
        print(f"* {r['Market'][:42]:<42} | d1W Flow: {r['Flow_1W']:+9,.0f} contracts")

    print("\n" + "=" * 70)
    print("[-] TOP INSTITUTIONAL CAPITAL OUTFLOWS THIS WEEK (Distribution)")
    print("=" * 70)
    for _, r in top_outflows.head(8).iterrows():
        print(f"* {r['Market'][:42]:<42} | d1W Flow: {r['Flow_1W']:+9,.0f} contracts")

    # Generate Markdown Report
    report_path = os.path.join(BASE_DIR, "weekly_cot_intelligence_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 📊 CFTC Commitment of Traders (COT) Weekly Intelligence Report\n\n")
        f.write(f"> **Report As-Of Date:** {latest_date.strftime('%Y-%m-%d')} (Released Friday close, effective next week trading)\n\n")
        
        f.write("## 1. 🚨 Cảnh báo Vùng Cực trị: Long Squeeze (Quá Mua Cấu Trúc)\n")
        f.write("Khi Z-Score > +1.5 hoặc COT Index 3Y > 90%, phe Mua đầu cơ (Hedge Funds) đã dồn tỷ trọng quá lớn. Sức mua mới cạn kiệt, rủi ro đảo chiều mạnh khi có tin tức bất lợi.\n\n")
        f.write("| Thị trường | Z-Score (3Y) | COT Index 3Y | Crowding (%) | Vị thế Net Spec | Trạng thái |\n")
        f.write("|:---|:---:|:---:|:---:|:---:|:---|\n")
        for _, r in extreme_longs.iterrows():
            f.write(f"| **{r['Market']}** | `{r['COT_ZScore_3Y']:+.2f}` | `{r['COT_Index_3Y']:.1f}%` | `{r['Crowding_Index']:.1f}%` | `{r['Net_Spec']:+,.0f}` | {r['Regime_Signal']} |\n")

        f.write("\n---\n\n## 2. 🚀 Cảnh báo Vùng Cực trị: Short Squeeze (Bán Tháo Cực Đại)\n")
        f.write("Khi Z-Score < -1.5 hoặc COT Index 3Y < 10%, phe Bán đầu cơ đã short kịch kim. Dễ xảy ra hiện tượng Short Squeeze (bật tăng bất thình lình khi phe short cắt lỗ).\n\n")
        f.write("| Thị trường | Z-Score (3Y) | COT Index 3Y | Crowding (%) | Vị thế Net Spec | Trạng thái |\n")
        f.write("|:---|:---:|:---:|:---:|:---:|:---|\n")
        for _, r in extreme_shorts.iterrows():
            f.write(f"| **{r['Market']}** | `{r['COT_ZScore_3Y']:+.2f}` | `{r['COT_Index_3Y']:.1f}%` | `{r['Crowding_Index']:.1f}%` | `{r['Net_Spec']:+,.0f}` | {r['Regime_Signal']} |\n")

        f.write("\n---\n\n## 3. 🌊 Top Dòng tiền Tổ chức Bơm Mua Mạnh Nhất Tuần Qua (Accumulation)\n\n")
        f.write("| Thị trường | Thay đổi 1W (Contracts) | Thay đổi 4W | OI Change (%) | Chế độ Dòng tiền |\n")
        f.write("|:---|:---:|:---:|:---:|:---|\n")
        for _, r in top_inflows.iterrows():
            f.write(f"| **{r['Market']}** | `{r['Flow_1W']:+,.0f}` | `{r['Flow_4W']:+,.0f}` | `{r['OI_Pct_1W']:+.1f}%` | {r['Regime_Signal']} |\n")

        f.write("\n---\n\n## 4. 🔻 Top Dòng tiền Tổ chức Rút Bán Mạnh Nhất Tuần Qua (Distribution)\n\n")
        f.write("| Thị trường | Thay đổi 1W (Contracts) | Thay đổi 4W | OI Change (%) | Chế độ Dòng tiền |\n")
        f.write("|:---|:---:|:---:|:---:|:---|\n")
        for _, r in top_outflows.iterrows():
            f.write(f"| **{r['Market']}** | `{r['Flow_1W']:+,.0f}` | `{r['Flow_4W']:+,.0f}` | `{r['OI_Pct_1W']:+.1f}%` | {r['Regime_Signal']} |\n")

        f.write("\n---\n\n## 5. 💡 Khuyến nghị Chiến lược Giao dịch (Strategy Execution)\n")
        f.write("1. **Tránh Fomo Mua ở các tài sản thuộc Mục 1**: Đang ở đỉnh vị thế mua 3 năm, tỷ lệ R:R vào lệnh Long rất kém.\n")
        f.write("2. **Quan sát tín hiệu Reversal ở Mục 2**: Chờ Price Action tạo cụm nến đảo chiều hoặc phân kỳ RSI/MACD trên khung D1 để bắt nhịp Short Squeeze với R:R cao.\n")
        f.write("3. **Đánh theo sóng Momentum ở Mục 3**: Các tài sản có `STRONG ACCUMULATION` kết hợp OI tăng là những thị trường có dòng tiền thực hỗ trợ xu hướng tăng tiếp diễn.\n")

    print(f"\n[OK] Full intelligence report generated at: {report_path}")

if __name__ == "__main__":
    run_screener()
