import streamlit as st
import pandas as pd
import json
import pytz
import hashlib

st.set_page_config(page_title="The FITS Tool", layout="wide")
st.title("The FITS Tool")
st.subheader("Fitbit Intensity, Timing, and Steps Tool")

# --- INSTRUCTIONS SECTION ---
st.markdown("""
This tool processes raw, minute-by-minute step data exported from Fitbit devices and calculates daily physical activity summaries based on user-selected cadence bands. It also produces a minute-level step log, an hourly steps summary, and a red-flag summary designed to help researchers identify days that may warrant review for incomplete data coverage.
""")
st.markdown("**📋 How to Use This Tool**")

with st.expander("Step 1: Export Your Fitbit Data", expanded=False):
    st.markdown("""
**Google Takeout (as of November 2026)**

1. Open [Google Takeout](https://takeout.google.com/) and sign in with the Google Account
   associated with the participant's Fitbit.
2. Deselect the other Google products and select **Google Health**.
3. Follow [Google's download instructions](https://support.google.com/accounts/answer/3024190)
   to create and download the archive. Choose **ZIP** as the archive file type.
4. Unzip the downloaded archive and open **"Physical Activity_GoogleData"**.
5. Open the **"Steps"** subfolder and locate the **"steps_YYYY-MM-DD.csv"** files.

**Legacy Fitbit Files**

For files previously downloaded through Fitbit, use the **"steps-YYYY-MM-DD.json"**
files from the **"Physical Activity"** folder in the unzipped archive.
    """)

with st.expander("Step 2: Configure Settings", expanded=False):
    st.markdown("""
The Fitbit step files use **Coordinated Universal Time (UTC)**. Use the options on the
**left side of the page** to choose how timestamps are grouped into local days and hours:

- **A. Timezone:** Select the timezone for the participant's location during data collection.
  Indicate whether that location observes daylight saving time. If it does, the tool applies
  the appropriate offset for each date automatically; do not change this choice just because
  a particular date falls in winter. If it does not, the tool uses standard time throughout.
  Choose UTC to keep the original UTC dates and times. Review and confirm the displayed settings.
- **B. Participant Information:** Enter a unique Participant ID. This label will appear
  in the output files.
- **C. Intensity Thresholds (spm):** Adjust the thresholds if your study uses different
  moderate physical activity (MPA) or vigorous physical activity (VPA) criteria.
  Defaults are MPA ≥100 steps/min and VPA ≥130 steps/min.²
- **D. Cadence Band Thresholds (spm):** Adjust the thresholds if your study uses custom
  cadence bands. Default band names and thresholds follow Tudor-Locke et al.¹
- **E. Data Upload:** Upload the participant's step files as described in Step 3.

Fitbit minute-level step timestamps are interpreted as UTC and converted to the confirmed
participant timezone before daily and hourly summaries are calculated. Daylight-saving
adjustments follow your selected setting. The dates available for selection may change when
you change these settings.
    """)

with st.expander("Step 3: Upload Files and Select the Analysis Dates", expanded=False):
    st.markdown("""
Upload files for one participant and one data source at a time. Avoid uploading
overlapping exports of the same records.

Upload JSON or CSV step files for the participant using **E. Data Upload** in the sidebar.
After the files are read and converted to local time, the app will display the earliest
and latest available dates. Select the intended analysis start and end dates, then confirm
the range. All daily and detailed exports retain the full selected date range.

Choose whether to **review red flags and/or exclude individual days**. If Yes,
review the table, check **Exclude** beside dates you want to omit from participant
averages, and optionally enter an exclusion reason. **Include all dates** overrides
individual exclusions. Flags prompt review; they do not establish nonwear or automatically
exclude dates. Define and report your study's inclusion criteria.

If No, all dates are included and the on-screen review is skipped. A Red Flag Summary
is still provided among the downloads. When ready, click **Yes — prepare downloadable files**.
Five download buttons then appear one per row, each with expandable calculation and output details.
Changing settings or exclusion decisions requires preparing the files again.

Exclusions affect only **Participant Averages**. Daily and detailed exports retain every date;
the Daily and Red Flag summaries record inclusion decisions and reasons. Averages give each
included day equal weight and omit NA separately for each measure, reporting its contributing-day
count. Recorded zeros count; missing values are never replaced with zero.

Missing minutes are exported as **NA** (no record in the source file), for both
JSON and CSV inputs. Explicit recorded zeros remain **0**. Missing records do
not establish inactivity or nonwear. Totals and cadence/intensity minutes use
recorded values only; recorded/missing minute counts show how much of each
period is represented. A period with no records has NA activity measures.
Zero-step intervals include only explicit zeros and are interrupted by NA.
Step-positive minutes are recorded minutes with more than zero steps.
Step-only records are not used to estimate wear time.

MPA steps sum counts in minutes at or above the MPA threshold but below VPA.\n    VPA steps sum counts in minutes at or above VPA. MVPA steps are MPA plus VPA steps.\n    These are recorded-step totals, not estimates for missing minutes.\n\n    **Additional daily calculations:** Steps within a cadence band are the sum of
recorded step counts for minutes in that band. Peak 1-, 30-, and 60-minute
cadence are the means of the highest 1, 30, or 60 recorded minute-level step
counts, respectively (steps/min). These minutes need not be consecutive.
Explicit recorded zeros are eligible; missing minutes are excluded and never
replaced with zero. A peak is NA when fewer than the required number of recorded
minutes are available. These additions were informed by
[stepmetrics](https://github.com/jhmigueles/stepmetrics)
(Migueles, *stepmetrics: Calculate Step and Cadence Metrics from Wearable Data*,
[doi:10.5281/zenodo.7858094](https://doi.org/10.5281/zenodo.7858094)).

Five output files are provided:
- 📄 **Participant Averages (CSV):** Mean daily measures across researcher-selected dates, with contributing-day counts and selection totals
- 📄 **Daily Summary (CSV):** Total steps; minutes and steps in each cadence band; step-positive minutes; MPA, VPA, and total MVPA minutes and steps; and peak 1-, 30-, and 60-minute cadence per calendar day
- 📄 **Minute-by-Minute Log (CSV):** A complete chronological record of the total steps recorded in each minute
- 📊 **Hourly Steps Summary (CSV):** Total steps recorded in each hour of the day
- 🚩 **Red Flag Summary (CSV):** Daily and daypart steps, step-positive minutes,
  recorded and missing minutes, activity span, recorded zero-step diagnostics,
  and exploratory data-coverage indicators
    """)

