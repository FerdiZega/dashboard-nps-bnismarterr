#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# ======================================================
# STREAMLIT CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard NPS Mentor — BNI",
    layout="wide",
)

# ======================================================
# SUPABASE CONFIG
# ======================================================
SUPABASE_URL = "https://misvoheyqxrlnebprxuf.supabase.co"
SUPABASE_KEY = "sb_publishable_6vPKansxgOEs-vkFSpyAmA_aqmHNFk1"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ======================================================
# UPLOAD DATA → Insert ke Supabase
# ======================================================
st.header("📤 Upload Dataset NPS")

file = st.file_uploader("Upload file CSV/Excel Anda:")

if file and st.button("Upload ke Database"):
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        required_cols = {"id_nps", "person_id", "skor_nps", "kategori", "nama"}
        if not required_cols.issubset(df.columns):
            st.error(f"Dataset harus memiliki kolom: {required_cols}")
            st.stop()

        # Kirim seluruh data ke Supabase
        records = df.to_dict(orient="records")
        supabase.table("nps_data").insert(records).execute()

        st.success("Dataset berhasil di upload ke Supabase ✔")

    except Exception as e:
        st.error(f"Upload gagal: {e}")

st.markdown("---")

# ======================================================
# AMBIL DATA DARI SUPABASE
# ======================================================
st.header("📊 Dashboard Analisis NPS")

try:
    rows = supabase.table("nps_data").select("*").execute().data
    df = pd.DataFrame(rows)

    if df.empty:
        st.warning("Belum ada data di database.")
        st.stop()

except Exception as e:
    st.error("Gagal mengambil data dari Supabase.")
    st.stop()

# ======================================================
# FILTER DASBOR
# ======================================================
kategori_list = ["Semua"] + sorted(df["kategori"].unique())
kategori_selected = st.sidebar.selectbox("Filter kategori:", kategori_list)

df_filtered = df.copy()

if kategori_selected != "Semua":
    df_filtered = df_filtered[df_filtered["kategori"] == kategori_selected]

search = st.sidebar.text_input("Cari nama mentor:")
if search:
    df_filtered = df_filtered[df_filtered["nama"].str.contains(search, case=False)]

# KPI
st.subheader("📈 KPI")

col1, col2, col3 = st.columns(3)
col1.metric("Rata-rata NPS", f"{df_filtered['skor_nps'].mean():.2f}")
col2.metric("Jumlah Mentor", df_filtered["person_id"].nunique())
col3.metric("Total Baris", len(df_filtered))

# Tabel
st.subheader("📄 Data Mentah")
st.dataframe(df_filtered)

# Download Excel
def to_excel(df):
    out = BytesIO()
    df.to_excel(out, index=False, sheet_name="nps_data")
    return out.getvalue()

st.download_button(
    "📥 Download Hasil (Excel)",
    to_excel(df_filtered),
    "nps_filtered.xlsx"
)

