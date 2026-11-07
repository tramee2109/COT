# 🏛️ HƯỚNG DẪN SỬ DỤNG COT DATA RESEARCH LAB
**Dành cho Người mới bắt đầu: Từ Khái niệm cơ bản đến Nghiên cứu Định lượng Chuyên sâu**

---

## MỤC LỤC
1. [Bản chất COT là gì? (Hiểu đúng trong 3 phút)](#1-bản-chất-cot-là-gì)
2. [Cách khởi động Trạm nghiên cứu](#2-cách-khởi-động-trạm-nghiên-cứu)
3. [Bố cục tổng quan & Quy tắc cốt lõi](#3-bố-cục-tổng-quan--quy-tắc-cốt-lõi)
4. [Hướng dẫn chi tiết 8 Module (Kèm Ví dụ Thực tế)](#4-hướng-dẫn-chi-tiết-8-module)
   - [Module 1: Overview & Data Coverage](#module-1-overview--data-coverage)
   - [Module 2: Market Explorer & Schema Dictionary](#module-2-market-explorer--schema-dictionary)
   - [Module 3: Trader Behavior Analysis](#module-3-trader-behavior-analysis)
   - [Module 4: Positioning Dynamics & Flow Decomposition](#module-4-positioning-dynamics--flow-decomposition)
   - [Module 5: Statistical Research & Econometrics](#module-5-statistical-research--econometrics)
   - [Module 6: Information Content & Event Studies](#module-6-information-content--event-studies)
   - [Module 7: Applications & Knowledge Base](#module-7-applications--knowledge-base)
   - [Module 8: Research Report Workspace](#module-8-research-report-workspace)
5. [Case Study thực hành: "Một ngày nghiên cứu thị trường Bạc (Silver)"](#5-case-study-thực-hành)
6. [Những sai lầm "chết người" người mới thường mắc phải](#6-những-sai-lầm-chết-người)

---

## 1. BẢN CHẤT COT LÀ GÌ?

### 💡 Khái niệm đơn giản
Nếu giá cả trên biểu đồ nến chỉ cho bạn biết **"giá đang chạy đi đâu"**, thì báo cáo **COT (Commitment of Traders)** của Ủy ban Giao dịch Hàng hóa Tương lai Mỹ (CFTC) giống như một **"bản chụp X-quang dòng tiền"**, cho bạn biết **"ai đang cầm bao nhiêu tiền thật trong thị trường"**.

Hàng tuần vào tối thứ Sáu (giờ Mỹ), CFTC bắt buộc tất cả các tổ chức tài chính lớn nhất thế giới phải khai báo số lượng hợp đồng mua (Long) và bán (Short) mà họ đang nắm giữ tính đến ngày thứ Ba cùng tuần.

### 🎭 4 Nhân vật chính trên thị trường hàng hóa (Disaggregated COT):
1. **Producer / Merchant (Phe Cung - Cầu vật chất thực tế):**
   - *Họ là ai?* Các công ty khai thác mỏ đồng, nông dân trồng ngô, nhà máy chế biến dầu ăn.
   - *Mục đích:* Phòng hộ rủi ro (Hedging). Khi giá lên cao, mỏ đồng sẽ **Bán khống (Short)** để khóa trước giá bán sản lượng tương lai, bảo vệ doanh thu.
2. **Managed Money (Phe Đầu cơ chuyên nghiệp / Smart Money):**
   - *Họ là ai?* Các quỹ phòng hộ (Hedge Funds), quỹ CTA, các chuyên gia quản lý tiền.
   - *Mục đích:* Kiếm lợi nhuận từ biến động giá. Họ thường đánh theo xu hướng lớn (Trend Following).
3. **Swap Dealers (Các ngân hàng tạo lập):**
   - *Họ là ai?* Goldman Sachs, JP Morgan, Morgan Stanley...
   - *Mục đích:* Bán sản phẩm phái sinh cho khách hàng (quỹ hưu trí, ETF vàng/bạc) rồi lên sàn phái sinh mở vị thế đối ứng để cân bằng trạng thái.
4. **Nonreportable (Nhà đầu tư cá nhân nhỏ lẻ - Retail):**
   - Các tài khoản nhỏ có khối lượng dưới ngưỡng bắt buộc khai báo của CFTC.

> ⚠️ **LƯU Ý CỐT LÕI:** Đây là **Trạm nghiên cứu định lượng (Research Lab)** giúp bạn hiểu quy luật vận động của dòng tiền lớn, **KHÔNG PHẢI** là phần mềm tự động bắn tín hiệu Mua/Bán để giao dịch.

---

## 2. CÁCH KHỞI ĐỘNG TRẠM NGHIÊN CỨU

### Cách 1: Nhanh nhất (1-Click)
Mở thư mục `cot_analyze` và **nhấp đúp chuột vào file**:
▶️ `start.bat`

### Cách 2: Chạy bằng Terminal (PowerShell)
```powershell
cd "E:\My\the20\test_strategy\commodity_source\cot_analyze"
streamlit run run_research_lab.py
```
Sau 2–3 giây, trình duyệt web sẽ tự động mở địa chỉ: `http://localhost:8501`.

---

## 3. BỐ CỤC TỔNG QUAN & QUY TẮC CỐT LÕI

Giao diện được thiết kế theo phong cách **Trạm làm việc tài chính định lượng chuyên nghiệp (Dark Terminal Theme)**:
- **Cột Menu bên trái (Sidebar):**
  - Danh sách chọn 8 Module nghiên cứu.
  - Bộ chọn hệ thống báo cáo: **Disaggregated COT** (Mặc định cho Hàng hóa vật chất) hoặc **TFF COT** (Dành cho Tài chính/Tiền tệ/Lãi suất).
  - Bộ chọn tài sản: Đồng (`Copper`), Bạc (`Silver`), Bạch kim (`Platinum`)...
  - Bộ lọc khoảng thời gian nghiên cứu (Date Range Filter).
- **Khu vực hiển thị chính (Main Screen):**
  - Các đồ thị tương tác cao (Plotly): Có thể phóng to, thu nhỏ, rê chuột xem số liệu từng tuần, bật/tắt các đường bằng cách bấm vào chú thích (Legend).

---

## 4. HƯỚNG DẪN CHI TIẾT 8 MODULE (KÈM VÍ DỤ THỰC TẾ)

---

### MODULE 1: OVERVIEW & DATA COVERAGE
*(Tổng quan quy mô dữ liệu & Kiểm soát chất lượng)*

#### 🎯 Mục đích:
Giúp bạn kiểm tra toàn bộ "sức khỏe" và phạm vi của tập dữ liệu trước khi đi vào phân tích: có bao nhiêu tuần dữ liệu, có bị lỗi ngày không, vị thế có cân bằng không.

#### 🔍 Những gì hiển thị trên màn hình:
1. **Thẻ KPI tổng thể:** Hơn 149.000 bản ghi, định dạng `Combined` (Futures + Options).
2. **Tiêu điểm 3 kim loại mục tiêu:**
   - **Đồng (Copper - Mã `085692`):** 461 tuần (2018 đến 2026). Đặc biệt ghi nhận bước chuyển đổi tên ngày 08/02/2022: tên cũ `COPPER-GRADE #1` đổi thành `COPPER- #1`. Khoảng cách chuyển đổi đúng 7 ngày, đảm bảo tính liên tục 100%.
   - **Bạc (Silver - Mã `084691`):** 461 tuần liên tục.
   - **Bạch kim (Platinum - Mã `076651`):** 461 tuần liên tục.
3. **Bảng kiểm định chất lượng (Reconciliation):** Đảm bảo $\sum \text{Long} = \sum \text{Short} = \text{Open Interest}$ và không có số âm vô lý.

> **💡 Ví dụ thực tế:** Khi xem thẻ Copper, bạn sẽ thấy lịch sử dữ liệu không hề bị đứt đoạn năm 2022 dù sàn COMEX đổi tên hợp đồng. Điều này giúp các mô hình backtest không bị lỗi thiếu dữ liệu.

---

### MODULE 2: MARKET EXPLORER & SCHEMA DICTIONARY
*(Bộ lọc quét thị trường & Từ điển CFTC)*

#### 🎯 Mục đích:
- Tra cứu danh bạ hơn 600 thị trường hàng hóa khác nhau (Ngô, Dầu thô, Cà phê, Vàng...).
- Giải nghĩa từng cột trong dữ liệu bằng ngôn ngữ dễ hiểu.

#### 🔍 Cách sử dụng:
- **Tab 1 - Market Screener:** Bạn muốn tìm hợp đồng Bạc? Gõ chữ `Silver` vào ô tìm kiếm $\rightarrow$ Hệ thống sẽ hiện ra: Mã hợp đồng `084691`, sàn `COMEX`, ngày bắt đầu `2018-01-02`, ngày mới nhất `2026-10-27`, độ đầy đủ `100%`.
- **Tab 2 - Schema Dictionary:** Bạn không hiểu cột `M_Money_Positions_Spread_All` là gì? Chọn danh mục `5. Spreading` $\rightarrow$ Hệ thống giải thích: *"Đây là vị thế mua và bán đồng thời ở các tháng kỳ hạn khác nhau của quỹ đầu cơ (chơi chênh lệch giá curve), không được cộng gộp vào vị thế định hướng Outright"*.

---

### MODULE 3: TRADER BEHAVIOR ANALYSIS
*(Phân tích hành vi từng nhóm vị thế & Mức độ tập trung)*

#### 🎯 Mục đích:
Bóc tách hành vi của từng "tay chơi" lớn trên thị trường để xem ai đang mua, ai đang bán và thị trường có bị thâu tóm bởi một vài cá mập hay không.

#### 🔍 3 Công cụ chính:
1. **Individual Trader Deep-Dive:**
   - Xem riêng nhóm **Managed Money** (Quỹ đầu cơ): Đồ thị hiển thị đường Gross Long (xanh lá) và Gross Short (đỏ).
   - Đồ thị Net Position: Cho biết họ đang Mua ròng hay Bán ròng bao nhiêu hợp đồng.
   - Trader Counts: Có bao nhiêu quỹ đang tham gia thị trường này.
2. **Cross-Category Comparison (So sánh đối trọng & Phân tích lượng hóa đa chiều):**
   - Đưa vị thế Net của tất cả các nhóm về dạng chuẩn hóa `% của Open Interest` để so sánh trên cùng hệ quy chiếu.
   - **📈 Overlay Giá giao ngay (Physical Price Overlay):**
     - Cho phép vẽ đè đường giá thực tế (Copper, Silver, Platinum) trực tiếp lên đồ thị vị thế COT.
     - Hỗ trợ 4 chế độ hiển thị:
       * *Raw Settlement Price ($):* Trục Y phụ thể hiện giá thật.
       * *Normalized Scale (0 - 100%):* Đưa toàn bộ biên độ giá về khoảng 0% - 100% để đối chiếu tương quan với % Open Interest.
       * *Z-Score Standardized (σ):* Chuẩn hóa độ lệch chuẩn, đo xem giá đang cao hay thấp hơn bao nhiêu độ lệch chuẩn so với trung bình.
       * *Rebased Index (Base = 100):* Quy mốc thời gian bắt đầu về 100 điểm để đo phần trăm tăng trưởng.
   - **⚡ Positioning Divergence (Chỉ số khoảng cách vị thế đầu cơ vs sản xuất):**
     - Tính khoảng cách (Spread): $\text{Divergence} = \text{Managed Money (\% OI)} - \text{Producer/Merchant (\% OI)}$.
     - Tính toán Z-score chu kỳ 52 tuần (1 năm) và 156 tuần (3 năm) đi kèm dải cảnh báo $\pm 2.0\sigma$.
     - Phân loại trạng thái mất cân đối cấu trúc (*Extreme Speculative Extension - Nguy cơ Short Squeeze*, *Elevated Speculative Dominance*, *Structural Balance*, *Commercial Overhang*).
   - **🔄 Multi-Horizon Rolling Correlation Panel (Bảng tương quan trượt 13W, 26W, 52W):**
     - Tính tương quan Pearson động giữa các nhóm tham gia theo các khung thời gian: 13 tuần (ngắn hạn / 1 quý), 26 tuần (trung hạn / nửa năm), 52 tuần (cấu trúc / 1 năm).
     - Cho phép chọn tính theo **Mức vị thế (Levels % OI)** hoặc **Dòng tiền hàng tuần (Weekly Flow Δ)**.
     - Giúp phát hiện khi nào quy luật phòng hộ truyền thống ($r \approx -0.8$ đến $-0.95$) bị đứt gãy ($r \rightarrow 0$ hoặc đảo chiều dương), báo hiệu biến động thanh khoản bất thường hoặc ép bán tháo (forced deleveraging).
3. **Concentration Analysis (Mức độ tập trung):**
   - Hiển thị tỷ lệ nắm giữ của **Top 4** và **Top 8** thực thể lớn nhất.
   - Nếu Top 4 nắm giữ $> 40\%$ vị thế Short $\rightarrow$ Cảnh báo: Thị trường có tính chất độc quyền nhóm, rủi ro biến động thanh khoản cao nếu 1 trong 4 cá mập này tất toán vị thế.

> **💡 Ví dụ thực tế:** Ở thị trường Bạc (Silver), khi thấy Top 4 Short chiếm tới 45% tổng Open Interest, bạn hiểu rằng chỉ cần 1 ngân hàng lớn mua lại để đóng lệnh Short thì giá Bạc có thể tăng dựng đứng vì thiếu thanh khoản đối ứng.

---

### MODULE 4: POSITIONING DYNAMICS & FLOW DECOMPOSITION
*(Động lực dòng tiền & Phân rã Waterfall kết nối Giá thực tế)*

#### 🎯 Mục đích:
Trả lời câu hỏi sống còn: **"Tuần này phe đầu cơ tăng vị thế Net Long là vì tiền mới nạp vào mua, hay do phe bán tháo chạy cắt lỗ? Giá hàng hóa phản ứng như thế nào sau các cú sốc dòng tiền này?"**

#### 🔍 3 Công cụ phân tích:
1. **Flow Decomposition & Weekly Price Return (Phân rã dòng tiền & Lợi suất giá):**
   - Biểu đồ phân rã trực quan 4 thành phần dòng tiền: *Long Accumulation (Tiền mới mua), Short Covering (Bán cắt lỗ), Long Liquidation (Mua chốt lời/cắt lỗ), New Shorts (Mở vị thế bán mới)*.
   - **Tích hợp Giá thực tế:** Cho phép vẽ đè đường **Lợi suất giá hàng tuần (Weekly Price Return %)** trên trục Y phụ để đối chiếu tức thời mức độ tương thích giữa dòng tiền và biên độ dao động giá.
2. **Positioning vs Price Momentum (Động lượng Vị thế vs Động lượng Giá 4W, 8W, 13W, 26W):**
   - Đo tốc độ luân chuyển vốn qua 4 khung thời gian: 4 tuần (1 tháng), 8 tuần (2 tháng), 13 tuần (1 quý) và 26 tuần (nửa năm).
   - **Đối chiếu Động lượng Giá:** Vẽ trực tiếp đường lợi suất giá cùng kỳ hạn và tính toán **Hệ số tương quan động lượng (Momentum Correlation $r$)** để xác định dòng tiền đang dẫn dắt giá hay giá đang kéo dòng tiền chạy theo.
   - Đo gia tốc dòng tiền (**Acceleration**): Cảnh báo sớm khi dòng tiền bắt đầu suy giảm gia tốc trước khi giá tạo đỉnh/đáy.
3. **Historical Extremes & Price Trajectories (Cực trị Vị thế & Biểu đồ Giá 3 Tầng):**
   - **Đồ thị 3 tầng đồng bộ:** Tầng 1 (Z-Score), Tầng 2 (Percentile), Tầng 3 (Giá kim loại kèm các điểm đánh dấu sự kiện cực trị màu đỏ $Z \ge +2\sigma$ và màu xanh lá $Z \le -2\sigma$).
   - Giúp kiểm chứng trực tiếp bằng mắt: Sau mỗi lần vị thế chạm vùng cực trị lịch sử, giá hàng hóa thực tế đã tiếp diễn xu hướng hay đảo chiều.

> **💡 Ví dụ thực tế:** Tuần này Net Long của Đồng tăng +5.000 hợp đồng. Nhìn vào biểu đồ Decomposition, bạn thấy cột *Long Accumulation = 0*, nhưng cột *Short Covering = +5.000*. Điều này có nghĩa: **Không có đồng tiền mới nào mua vào cả**, giá tăng chỉ vì phe Short đang đóng lệnh. Đây là đà tăng yếu ớt!

---

### MODULE 5: STATISTICAL RESEARCH & ECONOMETRICS
*(Nghiên cứu Thống kê & Kinh tế lượng)*

#### 🎯 Mục đích:
Kiểm tra các thuộc tính toán học nghiêm ngặt của chuỗi dữ liệu (phân phối, độ lệch, tính dừng, tương quan).

#### 🔍 Các kết quả quan trọng:
1. **Bảng thống kê mô tả (Descriptive Stats):**
   - Xem độ lệch (Skewness) và độ nhọn (Kurtosis). Vị thế đầu cơ thường có đuôi béo (*Fat tails*), tức là các sự kiện cực đoan xảy ra thường xuyên hơn phân phối chuẩn Gauss.
2. **Kiểm định tính dừng ADF (Augmented Dickey-Fuller Test):**
   - Nếu kiểm định cho kết quả **Non-Stationary (Không dừng, p-value > 0.05)** ở chuỗi vị thế thô $\rightarrow$ **Kết luận học thuật:** Bạn không được lấy chuỗi này hồi quy trực tiếp với giá (sẽ bị lỗi tương quan ảo - Spurious Regression).
   - Chuyển sang dạng **Weekly First Difference (Sai phân tuần $\Delta$)** $\rightarrow$ Kết quả đạt **Stationary (p-value < 0.01)**, sẵn sàng đưa vào mô hình định lượng.
3. **Tương quan liên hàng hóa (Cross-Commodity):**
   - Xem mức độ đồng pha vị thế giữa Đồng, Bạc và Bạch kim.

---

### MODULE 6: COT & PRICE RELATIONSHIP LAB
*(Phòng thí nghiệm Định lượng Mối quan hệ Vị thế & Giá Hàng hóa — Phase 11)*

#### 🎯 Mục đích:
Đây là trung tâm nghiên cứu chuyên sâu trả lời câu hỏi cốt lõi: **"Vị thế COT chứa đựng bao nhiêu hàm lượng thông tin dự báo giá tương lai, diễn ra ở những chân trời thời gian nào, và có vững chắc qua các chế độ thị trường khác nhau hay không?"**

> 🛡️ **Nguyên tắc Chống Look-Ahead Bias (Bảo đảm Tính chân thực):**
> Vị thế COT đo vào thứ Ba nhưng được công bố vào chiều thứ Sáu (3:30 PM ET). Hệ thống tự động áp dụng quy chuẩn **Publication-Aware Anchor**: Mọi tỷ suất sinh lời tương lai (Forward Returns) đều được tính bắt đầu từ **giá đóng cửa thứ Sáu**, tuyệt đối không dùng giá thứ Ba để tránh thiên kiến nhìn trước tương lai!

#### 🔍 5 Phân hệ nghiên cứu chuẩn tổ chức:
1. **📊 Phân tích Tương quan & Lead-Lag (Trễ - Dẫn dắt):**
   - **Tương quan Dòng tiền ($\Delta$) vs Lợi suất:** Loại bỏ tương quan ảo của chuỗi thô, đo tương quan thực sự kèm khoảng tin cậy 95% Fisher Z.
   - **Hồ sơ Lead-Lag Profile ($\pm 8$ tuần):** Tính tương quan chéo $Corr(\Delta COT_t, Return_{t+k})$ với dải biên ý nghĩa 95% Bartlett:
     * *Phía bên trái ($t-k$W - Màu đỏ):* Giá chạy trước COT $\rightarrow$ Quỹ đầu cơ là **Trend-Follower** (đuổi theo giá).
     * *Ở giữa ($t$ - Màu vàng):* Đồng pha tức thời trong tuần.
     * *Phía bên phải ($t+k$W - Màu xanh):* Vị thế COT dẫn dắt giá tương lai $\rightarrow$ Có **hàm lượng thông tin dự báo**.
2. **📈 Nghiên cứu Lợi suất Tương lai & Sự kiện (Event Studies):**
   - **Phân vị Forward Returns (Quintiles Q1 đến Q5):** Chia thị trường làm 5 nhóm từ Bán mạnh nhất đến Mua mạnh nhất; đo lợi suất kỳ vọng $1W, 2W, 4W, 8W, 13W, 26W$, tỷ lệ thắng (Win Rate %) và kiểm định t-test.
   - **Nghiên cứu Cực trị với Khử trùng lặp (First-Crossing Deduplication):** Lọc bỏ các tuần cực trị liên tiếp nhau để tránh bẫy thống kê giả độc lập, vẽ đường quỹ đạo giá tích lũy (Cumulative Trajectory) sau các cú sốc $|Z| \ge 2\sigma$.
   - **Sự kiện Dòng tiền (Flow Drivers):** So sánh giá sau các pha *Long Accumulation* vs *Short Covering* vs *Liquidation*.
3. **📐 Hồi quy Kinh tế lượng Newey-West HAC & Hệ số Thông tin (IC):**
   - **Hồi quy OLS Chuẩn sai số HAC:** Xử lý triệt để hiện tượng phương sai thay đổi và tự tương quan trong chuỗi thời gian tài chính để tính hệ số dốc $\beta$, t-stat và p-value chuẩn xác.
   - **Hệ số Hạng Spearman (Information Coefficient - IC):** Tính IC Mean, IC Std, và **Tỷ số Thông tin (Information Ratio $IR = Mean / Std$)** đo độ ổn định của tín hiệu vị thế.
   - **Hiệu chỉnh Đa giả thuyết:** Áp dụng thuật toán **Benjamini-Hochberg FDR** và **Bonferroni** để loại trừ các phát hiện ngẫu nhiên khi kiểm tra đồng thời nhiều chân trời thời gian.
4. **🔲 Ma trận Chế độ Thị trường 2D (2D Regime Matrix):**
   - Giao thoa 2 chiều: **Chế độ Vị thế (Extreme Long, Neutral, Extreme Short)** $\times$ **Chế độ Xu hướng Giá (Uptrend vs Downtrend so với MA 50 tuần)**.
   - Thống kê chi tiết số mẫu, Lợi suất kỳ vọng, Tỷ lệ tăng (Win Rate %) và Độ biến động thực tế (*Realized Volatility*).
5. **📋 Kiểm toán Nguồn dữ liệu Giá & Từ điển Ánh xạ:**
   - Minh bạch hóa toàn bộ hồ sơ dữ liệu giá: Hợp đồng tương lai liên tục COMEX High Grade Copper (`HG=F`), Silver (`SI=F`), NYMEX Platinum (`PL=F`), đơn vị tính, hệ số nhân và quy tắc chuyển tháng (Roll methodology).

---

### MODULE 7: APPLICATIONS & KNOWLEDGE BASE
*(Cẩm nang 10 Phương pháp luận Định lượng)*

#### 🎯 Mục đích:
Một cuốn bách khoa toàn thư thu nhỏ giải thích chi tiết 10 chủ đề phân tích vị thế hàng hóa chuẩn tổ chức:
1. *Tâm lý thị trường & Dòng vốn thực tế*
2. *Vị thế đầu cơ (Managed Money)*
3. *Hành vi phòng hộ của nhà sản xuất (Commercial Hedging)*
4. *Phân tích độ đông đúc & Tính dễ vỡ của thanh khoản (Crowded Trades)*
5. *Xác nhận xu hướng bằng Khối lượng mở (Open Interest)*
6. *Nghiên cứu đảo chiều & Squeeze cực trị*
7. *Phân loại chế độ thị trường (Market Regimes)*
8. *Vị thế tương đối giữa các kim loại (Cross-Commodity)*
9. *Phân kỳ giữa Giá và Vị thế (Divergence)*
10. *Rủi ro tập trung của các cá mập lớn (Concentration Risk)*

Mỗi chủ đề đều có: **Khái niệm, Cơ sở kinh tế học, Công thức, Ưu điểm, Nhược điểm và Bẫy sai lầm cần tránh**.

---

### MODULE 8: RESEARCH REPORT WORKSPACE
*(Không gian Biên soạn & Xuất Báo cáo Nghiên cứu)*

#### 🎯 Mục đích:
Giúp nhà phân tích tài liệu hóa kết quả nghiên cứu thành một bản báo cáo định lượng chuẩn mực, có thể tái lập (Reproducible) để gửi cho đồng nghiệp hoặc lưu trữ.

#### 🔍 Cách sử dụng:
1. Điền tiêu đề, câu hỏi nghiên cứu, tóm tắt phương pháp và kết luận thực nghiệm.
2. Bấm nút **"🔨 Compile Research Report"**.
3. Hệ thống sẽ tự động đóng gói báo cáo kèm mã JSON chứa đầy đủ tham số lịch sử (tên tài sản, mã CFTC, số lượng mẫu N, ngày bắt đầu/kết thúc).
4. Bấm **"📥 Download Research Report (.md)"** để tải về máy file Markdown hoàn chỉnh.

---

## 5. CASE STUDY THỰC HÀNH: "MỘT NGÀY NGHIÊN CỨU THỊ TRƯỜNG BẠC (SILVER)"

Hãy tưởng tượng bạn là một chuyên viên phân tích định lượng (Quant Analyst) được giao nhiệm vụ đánh giá thị trường **Bạc (COMEX Silver)**:

1. **Bước 1 (Vào Module 1):** Chọn tài sản `Silver` ở Sidebar $\rightarrow$ Xác nhận thị trường có 461 tuần dữ liệu liên tục, vị thế cân bằng 100%.
2. **Bước 2 (Vào Module 3):** Nhìn vào tab *Cross-Category Comparison* $\rightarrow$ Thấy Managed Money đang nắm Net Long +25.000 hợp đồng, trong khi Commercial Producer đang Short -45.000 hợp đồng để phòng hộ.
3. **Bước 3 (Vào Module 4):**
   - Nhìn biểu đồ *Flow Decomposition* 4 tuần gần nhất: Thấy Net Long tăng nhưng chủ yếu do *Short Covering* chứ không có *Long Accumulation*.
   - Nhìn biểu đồ *Z-Score 3 năm*: Z-Score đang ở mức `+2.15σ` (vượt ngưỡng +2σ) và Percentile đạt `93.5%`.
   - $\rightarrow$ **Phát hiện:** Thị trường Bạc đang rơi vào trạng thái **Crowded Long (Độ đông đúc cực đoan)**.
4. **Bước 4 (Vào Module 6):** Mở tab *Event Study* $\rightarrow$ Kiểm tra các lần trong quá khứ Z-Score Bạc vượt +2σ: Sau 4 tuần, tỷ lệ giá điều chỉnh giảm là 68% với mức giảm trung bình -3.8%.
5. **Bước 5 (Vào Module 8):** Ghi lại phát hiện vào Workspace và tải bản báo cáo: *"Cảnh báo rủi ro vị thế quá mua cực đoan trên thị trường Bạc COMEX"*.

---

## 6. NHỮNG SAI LẦM "CHẾT NGƯỜI" NGƯỜI MỚI THƯỜNG MẮC PHẢI

| Sai lầm phổ biến | Thực tế đúng về mặt định lượng |
| :--- | :--- |
| **1. Nhầm lẫn ngày chốt và ngày công bố (Lookahead Bias)** | Vị thế đo vào **thứ Ba**, nhưng CFTC công bố vào **tối thứ Sáu**. Nếu bạn lấy dữ liệu thứ Ba để phân tích giá thứ Tư, bạn đang "nhìn trước tương lai". Trạm nghiên cứu đã tự động dịch ngày hiệu lực sang **thứ Hai tuần sau** để triệt tiêu lỗi này. |
| **2. Coi Producer bán khống là tín hiệu tiêu cực** | Producer là mỏ khai thác kim loại. Họ bán khống để khóa trước giá bán sản lượng vật chất. Khi giá càng tăng cao, họ càng bán khống mạnh để chốt lời dài hạn cho doanh nghiệp. Đây là phòng hộ, không phải đầu cơ giá xuống. |
| **3. Nghĩ Z-Score > 2 là giá phải quay đầu ngay lập tức** | Ở các siêu chu kỳ tăng trưởng (Super-cycles), vị thế có thể giữ ở mức Z-score > 2 trong nhiều tháng liên tục. Cực trị chỉ cảnh báo "thanh khoản đang mỏng manh", không phải là lệnh bán ngay. |
| **4. Gộp lẫn số liệu của Disaggregated COT và TFF** | Nhóm *Managed Money* ở Disaggregated KHÔNG GIỐNG nhóm *Leveraged Money* ở TFF. Hai báo cáo đo lường hai phân khúc thị trường với tiêu chí phân loại khác nhau, tuyệt đối không được gộp chung. |
| **5. So sánh trực tiếp số lượng hợp đồng thô giữa các mặt hàng** | 1 hợp đồng Đồng = 25.000 pounds, trong khi 1 hợp đồng Bạc = 5.000 ounces. Bạn không thể so sánh "10.000 hợp đồng Đồng nhiều hơn 5.000 hợp đồng Bạc". Luôn luôn phải chuẩn hóa về **`% of Open Interest`** hoặc **`Z-Score`**. |

---
*Tài liệu được biên soạn phục vụ công tác nghiên cứu khoa học dữ liệu và phân tích định lượng cấu trúc thị trường hàng hóa tại COT Data Research Lab.*