with st.expander("Step 4: Processing a New Participant", expanded=False):
    st.markdown("""
To prevent data from one participant from carrying over to the next, 
**refresh your browser before uploading files for a new participant.** 
This clears the session and fully resets all settings.
    """)

st.markdown("""
⚠️ *This tool does not store, save, or transmit any uploaded data. All files are 
processed temporarily and deleted automatically when the browser is refreshed or closed.*
""")

with st.expander("References for Default Settings", expanded=False):
    st.markdown("""
¹ Tudor-Locke, C., Camhi, S. M., Leonardi, C., Johnson, W. D.,
Katzmarzyk, P. T., Earnest, C. P., & Church, T. S. (2011). Patterns of adult
stepping cadence in the 2005–2006 NHANES. *Preventive Medicine, 53*(3),
178–181. https://doi.org/10.1016/j.ypmed.2011.06.004

² O'Brien, M. W., Kivell, M. J., Wojcik, W. R., D'Entremont, G.,
Kimmerly, D. S., & Fowles, J. R. (2018). Step rate thresholds associated
with moderate and vigorous physical activity in adults. *International
Journal of Environmental Research and Public Health, 15*(11), 2454.
https://doi.org/10.3390/ijerph15112454
    """)


def peak_cadence(values, minutes):
    """Mean of the top N recorded minutes; do not impute absent minutes."""
    recorded = values.dropna()
    if len(recorded) < minutes:
        return float('nan')
    return recorded.nlargest(minutes).mean()


def build_participant_averages(daily, metric_columns, participant_id, timezone, start, end):
    """Equal-weight daily means; NA omitted separately for each numeric measure."""
    included = daily.loc[daily['Included_in_Participant_Summary']]
    rows = []
    for metric in metric_columns:
        values = included[metric]
        rows.append({
            'Participant_ID': participant_id,
            'Timezone': timezone,
            'Analysis_Start_Date': start,
            'Analysis_End_Date': end,
            'Days_In_Date_Range': len(daily),
            'Included_Days': len(included),
            'Excluded_Days': len(daily) - len(included),
            'Measure': metric,
            'Mean_Per_Day': values.mean(),
            'Contributing_Days': int(values.notna().sum()),
            'Included_Days_With_NA': int(values.isna().sum()),
        })
    return pd.DataFrame(rows)


def read_step_file(file):
    """Read legacy Fitbit JSON or Google Takeout steps CSV (November 2026)."""
    file.seek(0)
    if file.name.lower().endswith('.csv'):
        frame = pd.read_csv(file, dtype=str, encoding='utf-8-sig')
        if not {'timestamp', 'steps', 'data source'}.issubset(frame.columns):
            raise ValueError("CSV requires timestamp, steps, and data source columns.")
        if frame['data source'].dropna().str.strip().nunique() > 1:
            raise ValueError("Multiple data sources found; upload steps from one source at a time.")
        raw_times = frame['timestamp'].str.strip()
        if not raw_times.str.contains(r'(?:Z|[+-]\d{2}:?\d{2})$', na=False).all():
            raise ValueError("CSV timestamps require Z (UTC) or an explicit timezone offset.")
        times = raw_times.map(lambda value: pd.to_datetime(value, errors='raise', utc=True))
        frame = frame.rename(columns={'timestamp': 'dateTime', 'steps': 'value'})
    elif file.name.lower().endswith('.json'):
        data = json.load(file)
        if not isinstance(data, list) or not data:
            raise ValueError("Expected a nonempty list of Fitbit step records.")
        frame = pd.DataFrame(data)
        if not {'dateTime', 'value'}.issubset(frame.columns):
            raise ValueError("JSON requires dateTime and value fields.")
        times = pd.to_datetime(frame['dateTime'], errors='raise', utc=True)
    else:
        raise ValueError("Upload a steps JSON or CSV file.")
    if frame.empty:
        raise ValueError("The file contains no step records.")
    counts = pd.to_numeric(frame['value'], errors='raise')
    if counts.isna().any() or ((counts < 0) | (counts % 1 != 0)).any():
        raise ValueError("Step counts must be nonnegative whole numbers, without blanks.")
    if times.isna().any():
        raise ValueError("Missing timestamps are not supported.")
    if ((times.dt.second != 0) | (times.dt.microsecond != 0) | (times.dt.nanosecond != 0)).any():
        raise ValueError("Expected minute-aligned timestamps.")
    return pd.DataFrame({'dateTime': times, 'value': counts.astype('int64')})


