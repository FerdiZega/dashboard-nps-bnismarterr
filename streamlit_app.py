#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO
import altair as alt

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
# FUNGSI UPLOAD (CHUNK METHOD)
# ======================================================
def upload_in_chunks(df, table_name, chunk_size=5000):
    records = df.to_dict("records")
    total = len(records)

    progress = st.progress(0, text="Mengupload data...")

    for i in range(0, total, chunk_size):
        chunk = records[i:i+chunk_size]
        supabase.table(table_name).insert(chunk).execute()

        progress.progress(
            min(1.0, (i + chunk_size) / total),
            text=f"Uploading... {min(i+chunk_size, total)} / {total} rows"
        )

    progress.progress(1.0, text="Upload selesai!")

# ======================================================
# UPLOAD DATASET USER
# ======================================================
st.header("📤 Upload Dataset NPS")

file = st.file_uploader("Upload file CSV/Excel Anda:")

if file and st.button("Upload ke Database"):
    try:
        # Baca file sesuai format
        if file.name.endswith(".csv"):
            df = pd.read_csv(file, low_memory=False)
        else:
            df = pd.read_excel(file)

        # Validasi kolom dataset
        required_cols = {"id_nps", "person_id", "skor_nps", "kategori", "nama"}
        if not required_cols.issubset(df.columns):
            st.error(f"Dataset harus memiliki kolom: {required_cols}")
            st.stop()

        # Upload dalam batch
        upload_in_chunks(df, "nps_data", chunk_size=5000)

        st.success("Dataset berhasil di-upload ke Supabase ✔")

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

# 🔧 Konversi skor_nps ke numerik (WAJIB untuk grafik)
df["skor_nps"] = pd.to_numeric(df["skor_nps"], errors="coerce")

# ======================================================
# FILTER & ANALISIS
# ======================================================
kategori_list = ["Semua"] + sorted(df["kategori"].unique())
kategori_selected = st.sidebar.selectbox("Filter kategori:", kategori_list)

df_filtered = df.copy()

if kategori_selected != "Semua":
    df_filtered = df_filtered[df_filtered["kategori"] == kategori_selected]

search = st.sidebar.text_input("Cari nama mentor:")
if search:
    df_filtered = df_filtered[df_filtered["nama"].str.contains(search, case=False)]

# ======================================================
# KPI
# ======================================================
st.subheader("📈 KPI")

col1, col2, col3 = st.columns(3)
col1.metric("Rata-rata NPS", f"{df_filtered['skor_nps'].mean():.2f}")
col2.metric("Jumlah Mentor", df_filtered["person_id"].nunique())
col3.metric("Total Baris", len(df_filtered))

# ======================================================
# GRAFIK 1 – Distribusi Skor NPS
# ======================================================
st.subheader("📊 Distribusi Skor NPS")

try:
    chart1 = (
        alt.Chart(df_filtered)
        .mark_bar(color="#4a90e2")
        .encode(
            x=alt.X("skor_nps:Q", bin=alt.Bin(maxbins=20), title="Skor NPS"),
            y="count():Q",
        )
    )
    st.altair_chart(chart1, use_container_width=True)
except:
    st.info("Grafik tidak bisa dibuat. Pastikan skor_nps bertipe angka.")

# ======================================================
# GRAFIK 2 – Jumlah Mentor per Kategori
# ======================================================
st.subheader("📊 Jumlah Mentor per Kategori")

try:
    chart2 = (
        alt.Chart(df_filtered)
        .mark_bar(color="#f39c12")
        .encode(
            x=alt.X("kategori:N"),
            y=alt.Y("count():Q"),
        )
    )
    st.altair_chart(chart2, use_container_width=True)
except:
    st.info("Grafik gagal dibuat.")

# ======================================================
# GRAFIK 3 – Rata-rata NPS per Mentor (Top 20)
# ======================================================
st.subheader("📊 Rata-rata NPS per Mentor (Top 20)")

try:
    df_avg = (
        df_filtered.groupby("nama")["skor_nps"]
        .mean()
        .reset_index()
        .sort_values("skor_nps", ascending=False)
        .head(20)
    )

    chart3 = (
        alt.Chart(df_avg)
        .mark_bar(color="#2ecc71")
        .encode(
            x=alt.X("skor_nps:Q", title="Rata-rata Skor NPS"),
            y=alt.Y("nama:N", sort="-x"),
        )
    )

    st.altair_chart(chart3, use_container_width=True)
except:
    st.info("Grafik gagal dibuat.")

# ======================================================
# TABEL DATA
# ======================================================
st.subheader("📄 Data Mentah")
st.dataframe(df_filtered)

# ======================================================
# DOWNLOAD EXCEL
# ======================================================
def to_excel(df):
    out = BytesIO()
    df.to_excel(out, index=False, sheet_name="nps_data")
    return out.getvalue()

st.download_button(
    "📥 Download Hasil (Excel)",
    to_excel(df_filtered),
    "nps_filtered.xlsx"
)
