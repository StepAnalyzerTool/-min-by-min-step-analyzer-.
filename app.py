import streamlit as st
import pandas as pd
import json
from io import BytesIO
import pytz

st.set_page_config(page_title="Step Cadence Analyzer", layout="wide")
st.title("Minute-by-Minute Step Cadence Analyzer")
st.markdown("Upload minute-level Fitbit JSON exports to automatically reconstruct daily timeseries and calculate cadence bands/MVPA.")

st.sidebar.header("1. Settings")
timezone = st.sidebar.selectbox(
    "Select Timezone (Handles DST)", 
    ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "UTC"]
)

st.sidebar.header("2. Participant Information")
manual_participant_id = st.sidebar.text_input("Enter Participant ID", value="Participant_1")

st.sidebar.header("3. Cadence Thresholds (spm)")
st.sidebar.markdown("Adjust the lower limits for each band if needed.")
band2 = st.sidebar.number_input("Band 2 (Incidental) lower limit", value=1)
band3 = st.sidebar.number_input("Band 3 (Sporadic) lower limit", value=20)
band4 = st.sidebar.number_input("Band 4 (Purposeful) lower limit", value=40)
band5 = st.sidebar.number_input("Band 5 (Slow) lower limit", value=60)
band6 = st.sidebar.number_input("Band 6 (Medium) lower limit", value=80)
band7 = st.sidebar.number_input("Band 7 / MPA (Brisk) lower limit", value=100)
band8 = st.sidebar.number_input("Band 8 / VPA (Faster) lower limit", value=120)

st.sidebar.header("4. Data Upload")
uploaded_files = st.sidebar.file_uploader(
    "Upload Fitbit JSON files", 
    type=['json'], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"### Processing {len(uploaded_files)} file(s) for {manual_participant_id}...")
    
    all_raw_dfs = []

    # 1. READ ALL FILES AND COMBINE FIRST
    for file in uploaded_files:
        data = json.load(file)
        if not data:
            continue
            
        temp_df = pd.DataFrame(data)
        temp_df['value'] = temp_df['value'].astype(int)
        temp_df['dateTime'] = pd.to_datetime(temp_df['dateTime'])
        all_raw_dfs.append(temp_df)
        
    if all_raw_dfs:
        # Combine everything into one master dataframe
        df = pd.concat(all_raw_dfs)
        
        # Drop duplicate timestamps in case files overlap exactly
        df = df.drop_duplicates(subset=['dateTime'])
        
        # Localize timezone
        df = df.set_index('dateTime').tz_localize(timezone, ambiguous=True, nonexistent='shift_forward')
        df = df[df.index.notna()]
        
        unique_dates = df.index.normalize().unique()
        participant_full_timeseries = []

        # 2. RECONSTRUCT CONTINUOUS TIMELINES PER DAY
        for date in unique_dates:
            if pd.isna(date):
                continue
                
            daily_index = pd.date_range(
                start=date, 
                end=date + pd.Timedelta(days=1) - pd.Timedelta(minutes=1), 
                freq='min', 
                tz=timezone
            )
            
            day_data = df[df.index.normalize() == date]
            day_data = day_data[~day_data.index.duplicated(keep='first')]
            
            day_full = day_data.reindex(daily_index, fill_value=0)
            
            day_full['Participant_ID'] = manual_participant_id
            day_full['Date'] = date.date()
            day_full['Time'] = day_full.index.time
            day_full = day_full.rename(columns={'value': 'Steps'})
            
            participant_full_timeseries.append(day_full)

        part_df = pd.concat(participant_full_timeseries)
        
        # 3. CALCULATE BANDS AND SUMMARIES
        bins = [-1, band2-1, band3-1, band4-1, band5-1, band6-1, band7-1, band8-1, 9999]
        labels = [
            'Band 1 (0)', 
            f'Band 2 ({band2}-{band3-1})', 
            f'Band 3 ({band3}-{band4-1})', 
            f'Band 4 ({band4}-{band5-1})', 
            f'Band 5 ({band5}-{band6-1})', 
            f'Band 6 ({band6}-{band7-1})', 
            f'Band 7 / MPA ({band7}-{band8-1})', 
            f'Band 8 / VPA ({band8}+)'
        ]
        
        part_df['Cadence_Band'] = pd.cut(part_df['Steps'], bins=bins, labels=labels)
        
        summary = part_df.groupby(['Participant_ID', 'Date', 'Cadence_Band'], observed=False).size().unstack(fill_value=0)
        summary = summary.reindex(columns=labels, fill_value=0)
        
        summary['Total_MPA_Minutes'] = summary[labels[6]]
        summary['Total_VPA_Minutes'] = summary[labels[7]]
        summary['Total_MVPA_Minutes'] = summary['Total_MPA_Minutes'] + summary['Total_VPA_Minutes']
        summary['Total_Daily_Steps'] = part_df.groupby(['Participant_ID', 'Date'])['Steps'].sum()
        
        column_order = [
            'Total_Daily_Steps',
            'Total_MPA_Minutes',
            'Total_VPA_Minutes',
            'Total_MVPA_Minutes',
            labels[0], labels[1], labels[2], labels[3], 
            labels[4], labels[5], labels[6], labels[7]
        ]
        
        final_summary = summary[column_order].reset_index()
        final_summary = final_summary.sort_values(by='Date')
        
        final_min_by_min = part_df[['Participant_ID', 'Date', 'Time', 'Steps', 'Cadence_Band']]

        st.success("Analysis Complete!")
        st.write("### Daily Summary Preview")
        st.dataframe(final_summary)

        col1, col2 = st.columns(2)
        with col1:
            csv_summary = final_summary.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Daily Summaries (CSV)", data=csv_summary, file_name=f"{manual_participant_id}_Daily_Summaries.csv", mime="text/csv")
        with col2:
            csv_min_by_min = final_min_by_min.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Minute-by-Minute Data (CSV)", data=csv_min_by_min, file_name=f"{manual_participant_id}_Min_by_Min.csv", mime="text/csv")
