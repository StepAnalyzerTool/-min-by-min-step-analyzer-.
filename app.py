import streamlit as st
import pandas as pd
import json
from io import BytesIO
import pytz

st.set_page_config(page_title="Step Cadence Analyzer", layout="wide")
st.title("Minute-by-Minute Step Cadence Analyzer")

# --- INSTRUCTIONS SECTION ---
with st.expander("📋 How to Use This Tool", expanded=True):
    st.markdown("""
    This application processes raw, minute-by-minute step data exported from Fitbit devices 
    and automatically calculates daily physical activity summaries based on step cadence bands.
    
    ---
    
    **Step 1: Export Your Fitbit Data**
    
    Visit the [Fitbit Data Export Help Page](https://support.google.com/googlehealth/answer/14236615?hl=en) 
    for step-by-step instructions on downloading your Fitbit data archive. Note that instructions 
    may vary slightly depending on whether the participant signs in with a Google Account or a 
    Fitbit login.
    
    Once downloaded, unzip the archive and locate the **"Physical Activity"** folder. 
    You will be uploading the files named **"steps-YYYY-MM-DD.json"** (e.g., steps-2012-10-01.json) 
    from that folder.
    
    ---
    
    **Step 2: Configure Settings**
    
    Use the sidebar on the left to:
    - Select the **timezone** that matches the participant's location during data collection
    - Enter a unique **Participant ID** (this label will appear in your output files)
    - Adjust the **cadence band thresholds** if your study uses custom step-rate criteria
    (default values are pre-loaded based on published guidelines)
    
    ---
    
    **Step 3: Upload Files and Download Results**
    
    Upload all JSON step files for the participant using the file uploader in the sidebar. 
    The app will automatically process the data and display a preview of the daily summary. 
    Download your results using the buttons that appear below the preview.
    
    Three output files are provided:
    - 📄 **Daily Summary (CSV):** Total steps, minutes in each cadence band, and total MVPA minutes per calendar day
    - 📄 **Minute-by-Minute Log (CSV):** A complete chronological record of step counts and cadence band assignments
    - 📊 **Hourly Analysis (Excel):** Total steps and minutes per cadence band broken down by hour of day, with one tab per band
    
    ---
    
    **Step 4: Processing a New Participant**
    
    To prevent data from one participant from carrying over to the next, 
    **refresh your browser before uploading files for a new participant.** 
    This clears the session and fully resets all settings.
    
    ---
    
    ⚠️ *This tool does not store, save, or transmit any uploaded data. All files are 
    processed temporarily and deleted automatically when the browser is refreshed or closed.*
    """)

# --- SIDEBAR ---
st.sidebar.header("1. Settings")
timezone = st.sidebar.selectbox(
    "Select Timezone (Handles DST)",
    ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "UTC"]
)

st.sidebar.header("2. Participant Information")
manual_participant_id = st.sidebar.text_input("Enter Participant ID", value="Participant_1")

st.sidebar.header("3. Cadence Thresholds (spm)")
st.sidebar.markdown("Most researchers need only MPA and VPA. Adjust Bands 1–5 if your study uses custom step-rate criteria.")
mpa = st.sidebar.number_input("MPA (Moderate Physical Activity) lower limit", value=100)
vpa = st.sidebar.number_input("VPA (Vigorous Physical Activity) lower limit", value=120)
st.sidebar.markdown("---")
b1 = st.sidebar.number_input("Band 1 (Incidental) lower limit", value=1)
b2 = st.sidebar.number_input("Band 2 (Sporadic) lower limit", value=20)
b3 = st.sidebar.number_input("Band 3 (Purposeful) lower limit", value=40)
b4 = st.sidebar.number_input("Band 4 (Slow) lower limit", value=60)
b5 = st.sidebar.number_input("Band 5 (Medium) lower limit", value=80)

st.sidebar.header("4. Data Upload")
uploaded_files = st.sidebar.file_uploader(
    "Upload Fitbit JSON files",
    type=['json'],
    accept_multiple_files=True
)

# Hour labels for Excel output (hour 0 = midnight to 1am)
hour_labels = [
    "12:00-1:00 AM", "1:00-2:00 AM", "2:00-3:00 AM", "3:00-4:00 AM",
    "4:00-5:00 AM", "5:00-6:00 AM", "6:00-7:00 AM", "7:00-8:00 AM",
    "8:00-9:00 AM", "9:00-10:00 AM", "10:00-11:00 AM", "11:00 AM-12:00 PM",
    "12:00-1:00 PM", "1:00-2:00 PM", "2:00-3:00 PM", "3:00-4:00 PM",
    "4:00-5:00 PM", "5:00-6:00 PM", "6:00-7:00 PM", "7:00-8:00 PM",
    "8:00-9:00 PM", "9:00-10:00 PM", "10:00-11:00 PM", "11:00 PM-12:00 AM"
]