# --- SIDEBAR ---
st.sidebar.header("A. Timezone")
# Standard offsets for the supported timezone choices (minutes east of UTC).
TIMEZONE_SETTINGS = {
    "America/New_York": ("Eastern — America/New_York", -300, True),
    "America/Chicago": ("Central — America/Chicago", -360, True),
    "America/Denver": ("Mountain — America/Denver", -420, True),
    "America/Los_Angeles": ("Pacific — America/Los_Angeles", -480, True),
    "America/Phoenix": ("Arizona — America/Phoenix", -420, False),
    "Pacific/Honolulu": ("Hawaii — Pacific/Honolulu", -600, False),
    "UTC": ("UTC — no local-time conversion", 0, False),
}
st.sidebar.caption("Source step timestamps use UTC. Choose the participant's local timezone, or keep UTC.")
timezone = st.sidebar.selectbox(
    "Select participant timezone", list(TIMEZONE_SETTINGS),
    format_func=lambda name: TIMEZONE_SETTINGS[name][0],
    help="Choose the location during data collection. For locations without seasonal clock changes, turn off daylight saving below."
)
_, standard_offset, seasonal_zone = TIMEZONE_SETTINGS[timezone]
observes_dst = st.sidebar.checkbox(
    "This location observes daylight saving time",
    value=seasonal_zone, disabled=not seasonal_zone, key=f"observes_dst_{timezone}",
    help="Select whether the location observes seasonal clock changes, not whether daylight saving is active today. Date-specific changes are automatic when selected."
)
if observes_dst:
    analysis_timezone = pytz.timezone(timezone)
    timezone_description = f"{timezone}; date-specific daylight-saving adjustments enabled"
else:
    analysis_timezone = pytz.FixedOffset(standard_offset)
    offset_sign = '+' if standard_offset >= 0 else '-'
    offset_hours, offset_minutes = divmod(abs(standard_offset), 60)
    timezone_description = (
        f"{timezone}; fixed UTC{offset_sign}{offset_hours:02d}:{offset_minutes:02d}; no daylight-saving adjustments"
    )
st.sidebar.caption(timezone_description)
timezone_confirmed = st.sidebar.checkbox(
    "I confirm the timezone and daylight-saving settings above",
    value=False, key=f"timezone_confirmed_{timezone}_{observes_dst}"
)

st.sidebar.header("B. Participant Information")
manual_participant_id = st.sidebar.text_input("Enter Participant ID", value="Participant_1")

st.sidebar.header("C. Intensity Thresholds (spm)")
st.sidebar.markdown(
    "Default intensity thresholds are MPA ≥100 spm and VPA ≥130 spm "
    "(O'Brien et al., 2018)."
)
mpa = st.sidebar.number_input("MPA (Moderate Physical Activity) lower limit", value=100)
vpa = st.sidebar.number_input("VPA (Vigorous Physical Activity) lower limit", value=130)

st.sidebar.header("D. Cadence Band Thresholds (spm)")
st.sidebar.markdown(
    "Default band names and thresholds follow Tudor-Locke et al. (2011)."
)
st.sidebar.markdown("---")
b1 = st.sidebar.number_input("Incidental movement lower limit", value=1)
b2 = st.sidebar.number_input("Sporadic movement lower limit", value=20)
b3 = st.sidebar.number_input("Purposeful steps lower limit", value=40)
b4 = st.sidebar.number_input("Slow walking lower limit", value=60)
b5 = st.sidebar.number_input("Medium walking lower limit", value=80)
b6 = st.sidebar.number_input("Brisk walking lower limit", value=100)
b7 = st.sidebar.number_input("Faster locomotion/ambulation lower limit", value=120)

st.sidebar.header("E. Data Upload")
uploaded_files = st.sidebar.file_uploader(
    "Upload Fitbit JSON or Google Takeout steps CSV files",
    type=['json', 'csv'],
    accept_multiple_files=True
)

# Hour labels used in the hourly CSV output (hour 0 = midnight to 1 a.m.)
hour_labels = [
    "12:00-1:00 AM", "1:00-2:00 AM", "2:00-3:00 AM", "3:00-4:00 AM",
    "4:00-5:00 AM", "5:00-6:00 AM", "6:00-7:00 AM", "7:00-8:00 AM",
    "8:00-9:00 AM", "9:00-10:00 AM", "10:00-11:00 AM", "11:00 AM-12:00 PM",
    "12:00-1:00 PM", "1:00-2:00 PM", "2:00-3:00 PM", "3:00-4:00 PM",
    "4:00-5:00 PM", "5:00-6:00 PM", "6:00-7:00 PM", "7:00-8:00 PM",
    "8:00-9:00 PM", "9:00-10:00 PM", "10:00-11:00 PM", "11:00 PM-12:00 AM"
]


