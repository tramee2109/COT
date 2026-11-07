"""
COT DATA RESEARCH LAB — Module 9: Data Center & Export Hub
Permits interactive preview, filtering, and direct CSV / Parquet downloading of:
1. Curated Weekly COT Market Data (Active Commodity)
2. Daily / Weekly Physical Commodity Settlement Prices
3. Aligned Multi-Variable Research Dataset (Positions + Prices + Flows + Metrics)
4. Full COT Historical Archives (Disaggregated & Legacy)
"""

import streamlit as st
import pandas as pd
import io
from research_lab.metrics_engine import compute_trader_metrics, compute_position_decomposition
from research_lab.price_engine import align_cot_and_price, COT_PRICE_MARKET_REGISTRY

def render_data_center(market_df, report_family_name, commodity_label, price_df, df_disagg, df_tff):
    st.title(f"📥 Data Center & Export Hub — {commodity_label}")
    st.caption("Directly inspect, customize, and export curated datasets in CSV or Parquet formats.")

    st.markdown("""
    Trung tâm dữ liệu cho phép bạn truy xuất, lọc dữ liệu theo nhu cầu và tải về máy tính để phục vụ nghiên cứu độc lập trên Excel, Python hoặc R.
    """)

    tabs = st.tabs([
        "📊 1. Dữ liệu Vị thế COT (Thị trường đang chọn)",
        "📈 2. Dữ liệu Giá Hàng hóa (Futures Settlement)",
        "🧪 3. Dữ liệu Nghiên cứu Hợp nhất (COT + Price + Flow)",
        "📦 4. Kho Dữ liệu Gốc Toàn diện (Full Archives)"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: ACTIVE MARKET COT DATA
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader(f"1. Dữ liệu Báo cáo COT: {commodity_label} ({report_family_name})")
        st.caption("Toàn bộ chuỗi dữ liệu báo cáo vị thế hàng tuần của mặt hàng đang chọn.")

        if market_df.empty:
            st.warning("Không có dữ liệu cho thị trường này.")
        else:
            m_metrics = compute_trader_metrics(market_df, report_family_name)
            
            c_f1, c_f2 = st.columns([2, 1])
            with c_f1:
                export_cols = st.multiselect(
                    "Chọn các cột muốn xuất (mặc định lấy các cột quan trọng):",
                    options=list(m_metrics.columns),
                    default=[c for c in [
                        'report_date', 'contract_code', 'market_name', 'Open_Interest_All',
                        'primary_spec_net', 'primary_commercial_net', 'managed_money_net_pct_oi',
                        'prod_merc_net_pct_oi', 'swap_net_pct_oi', 'non_rept_net_pct_oi'
                    ] if c in m_metrics.columns]
                )
            with c_f2:
                max_preview_rows = st.number_input("Số dòng xem trước:", min_value=5, max_value=500, value=15, key="cot_prev_rows")

            if not export_cols:
                export_cols = list(m_metrics.columns)

            subset_df = m_metrics[export_cols].sort_values('report_date', ascending=False)
            
            st.markdown(f"**Xem trước ({len(subset_df)} dòng tổng cộng):**")
            st.dataframe(subset_df.head(max_preview_rows), use_container_width=True)

            cd1, cd2 = st.columns(2)
            with cd1:
                csv_bytes = subset_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"⬇️ Tải file CSV ({commodity_label}_COT.csv)",
                    data=csv_bytes,
                    file_name=f"{commodity_label.lower().replace(' ', '_')}_{report_family_name.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Tải bảng dữ liệu vị thế dạng file CSV thông dụng, mở tốt trên Excel/Sheets."
                )
            with cd2:
                buffer = io.BytesIO()
                subset_df.to_parquet(buffer, index=False)
                st.download_button(
                    label=f"⬇️ Tải file Parquet ({commodity_label}_COT.parquet)",
                    data=buffer.getvalue(),
                    file_name=f"{commodity_label.lower().replace(' ', '_')}_{report_family_name.lower().replace(' ', '_')}.parquet",
                    mime="application/octet-stream",
                    use_container_width=True,
                    help="Tải định dạng Apache Parquet hiệu năng cao, tối ưu cho Python, R và Big Data."
                )

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: COMMODITY PRICE DATA
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.subheader(f"2. Chuỗi Giá Futures Hàng Ngày & Hàng Tuần")
        st.caption("Dữ liệu giá đóng cửa thanh toán liên tục (Continuous Daily Futures Settlement).")

        if commodity_label in ["Copper", "Silver", "Platinum"] and price_df is not None and not price_df.empty:
            p_code = {"Copper": "hg_f", "Silver": "si_f", "Platinum": "pl_f"}.get(commodity_label)
            p_sub = price_df[price_df['commodity'] == p_code].copy() if 'commodity' in price_df.columns else price_df.copy()
            
            if p_sub.empty:
                p_sub = price_df.copy()

            p_sub = p_sub.sort_values('date', ascending=False) if 'date' in p_sub.columns else p_sub

            st.markdown(f"**Xem trước dữ liệu giá {commodity_label} ({len(p_sub):,} ngày giao dịch):**")
            st.dataframe(p_sub.head(15), use_container_width=True)

            cd_p1, cd_p2 = st.columns(2)
            with cd_p1:
                csv_p_bytes = p_sub.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"⬇️ Tải Giá {commodity_label} (CSV)",
                    data=csv_p_bytes,
                    file_name=f"{commodity_label.lower()}_futures_daily.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Dữ liệu giá lịch sử liên tục định dạng CSV."
                )
            with cd_p2:
                buf_p = io.BytesIO()
                p_sub.to_parquet(buf_p, index=False)
                st.download_button(
                    label=f"⬇️ Tải Giá {commodity_label} (Parquet)",
                    data=buf_p.getvalue(),
                    file_name=f"{commodity_label.lower()}_futures_daily.parquet",
                    mime="application/octet-stream",
                    use_container_width=True,
                    help="Dữ liệu giá định dạng Parquet nén gọn gàng."
                )
        else:
            st.info(f"Hiện tại chuỗi giá hàng ngày được hiệu chỉnh và kiểm chứng cho Copper (Đồng), Silver (Bạc) và Platinum (Bạch kim).")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: ALIGNED RESEARCH DATASET
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[2]:
        st.subheader("3. Bảng Dữ liệu Nghiên cứu Đã Hợp nhất (Aligned Dataset)")
        st.caption("Dữ liệu khớp ngày giữa Báo cáo COT (Thứ Ba / Thứ Sáu công bố) và Giá Hàng hóa, kèm Flow Decomposition & Z-Scores.")

        if commodity_label in ["Copper", "Silver", "Platinum"]:
            m_metrics = compute_trader_metrics(market_df, report_family_name)
            spec_prefix = "M_Money" if "Disaggregated" in report_family_name else "Lev_Money"
            m_metrics = compute_position_decomposition(m_metrics, category_prefix=spec_prefix)

            conv = st.radio(
                "Quy ước khớp ngày giá (Alignment Convention):",
                ["Publication-Aware (Thứ 6 công bố - Loại trừ hoàn toàn Lookahead bias)", "Tuesday Survey Close (Thứ 3 khảo sát)"],
                horizontal=True
            )
            c_code = "publication_aware" if "Publication-Aware" in conv else "tuesday_close"

            aligned_data = align_cot_and_price(m_metrics, commodity_label, convention=c_code)

            if not aligned_data.empty:
                st.markdown(f"**Xem trước ({len(aligned_data)} tuần đồng bộ hoàn chỉnh):**")
                st.dataframe(aligned_data.sort_values('report_date', ascending=False).head(15), use_container_width=True)

                ca1, ca2 = st.columns(2)
                with ca1:
                    csv_a = aligned_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"⬇️ Tải Aligned Research Dataset (CSV)",
                        data=csv_a,
                        file_name=f"{commodity_label.lower()}_aligned_research_dataset.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Bộ dữ liệu sạch đã căn chỉnh giá và vị thế, sẵn sàng cho backtesting và mô hình hồi quy."
                    )
                with ca2:
                    buf_a = io.BytesIO()
                    aligned_data.to_parquet(buf_a, index=False)
                    st.download_button(
                        label=f"⬇️ Tải Aligned Research Dataset (Parquet)",
                        data=buf_a.getvalue(),
                        file_name=f"{commodity_label.lower()}_aligned_research_dataset.parquet",
                        mime="application/octet-stream",
                        use_container_width=True
                    )
        else:
            st.info("Tính năng ghép nối vị thế với giá hiện hỗ trợ các mặt hàng trọng điểm (Copper, Silver, Platinum).")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4: COMPLETE ARCHIVES
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[3]:
        st.subheader("4. Kho Lưu Trữ Dữ Liệu Lịch Sử Toàn Diện (Full Historical Archives)")
        st.caption("Tải về toàn bộ cơ sở dữ liệu hàng chục năm của tất cả các thị trường hàng hóa và tài chính.")

        col_arc1, col_arc2 = st.columns(2)

        with col_arc1:
            st.markdown("""
            #### 📦 Disaggregated COT Full Archive (2018 – 2026)
            - **Mô tả:** Toàn bộ báo cáo phân rã (Managed Money, Producer, Swap Dealers...) của tất cả các thị trường nông sản, năng lượng, kim loại.
            - **Dung lượng:** ~24 MB (Định dạng Parquet nén)
            """)
            if df_disagg is not None and not df_disagg.empty:
                buf_dis = io.BytesIO()
                df_disagg.to_parquet(buf_dis, index=False)
                st.download_button(
                    label="⬇️ Tải Toàn Bộ Disaggregated COT (Parquet)",
                    data=buf_dis.getvalue(),
                    file_name="cot_disagg_full_archive.parquet",
                    mime="application/octet-stream",
                    use_container_width=True
                )

        with col_arc2:
            st.markdown("""
            #### 📦 Financial Futures (TFF) Full Archive
            - **Mô tả:** Toàn bộ dữ liệu vị thế tài chính (Traders in Financial Futures: Trái phiếu, Tiền tệ, Chỉ số chứng khoán).
            - **Dung lượng:** Tối ưu hóa siêu nhẹ
            """)
            if df_tff is not None and not df_tff.empty:
                buf_tff = io.BytesIO()
                df_tff.to_parquet(buf_tff, index=False)
                st.download_button(
                    label="⬇️ Tải Toàn Bộ TFF COT (Parquet)",
                    data=buf_tff.getvalue(),
                    file_name="cot_tff_full_archive.parquet",
                    mime="application/octet-stream",
                    use_container_width=True
                )