if uploaded_files:
    st.write(f"### Processing {len(uploaded_files)} file(s) for {manual_participant_id}...")

    all_raw_dfs = []

    # 1. READ ALL FILES WITH SCHEMA VALIDATION
    for file in uploaded_files:
        try:
            data = json.load(file)
        except Exception:
            st.warning(f"⚠️ Skipping `{file.name}`: Not a valid JSON file.")
            continue

        if not data or not isinstance(data, list):
            st.warning(f"⚠️ Skipping `{file.name}`: File is empty or not in the expected Fitbit format.")
            continue

        temp_df = pd.DataFrame(data)

        if 'dateTime' not in temp_df.columns or 'value' not in temp_df.columns:
            st.warning(f"⚠️ Skipping `{file.name}`: Missing 'dateTime' or 'value' columns. Are you sure this is a steps file?")
            continue

        try:
            temp_df['value'] = temp_df['value'].astype(int)
            temp_df['dateTime'] = pd.to_datetime(temp_df['dateTime'])
        except Exception as e:
            st.warning(f"⚠️ Skipping `{file.name}`: Data formatting error. ({e})")
            continue

        all_raw_dfs.append(temp_df)

    if all_raw_dfs:
        df = pd.concat(all_raw_dfs)
        df = df.drop_duplicates(subset=['dateTime'])
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
                end=date + pd.DateOffset(days=1) - pd.Timedelta(minutes=1),
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

        # Add hour column for hourly Excel output
        part_df['Hour'] = part_df.index.hour

        # 3. DEFINE BINS AND LABELS
        bins = [-1, b1-1, b2-1, b3-1, b4-1, b5-1, mpa-1, vpa-1, 9999]

        mpa_label = f'MPA ({mpa}-{vpa-1} spm)'
        vpa_label = f'VPA ({vpa}+ spm)'

        labels = [
            'Sedentary (0 spm)',
            f'Band 1 - Incidental ({b1}-{b2-1} spm)',
            f'Band 2 - Sporadic ({b2}-{b3-1} spm)',
            f'Band 3 - Purposeful ({b3}-{b4-1} spm)',
            f'Band 4 - Slow ({b4}-{b5-1} spm)',
            f'Band 5 - Medium ({b5}-{mpa-1} spm)',
            mpa_label,
            vpa_label
        ]

        part_df['Cadence_Band'] = pd.cut(part_df['Steps'], bins=bins, labels=labels)

        # 4. CALCULATE DAILY SUMMARIES
        summary = part_df.groupby(
            ['Participant_ID', 'Date', 'Cadence_Band'], observed=False
        ).size().unstack(fill_value=0)
        summary = summary.reindex(columns=labels, fill_value=0)

        summary['Total_MPA_Minutes'] = summary[mpa_label]
        summary['Total_VPA_Minutes'] = summary[vpa_label]
        summary['Total_MVPA_Minutes'] = summary['Total_MPA_Minutes'] + summary['Total_VPA_Minutes']
        summary['Total_Daily_Steps'] = part_df.groupby(['Participant_ID', 'Date'])['Steps'].sum()

        column_order = [
            'Total_Daily_Steps',
            'Total_MPA_Minutes',
            'Total_VPA_Minutes',
            'Total_MVPA_Minutes',
        ] + labels

        final_summary = summary[column_order].reset_index()
        final_summary = final_summary.sort_values(by='Date')

        final_min_by_min = part_df[['Participant_ID', 'Date', 'Time', 'Steps', 'Cadence_Band']]

        # 5. BUILD HOURLY EXCEL OUTPUT
        all_dates = sorted(part_df['Date'].unique())

        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:

            # Tab 1: Total Steps per Hour
            hourly_steps = part_df.groupby(['Date', 'Hour'])['Steps'].sum().unstack(fill_value=0)
            hourly_steps = hourly_steps.reindex(index=all_dates, fill_value=0)
            hourly_steps = hourly_steps.reindex(columns=range(24), fill_value=0)
            hourly_steps.columns = hour_labels
            hourly_steps.reset_index().to_excel(
                writer, sheet_name='Total Steps per Hour', index=False
            )

            # One tab per cadence band
            for label in labels:
                band_data = part_df[part_df['Cadence_Band'] == label]

                if not band_data.empty:
                    hourly_band = band_data.groupby(
                        ['Date', 'Hour']
                    ).size().unstack(fill_value=0)
                else:
                    hourly_band = pd.DataFrame(
                        index=pd.Index(all_dates, name='Date'),
                        columns=range(24),
                        dtype=float
                    ).fillna(0)

                hourly_band = hourly_band.reindex(index=all_dates, fill_value=0)
                hourly_band = hourly_band.reindex(columns=range(24), fill_value=0)
                hourly_band = hourly_band.astype(int)
                hourly_band.columns = hour_labels
                # Excel sheet names max 31 characters
                sheet_name = label[:31]
                hourly_band.reset_index().to_excel(writer, sheet_name=sheet_name, index=False)

        excel_buffer.seek(0)

        # 6. DISPLAY RESULTS AND DOWNLOAD BUTTONS
        st.success("✅ Analysis Complete!")
        st.write("### Daily Summary Preview")
        st.dataframe(final_summary)

        col1, col2, col3 = st.columns(3)
        with col1:
            csv_summary = final_summary.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Daily Summaries (CSV)",
                data=csv_summary,
                file_name=f"{manual_participant_id}_Daily_Summaries.csv",
                mime="text/csv"
            )
        with col2:
            csv_min_by_min = final_min_by_min.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Minute-by-Minute Log (CSV)",
                data=csv_min_by_min,
                file_name=f"{manual_participant_id}_Min_by_Min.csv",
                mime="text/csv"
            )
        with col3:
            st.download_button(
                "📊 Download Hourly Analysis (Excel)",
                data=excel_buffer,
                file_name=f"{manual_participant_id}_Hourly_Analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.error("❌ No valid Fitbit data found in the uploaded files. Please check your files and try again.")