DAYPARTS = ["Overnight", "Morning", "Afternoon", "Evening"]


def format_clock(timestamp):
    """Format a timestamp as, for example, 6:33 p.m."""
    hour = timestamp.hour % 12 or 12
    suffix = "a.m." if timestamp.hour < 12 else "p.m."
    return f"{hour}:{timestamp.minute:02d} {suffix}"


def build_red_flag_summary(part_df, participant_id):
    """Build the exploratory daily/daypart data-coverage summary."""
    red_flag_df = part_df[['Date', 'Steps']].copy()
    red_flag_df['Daypart'] = pd.cut(
        red_flag_df.index.hour,
        bins=[-1, 5, 11, 17, 23],
        labels=DAYPARTS
    )
    red_flag_df['Active_Minute'] = red_flag_df['Steps'].gt(0).astype(int)

    # Only explicit zeros form zero-step runs. Missing minutes break runs.
    zero_step = red_flag_df['Steps'].eq(0)
    consecutive_minute = red_flag_df.index.to_series().diff().eq(pd.Timedelta(minutes=1))
    run_start = (~zero_step) | (~consecutive_minute)
    run_id = run_start.cumsum()
    zero_run_lengths = zero_step.groupby(run_id).transform('sum')
    red_flag_df['Zero_Step_Run_ID'] = run_id.where(zero_step)
    red_flag_df['Zero_Step_Run_Length'] = zero_run_lengths.where(zero_step, 0)
    red_flag_df['Prolonged_Zero_Step'] = (
        zero_step & zero_run_lengths.ge(90)
    ).astype(int)
    red_flag_df['Recorded_Minute'] = red_flag_df['Steps'].notna().astype(int)
    red_flag_df['Missing_Minute'] = red_flag_df['Steps'].isna().astype(int)

    dates = sorted(red_flag_df['Date'].unique())
    rows = []
    for day_number, date_value in enumerate(dates, start=1):
        day_df = red_flag_df[red_flag_df['Date'] == date_value]
        steps_by_part = (
            day_df.groupby('Daypart', observed=False)['Steps']
            .sum(min_count=1).reindex(DAYPARTS)
        )
        active_by_part = (
            day_df.groupby('Daypart', observed=False)['Active_Minute']
            .sum().reindex(DAYPARTS, fill_value=0).astype(int)
        )
        recorded_by_part = day_df.groupby('Daypart', observed=False)['Recorded_Minute'].sum().reindex(DAYPARTS, fill_value=0)
        missing_by_part = day_df.groupby('Daypart', observed=False)['Missing_Minute'].sum().reindex(DAYPARTS, fill_value=0)
        active_by_part = active_by_part.where(recorded_by_part.gt(0))
        active_rows = day_df[day_df['Steps'] > 0]
        if active_rows.empty:
            activity_span_label = ""
            activity_span_minutes = None
        else:
            first_active = active_rows.index[0]
            last_active = active_rows.index[-1]
            activity_span_label = (
                f"{format_clock(first_active)}–{format_clock(last_active)}"
            )
            activity_span_minutes = int(
                (last_active - first_active).total_seconds() // 60
            )

        total_recorded = int(recorded_by_part.sum())
        total_missing = int(missing_by_part.sum())
        total_steps = day_df['Steps'].sum(min_count=1)
        total_active = active_by_part.sum(min_count=1)
        active_dayparts = int((active_by_part > 0).sum())
        no_records_day = total_recorded == 0
        zero_steps_day = total_steps == 0 if total_recorded else None

        zero_rows = day_df.loc[
            day_df['Zero_Step_Run_ID'].notna(),
            ['Zero_Step_Run_ID', 'Zero_Step_Run_Length']
        ]
        zero_run_minutes_in_day = (
            zero_rows.groupby('Zero_Step_Run_ID').size()
            if not zero_rows.empty else pd.Series(dtype='int64')
        )
        longest_zero_step_interval = (
            int(zero_run_minutes_in_day.max())
            if not zero_run_minutes_in_day.empty else 0
        )
        prolonged_zero_step_intervals = int(
            zero_rows.loc[
                zero_rows['Zero_Step_Run_Length'].ge(90),
                'Zero_Step_Run_ID'
            ].nunique()
        )

        red_flag_total_steps = bool(total_steps < 1000) if total_recorded else None
        red_flag_one_daypart = active_dayparts == 1 if total_recorded else None
        red_flag_short_span = (
            activity_span_minutes is not None
            and activity_span_minutes < 360
        )
        red_flag_values = [
            no_records_day,
            zero_steps_day,
            red_flag_total_steps,
            red_flag_one_daypart,
            red_flag_short_span,
        ]

        rows.append({
            "Participant_ID": participant_id,
            "Day": day_number,
            "Date": date_value,
            "Total_Steps": total_steps,
            **{f"{daypart}_Steps": steps_by_part[daypart] for daypart in DAYPARTS},
            "Total_Step_Positive_Minutes": total_active,
            **{
                f"{daypart}_Step_Positive_Minutes": active_by_part[daypart]
                for daypart in DAYPARTS
            },
            "Expected_Minutes": len(day_df),
            "Recorded_Minutes": total_recorded,
            "Missing_Minutes": total_missing,
            **{f"{daypart}_Recorded_Minutes": int(recorded_by_part[daypart]) for daypart in DAYPARTS},
            **{f"{daypart}_Missing_Minutes": int(missing_by_part[daypart]) for daypart in DAYPARTS},
            "First_Last_Step_Positive_Time": activity_span_label,
            "Activity_Span_Minutes": activity_span_minutes,
            "Number_of_Active_Dayparts": active_dayparts if total_recorded else None,
            "Longest_Zero_Step_Interval_Minutes": longest_zero_step_interval if total_recorded else None,
            "Number_of_Zero_Step_Intervals_90_Minutes_or_Longer": (
                prolonged_zero_step_intervals if total_recorded else None
            ),
            "No_Recorded_Data_Day": no_records_day,
            "Recorded_Zero_Steps_Day": zero_steps_day,
            "Red_Flag_Total_Steps_Under_1000": red_flag_total_steps,
            "Red_Flag_Activity_In_Only_One_Daypart": red_flag_one_daypart,
            "Red_Flag_Activity_Span_Under_6_Hours": red_flag_short_span,
            "Number_of_Red_Flags": sum(bool(flag) for flag in red_flag_values if flag is not None),
            "Any_Red_Flag": any(red_flag_values),
        })

    return pd.DataFrame(rows)


