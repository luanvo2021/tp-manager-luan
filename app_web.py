import streamlit as st
import gspread
import requests
import base64
from datetime import datetime
import pandas as pd
import re

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Quản lý Lệnh Cạp - Luan", layout="wide")

# API Key ImgBB của bạn
IMGBB_API_KEY = "38c76e7f06864f01eb8ea9a5e011c4ae" 

# --- 2. KẾT NỐI GOOGLE SHEETS BẰNG SECRETS ---
def authenticate_sheets():
    try:
        # Nếu đang chạy trên Streamlit Cloud (tìm thấy két sắt Secrets)
        if "gcp_service_account" in st.secrets:
            credentials = dict(st.secrets["gcp_service_account"])
            return gspread.service_account_from_dict(credentials)
        # Nếu đang chạy test trên máy tính cá nhân (tìm file json vật lý)
        else:
            return gspread.service_account(filename="service_account.json")
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        return None

gc = authenticate_sheets()

# --- 3. HÀM UPLOAD ẢNH LÊN IMGBB ---
def upload_to_imgbb(file):
    if file is None: return ""
    try:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64.b64encode(file.read()).decode('utf-8'),
        }
        res = requests.post(url, payload)
        res_data = res.json()
        if res_data['status'] == 200:
            return res_data['data']['url']
        return ""
    except:
        return ""

# --- 4. GIAO DIỆN NHẬP LIỆU ---
st.title("🏗️ Hệ Thống Quản Lý Lệnh Cạp")
st.markdown("---")

st.sidebar.header("Cài đặt")
sheet_name_input = st.sidebar.text_input("Tên file Google Sheet", value="Demo_QuanLy")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📝 Thông tin chi tiết")
        lenh_cap = st.text_input("Lệnh Cạp")
        ngay_nhap = st.date_input("Ngày", datetime.now())
        thoi_gian = st.time_input("Thời gian", datetime.now().time())
        cong_ty = st.text_input("Công Ty")
        so_tau = st.text_input("Số tàu")
        kl_cap = st.number_input("Khối lượng (KL) cạp", min_value=0.0, step=0.1)
        noi_dung = st.text_area("Nội dung", height=100)

    with col2:
        st.subheader("📸 Hình ảnh & Chứng từ")
        img1 = st.file_uploader("Ảnh số hiệu tàu (Bắt đầu)", type=['jpg','png','jpeg'])
        img2 = st.file_uploader("Ảnh kết thúc cạp (Kết thúc)", type=['jpg','png','jpeg'])
        img3 = st.file_uploader("Ảnh Phiếu giao nhận", type=['jpg','png','jpeg'])
        img4 = st.file_uploader("Chứng từ đo đạc (Nếu có)", type=['jpg','png','jpeg'])

# --- 5. XỬ LÝ LƯU DỮ LIỆU ---
st.markdown("---")
if st.button("🚀 XÁC NHẬN CẬP NHẬT LÊN SHEET", use_container_width=True):
    if not lenh_cap:
        st.warning("Vui lòng nhập Lệnh Cạp!")
    elif gc is None:
        st.error("Không thể kết nối với Google Sheets. Vui lòng kiểm tra lại cấu hình tài khoản (Secrets/JSON).")
    else:
        with st.spinner('Đang upload ảnh và ghi dữ liệu...'):
            try:
                # Upload ảnh
                link1 = upload_to_imgbb(img1)
                link2 = upload_to_imgbb(img2)
                link3 = upload_to_imgbb(img3)
                link4 = upload_to_imgbb(img4)

                # Rút gọn link
                f_link1 = f'=HYPERLINK("{link1}"; "Xem ảnh")' if link1 else ""
                f_link2 = f'=HYPERLINK("{link2}"; "Xem ảnh")' if link2 else ""
                f_link3 = f'=HYPERLINK("{link3}"; "Xem ảnh")' if link3 else ""
                f_link4 = f'=HYPERLINK("{link4}"; "Xem ảnh")' if link4 else ""

                # Kết nối Sheet
                sh = gc.open(sheet_name_input)
                ws = sh.worksheet("Data1")
                all_vals = ws.get_all_values()
                
                # STT tự động (Max + 1)
                numeric_stt = []
                for row_data in all_vals[1:]:
                    val = str(row_data[0]).strip()
                    if val:
                        clean = re.sub(r'[^\d]', '', val)
                        if clean: numeric_stt.append(int(clean))
                stt_moi = (max(numeric_stt) + 1) if numeric_stt else 1

                # Tạo dòng dữ liệu
                final_row = [
                    stt_moi,            # Cột A
                    lenh_cap,           # Cột B
                    ngay_nhap.strftime("%d/%m/%Y"), # Cột C
                    thoi_gian.strftime("%H:%M"),    # Cột D
                    cong_ty,            # Cột E
                    so_tau,             # Cột F
                    kl_cap,             # Cột G
                    noi_dung,           # Cột H
                    f_link1,            # Cột I: Ảnh số hiệu
                    f_link2,            # Cột J: Ảnh kết thúc
                    f_link3,            # Cột K: Ảnh phiếu
                    f_link4             # Cột L: Chứng từ đo
                ]

                # Chèn vào hàng số 2
                ws.insert_row(final_row, index=2, value_input_option='USER_ENTERED')
                
                st.success(f"✅ Đã lưu thành công dữ liệu STT {stt_moi} vào Sheet Data1!")
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