def build_hourly_steps_summary(part_df):
    """Build one CSV row per date with total steps in each labeled hour."""
    hourly_totals = (
        part_df.groupby(["Participant_ID", "Date", "Hour"], as_index=False)["Steps"]
        .sum(min_count=1)
        .rename(columns={"Steps": "Total_Steps"})
    )
    hourly_totals["Hour_Label"] = hourly_totals["Hour"].map(
        dict(enumerate(hour_labels))
    )
    hourly_steps_summary = (
        hourly_totals.pivot(
            index=["Participant_ID", "Date"],
            columns="Hour_Label",
            values="Total_Steps"
        )
        .reindex(columns=hour_labels)
        .reset_index()
    )
    coverage = part_df.groupby(["Participant_ID", "Date", "Hour"])["Steps"].agg(
        Recorded_Minutes="count", Expected_Minutes="size"
    )
    coverage["Missing_Minutes"] = coverage["Expected_Minutes"] - coverage["Recorded_Minutes"]
    for metric in ["Recorded_Minutes", "Missing_Minutes"]:
        wide = coverage[metric].unstack("Hour").reindex(columns=range(24), fill_value=0).fillna(0).astype(int)
        wide.columns = [f"{hour_labels[hour]}_{metric}" for hour in range(24)]
        hourly_steps_summary = hourly_steps_summary.merge(wide.reset_index(), on=["Participant_ID", "Date"])
    hourly_steps_summary.columns.name = None
    return hourly_steps_summary.sort_values("Date")


if uploaded_files and not timezone_confirmed:
    st.warning(
        "⚠️ Confirm the participant's timezone in the sidebar before processing the step files."
    )

elif uploaded_files:
    st.write(f"### Reading {len(uploaded_files)} file(s) for {manual_participant_id}...")

    all_raw_dfs = []

    # 1. READ AND VALIDATE JSON OR CSV STEP RECORDS
    for file in uploaded_files:
        try:
            temp_df = read_step_file(file)
        except Exception as e:
            st.warning(f"⚠️ Skipping `{file.name}`: {e}")
            continue
        all_raw_dfs.append(temp_df)

    if all_raw_dfs:
        df = pd.concat(all_raw_dfs)
        df = df.drop_duplicates(subset=['dateTime'])
        df = df.set_index('dateTime').tz_convert(analysis_timezone)
        df = df[df.index.notna()]

        earliest_available_date = df.index.min().date()
        latest_available_date = df.index.max().date()

        st.write("### Select Analysis Date Range")
        st.info(
            f"Available local dates: **{earliest_available_date:%B %d, %Y}** "
            f"through **{latest_available_date:%B %d, %Y}**"
        )

        date_col1, date_col2 = st.columns(2)
        with date_col1:
            analysis_start_date = st.date_input(
                "Analysis start date",
                value=earliest_available_date,
                min_value=earliest_available_date,
                max_value=latest_available_date
            )
        with date_col2:
            analysis_end_date = st.date_input(
                "Analysis end date",
                value=latest_available_date,
                min_value=earliest_available_date,
                max_value=latest_available_date
            )

        valid_date_range = analysis_start_date <= analysis_end_date
        if not valid_date_range:
            st.error("❌ The analysis start date must be on or before the end date.")

        date_range_confirmed = st.checkbox(
            (
                "I confirm that the analysis should include "
                f"{analysis_start_date:%B %d, %Y} through "
                f"{analysis_end_date:%B %d, %Y}"
            ),
            value=False,
            disabled=not valid_date_range
        )

        if valid_date_range:
            local_dates = pd.Series(df.index.date, index=df.index)
            selected_date_mask = (
                (local_dates >= analysis_start_date)
                & (local_dates <= analysis_end_date)
            )
            selected_df = df.loc[selected_date_mask.to_numpy()]
        else:
            selected_df = df.iloc[0:0]

        if valid_date_range and selected_df.empty:
            st.warning("No source records occur in this range. Outputs will mark every minute as NA.")

        if not date_range_confirmed:
            st.info("Confirm the analysis date range to review days and generate outputs.")
            st.stop()

        df = selected_df
        st.write(
            f"### Processing {analysis_start_date:%B %d, %Y} through "
            f"{analysis_end_date:%B %d, %Y}..."
        )

        unique_dates = pd.date_range(analysis_start_date, analysis_end_date, freq="D", tz=analysis_timezone)
        participant_full_timeseries = []

        # 2. RECONSTRUCT CONTINUOUS TIMELINES PER DAY
        for date in unique_dates:
            if pd.isna(date):
                continue

            daily_index = pd.date_range(
                start=date,
                end=date + pd.DateOffset(days=1) - pd.Timedelta(minutes=1),
                freq='min',
                tz=analysis_timezone
            )

            day_data = df[df.index.normalize() == date]
            day_data = day_data[~day_data.index.duplicated(keep='first')]
            day_full = day_data.reindex(daily_index)

            day_full['Participant_ID'] = manual_participant_id
            day_full['Date'] = date.date()
            day_full['Time'] = day_full.index.time
            day_full = day_full.rename(columns={'value': 'Steps'})

            participant_full_timeseries.append(day_full)

        part_df = pd.concat(participant_full_timeseries)

        # Add hour column for hourly CSV output
        part_df['Hour'] = part_df.index.hour

        # 3. DEFINE TUDOR-LOCKE CADENCE BINS AND INTENSITY CLASSIFICATIONS
        bins = [-1, b1-1, b2-1, b3-1, b4-1, b5-1, b6-1, b7-1, 9999]

        mpa_label = f'MPA ({mpa}-{vpa-1} spm)'
        vpa_label = f'VPA ({vpa}+ spm)'

        labels = [
            'Non-movement (0 spm)',
            f'Incidental movement ({b1}-{b2-1} spm)',
            f'Sporadic movement ({b2}-{b3-1} spm)',
            f'Purposeful steps ({b3}-{b4-1} spm)',
            f'Slow walking ({b4}-{b5-1} spm)',
            f'Medium walking ({b5}-{b6-1} spm)',
            f'Brisk walking ({b6}-{b7-1} spm)',
            f'Faster locomotion ({b7}+ spm)'
        ]

        part_df['Cadence_Band'] = pd.cut(part_df['Steps'], bins=bins, labels=labels)
        part_df['Intensity_Category'] = pd.Series('Below MPA threshold', index=part_df.index).where(part_df['Steps'].notna())
        part_df.loc[
            (part_df['Steps'] >= mpa) & (part_df['Steps'] < vpa),
            'Intensity_Category'
        ] = mpa_label
        part_df.loc[part_df['Steps'] >= vpa, 'Intensity_Category'] = vpa_label

        # 4. CALCULATE DAILY SUMMARIES
        summary = part_df.groupby(
            ['Participant_ID', 'Date', 'Cadence_Band'], observed=False
        ).size().unstack(fill_value=0)
        summary = summary.reindex(columns=labels, fill_value=0)

        daily_intensity = part_df.groupby(['Participant_ID', 'Date']).agg(
            Total_MPA_Minutes=(
                'Steps', lambda values: ((values >= mpa) & (values < vpa)).sum()
            ),
            Total_VPA_Minutes=('Steps', lambda values: (values >= vpa).sum()),
            Total_Step_Positive_Minutes=('Steps', lambda values: (values > 0).sum()),
            Total_MPA_Steps=('Steps', lambda values: values[(values >= mpa) & (values < vpa)].sum()),
            Total_VPA_Steps=('Steps', lambda values: values[values >= vpa].sum())
        )
        for column in ('Total_Step_Positive_Minutes', 'Total_MPA_Steps', 'Total_VPA_Steps'):
            summary[column] = daily_intensity[column]
        summary['Total_MVPA_Steps'] = summary['Total_MPA_Steps'] + summary['Total_VPA_Steps']
        summary['Total_MPA_Minutes'] = daily_intensity['Total_MPA_Minutes']
        summary['Total_VPA_Minutes'] = daily_intensity['Total_VPA_Minutes']
        summary['Total_MVPA_Minutes'] = summary['Total_MPA_Minutes'] + summary['Total_VPA_Minutes']
        summary['Total_Daily_Steps'] = part_df.groupby(['Participant_ID', 'Date'])['Steps'].sum(min_count=1)
        # Step sums use the same cadence assignments as the minute counts.
        band_steps = part_df.groupby(
            ['Participant_ID', 'Date', 'Cadence_Band'], observed=False
        )['Steps'].sum().unstack(fill_value=0).reindex(columns=labels, fill_value=0)
        band_step_columns = [f'Steps: {label}' for label in labels]
        band_steps.columns = band_step_columns
        summary = summary.join(band_steps)
        peak_columns = []
        daily_steps = part_df.groupby(['Participant_ID', 'Date'])['Steps']
        for minutes in (1, 30, 60):
            column = f'Peak_{minutes}_Minute_Cadence_spm'
            peak_columns.append(column)
            summary[column] = daily_steps.agg(
                lambda values, n=minutes: peak_cadence(values, n)
            )

        coverage = part_df.groupby(['Participant_ID', 'Date'])['Steps'].agg(
            Expected_Minutes='size', Recorded_Minutes='count'
        )
        coverage['Missing_Minutes'] = coverage['Expected_Minutes'] - coverage['Recorded_Minutes']
        summary.loc[coverage['Recorded_Minutes'].eq(0), :] = float('nan')
        summary = summary.join(coverage)

        column_order = [
            'Total_Daily_Steps',
            'Expected_Minutes',
            'Recorded_Minutes',
            'Missing_Minutes',
            'Total_Step_Positive_Minutes',
            'Total_MPA_Minutes',
            'Total_MPA_Steps',
            'Total_VPA_Minutes',
            'Total_VPA_Steps',
            'Total_MVPA_Minutes',
            'Total_MVPA_Steps',
        ] + peak_columns + [column for pair in zip(labels, band_step_columns) for column in pair]

        final_summary = summary[column_order].reset_index()
        final_summary = final_summary.sort_values(by='Date')

        final_min_by_min = part_df[
            [
                'Participant_ID',
                'Date',
                'Time',
                'Steps'
            ]
        ].copy()

        # 5. BUILD HOURLY AND RED-FLAG CSV OUTPUTS
        hourly_steps_summary = build_hourly_steps_summary(part_df)
        red_flag_summary = build_red_flag_summary(part_df, manual_participant_id)

        # 6. OPTIONAL REVIEW. Calculations above support review; CSVs are prepared only on request.
        # Reset decisions for different input records, participant, timezone, dates or thresholds.
        review_context = hashlib.sha256(
            pd.util.hash_pandas_object(df[['value']], index=True).values.tobytes()
            + repr((manual_participant_id, timezone, observes_dst, analysis_start_date, analysis_end_date,
                    mpa, vpa, bins)).encode('utf-8')
        ).hexdigest()
        review_choice = st.radio(
            "Would you like to review red flags and/or exclude individual days?",
            ["Yes", "No"], index=None, horizontal=True, key=f"review_choice_{review_context}"
        )
        if review_choice is None:
            st.info("Choose Yes or No to continue.")
            st.stop()
        decisions = red_flag_summary[['Date']].copy()
        decisions['Included_in_Participant_Summary'] = True
        decisions['Exclusion_Reason'] = ''
        if review_choice == "Yes":
            st.subheader("Red Flag Summary and Day Selection")
            st.write("Flags prompt review; they do not establish nonwear or automatically exclude days. You may exclude a day for any study-specific reason.")
            include_all = st.checkbox(
                "Include all dates from the analysis start date through the end date in participant averages",
                value=False, key=f"include_all_v2_{review_context}"
            )
            if include_all:
                st.info("Individual exclusions and notes are locked because Include all dates is checked. Uncheck it to edit the table.")
            else:
                st.info("Check Exclude from averages beside a date to exclude it. Double-click its Exclusion reason cell to type a note, then press Enter. Dates remain included unless you check their exclusion boxes.")
            st.caption(
                "Include all dates overrides individual exclusions. "
                "An exclusion reason is optional. The other four exports retain every date. "
                "Missing minutes are not evidence of inactivity or nonwear."
            )
            review = red_flag_summary.copy()
            flag_labels = {
                'No_Recorded_Data_Day': 'No recorded data',
                'Recorded_Zero_Steps_Day': 'Recorded steps total zero',
                'Red_Flag_Total_Steps_Under_1000': 'Recorded steps below 1,000',
                'Red_Flag_Activity_In_Only_One_Daypart': 'Steps in only one daypart',
                'Red_Flag_Activity_Span_Under_6_Hours': 'First-to-last positive minute span below 6 hours',
            }
            review['Flag_Reasons'] = review.apply(
                lambda row: '; '.join(label for column, label in flag_labels.items()
                                      if pd.notna(row[column]) and bool(row[column])), axis=1
            )
            review.insert(0, 'Exclude_from_Averages', False)
            review.insert(1, 'Exclusion_Reason', '')
            leading_columns = [
                'Exclude_from_Averages', 'Date', 'Exclusion_Reason', 'Flag_Reasons',
                'Total_Steps', 'Recorded_Minutes', 'Missing_Minutes',
                'Total_Step_Positive_Minutes', 'Number_of_Red_Flags',
            ]
            review = review[leading_columns]
            edited_review = st.data_editor(
                review, hide_index=True, use_container_width=True,
                key=f"day_review_v3_{review_context}_{include_all}",
                disabled=True if include_all else [
                    c for c in review.columns if c not in ('Exclude_from_Averages', 'Exclusion_Reason')
                ],
                column_config={
                    'Exclude_from_Averages': st.column_config.CheckboxColumn('Exclude', width='small'),
                    'Date': st.column_config.DateColumn('Date', format='YYYY-MM-DD', width='small'),
                    'Flag_Reasons': st.column_config.TextColumn('Red flag reasons', width='large'),
                    'Exclusion_Reason': st.column_config.TextColumn('Exclusion reason (optional)', width='large'),
                }
            )
            with st.expander("Full red flag reasons (not truncated)", expanded=True):
                flagged = review.loc[review['Flag_Reasons'].ne('')]
                if flagged.empty:
                    st.write("No dates meet the current red flag criteria.")
                for _, row in flagged.iterrows():
                    st.markdown(f"**{row['Date']}** — {row['Flag_Reasons']}")
            decisions = edited_review[['Date', 'Exclude_from_Averages', 'Exclusion_Reason']].copy()
            if include_all:
                decisions['Exclude_from_Averages'] = False
            decisions['Included_in_Participant_Summary'] = ~decisions['Exclude_from_Averages'].fillna(False).astype(bool)
            decisions['Exclusion_Reason'] = decisions['Exclusion_Reason'].fillna('').where(
                ~decisions['Included_in_Participant_Summary'], ''
            )
            decisions = decisions[['Date', 'Included_in_Participant_Summary', 'Exclusion_Reason']]
        else:
            st.info("All dates will be included. A Red Flag Summary will still be available as a download.")
        final_summary = final_summary.merge(decisions, on='Date', validate='one_to_one')
        red_flag_summary = red_flag_summary.merge(decisions, on='Date', validate='one_to_one')
        included_count = int(final_summary['Included_in_Participant_Summary'].sum())
        st.caption(f"{included_count} included day(s); {len(final_summary) - included_count} excluded day(s). Exclusions affect participant averages only.")
        if included_count == 0:
            st.warning("No dates are included. Participant means will be NA with zero contributing days.")
        # Reconfirm after any change to settings, review mode, dates, exclusions or reasons.
        output_context = hashlib.sha256(
            (review_context + review_choice).encode('utf-8')
            + pd.util.hash_pandas_object(decisions, index=False).values.tobytes()
        ).hexdigest()
        if st.session_state.get('prepared_output_context') != output_context:
            st.session_state.pop('prepared_output_context', None)
        st.subheader("Ready to prepare your downloadable analysis files?")
        if st.button("Yes — prepare downloadable files", key=f"prepare_{output_context}", type="primary"):
            st.session_state['prepared_output_context'] = output_context
        if st.session_state.get('prepared_output_context') != output_context:
            st.caption("Review your choices above, then click Yes. Download files have not yet been generated for these choices.")
            st.stop()

        participant_averages = build_participant_averages(
            final_summary, column_order, manual_participant_id, timezone_description,
            analysis_start_date, analysis_end_date
        )
        for output_frame in (final_summary, final_min_by_min, hourly_steps_summary, red_flag_summary):
            output_frame['Analysis_Timezone'] = timezone_description
            output_frame['Daylight_Saving_Observed'] = observes_dst
        st.success("Your five analysis files are ready.")
        st.caption(
            f"Dates are based on {timezone_description}. Daily and detailed outputs retain the full selected range; "
            "only participant averages use your day exclusions. Missing values are exported as NA."
        )
        downloads = [
            ("Daily Summary", final_summary, "Daily_Summaries", """
Daily recorded steps; step-positive minutes; MPA, VPA and MVPA minutes and steps;
minutes and steps in each cadence band; peak 1-, 30- and 60-minute cadence; and coverage counts.
MPA is at least the selected MPA threshold and below VPA; VPA is at least the VPA threshold.
MVPA combines MPA and VPA. Band steps sum the recorded counts within each band.
Peak cadence averages the highest N recorded minute counts, which need not be consecutive.
A peak is NA if fewer than N recorded minutes exist. Recorded zeros remain eligible.
All dates remain, with inclusion decisions and exclusion reasons.
"""),
            ("Minute-by-Minute Log", final_min_by_min, "Min_by_Min", """
Participant ID, local date, local time and steps for every minute in the selected range.
Absent records are NA; explicitly recorded zeros stay zero. Days follow the selected timezone,
with daylight-saving changes only when enabled. Excluded dates remain in this file.
"""),
            ("Hourly Steps Summary", hourly_steps_summary, "Hourly_Steps_Summary", """
Recorded step totals for each local clock hour, with recorded- and missing-minute counts.
Hours with no records have NA totals. A repeated daylight-saving hour is combined under its
clock-hour label when daylight-saving adjustments are enabled. With adjustments disabled,
every selected day has 24 clock hours. Excluded dates remain in this file.
"""),
            ("Red Flag Summary", red_flag_summary, "Red_Flag_Summary", """
Daily and daypart steps, step-positive minutes, data coverage, activity span and explicit-zero
intervals. Flags identify no recorded data, recorded zero-step days, fewer than 1,000 steps,
steps in only one daypart, or an activity span below six hours. These indicators do not establish
nonwear or automatically exclude dates. NA interrupts zero-step intervals. All dates remain,
with your inclusion decisions and exclusion reasons, even when you skip the on-screen review.
"""),
            ("Participant Averages", participant_averages, "Participant_Averages", """
An equally weighted mean of each daily measure across your included dates, including activity
and coverage measures. NA is omitted separately for each measure; recorded zeros count.
Each row reports its contributing-day count, included days with NA, and total included/excluded
days. If no included day has a value, the mean is NA. These averages describe recorded data
and do not estimate activity during missing minutes.
"""),
        ]
        for title, frame, suffix, explanation in downloads:
            st.download_button(
                f"📥 Download {title} (CSV)",
                data=frame.to_csv(index=False, na_rep="NA").encode('utf-8-sig'),
                file_name=f"{manual_participant_id}_{suffix}.csv", mime="text/csv",
                use_container_width=True
            )
            with st.expander(f"About {title}: calculations and output details"):
                st.markdown(explanation)

    else:
        st.error("❌ No valid Fitbit data found in the uploaded files. Please check your files and try again.")



