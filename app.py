import streamlit as st
import pandas as pd
import json
import pytz
import hashlib
from datetime import datetime
from collections import Counter

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
Use the options on the **left side of the page**:

**A. Time Zone**

- The Fitbit step files use **Coordinated Universal Time (UTC)**.
- Select the timezone for the participant's location during data collection and indicate
  whether that location observes daylight saving time. Or choose UTC to keep the original
  UTC dates and times.
- Review and confirm the displayed settings.
    """)
    with st.expander("How timezone selections affect data analysis", expanded=False):
        st.markdown("""
Timezone conversion can move records to a different date or hour, changing daily totals, cadence summaries, flags and participant averages.

- **UTC:** Keeps the original UTC dates and times, without daylight-saving adjustments.
- **Daylight saving selected:** Uses the chosen location's historical timezone rules for each
  record. Select this based on the location during data collection, not whether daylight
  saving is active today. Clock-change days may be shorter or longer than 24 hours.
- **Daylight saving not selected:** Uses the fixed standard-time UTC offset displayed under
  A throughout the analysis. Every day has 24 hours. This offset is based on the selected
  timezone's standard offset in the current year; check the displayed offset for historical
  data or locations whose standard time has changed.

Some locations have started or stopped observing daylight saving time. Choose the setting that applied when the data were collected, not necessarily the setting used today. Selecting timezone settings requires confirmation before summary files are prepared.
        """)
    st.markdown("""
**B. Participant Information**

- Enter a unique Participant ID. This label will appear in the output files.

**C. Intensity Thresholds (spm)**

- Adjust the thresholds if your study uses different moderate physical activity (MPA)
  or vigorous physical activity (VPA) criteria.
- Defaults are MPA ≥100 steps/min and VPA ≥130 steps/min.²

**D. Cadence Band Thresholds (spm)**

- Adjust the thresholds if your study uses custom cadence bands.
- Default band names and thresholds follow Tudor-Locke et al.¹

**E. Data Upload**

- Upload the participant's step files as described in Step 3.
    """)

with st.expander("Step 3: Upload Files", expanded=False):
    st.markdown("""
- Use **E. Data Upload** on the left to upload Google Takeout steps CSV files or older Fitbit JSON files.
- Upload files for one participant and one data source at a time.
- Review the accepted files and any files that could not be used. Remove or replace rejected
  files, or explicitly choose **Continue with accepted files only**. If no files are usable,
  processing stops until you supply a usable file.
    """)
    with st.expander("Recorded zeros, missing minutes, and file formats", expanded=False):
        st.markdown("""
- **Recorded 0:** The tool keeps the value as zero. It counts as a recorded minute with no
  steps and is included in calculations, including the zero-step cadence band and peak cadence.
- **Missing minute:** When a minute has no record in the source file, the tool labels it
  **NA**, rather than zero. It is excluded from activity calculations but counted in
  missing-minute coverage totals. A day with no records has NA activity measures and does
  not contribute to averages of those measures.

**Differences between file formats**

- **Google Takeout CSV (as of November 2026):** Google exports only include minutes with 1 or more steps (positive step counts); minutes with 0 steps are not listed. The tool labels any missing minutes as NA. An absent minute does not distinguish between wearing the Fitbit without taking steps and not wearing it.
- **Older Fitbit JSON:** These files contain recorded zeros as well as positive step counts.
  The tool preserves those zeros and labels any missing minutes as NA.

        """)

with st.expander("Step 4: Select the Analysis Dates", expanded=False):
    st.markdown("""
- Select and confirm your analysis start and end dates. Use **Change dates** to revise them.
- Choose whether to **review red flags and/or exclude individual days**. If Yes, check **Exclude** beside any dates you want to omit and optionally enter a reason.
- Excluded dates are removed from the daily, minute-level, and hourly files and from participant averages. The **Red Flag Summary** retains every date.
    """)
    with st.expander("More about dates, red flags, and exclusions", expanded=False):
        st.markdown("""
- Available dates reflect your selected timezone.
- Red flags identify days that may warrant review. They do not establish nonwear or automatically exclude dates. Use and report your study's inclusion criteria.
- **Include all dates** overrides individual exclusions. Choosing **No** to the review question also includes all dates and skips the on-screen review.
- A **Red Flag Summary** is provided whether or not you review flags on screen.
- The **Red Flag Summary** records inclusion decisions and exclusion reasons for every date in the selected range.
        """)

with st.expander("Step 5: Generate the Summary Files", expanded=False):
    st.markdown("""
- Click **Yes — prepare downloadable files** when you are ready.
- Five download buttons appear, one per row, each with an expandable explanation of its calculations and contents.
- If you change settings or exclusions, prepare the files again before downloading.

**Available CSV files**

- **Daily Summary:** Daily steps, intensity and cadence measures, coverage counts, and inclusion decisions.
- **Minute-by-Minute Log:** Recorded steps and missing minutes throughout the selected date range.
- **Hourly Steps Summary:** Recorded step totals and coverage counts for each hour.
- **Red Flag Summary:** Daily and daypart measures, coverage indicators, flags, and exclusion reasons.
- **Participant Averages:** Mean daily measures across included dates, with contributing-day counts.
    """)
    with st.expander("Calculation details and missing data", expanded=False):
        st.markdown("""
Participant averages give each included day equal weight and omit NA separately for each measure, reporting its contributing-day count. Recorded zeros count; missing values are never replaced with zero.

Missing minutes are exported as **NA** (no record in the source file), for both
JSON and CSV inputs. Explicit recorded zeros remain **0**. Missing records do
not establish inactivity or nonwear. Totals and cadence/intensity minutes use
recorded values only; recorded/missing minute counts show how much of each
period is represented. A period with no records has NA activity measures.
Zero-step intervals include only explicit zeros and are interrupted by NA.
Step-positive minutes are recorded minutes with more than zero steps.
Step-only records are not used to estimate wear time.

MPA steps sum counts in minutes at or above the MPA threshold but below VPA.
VPA steps sum counts in minutes at or above VPA. MVPA steps are MPA plus VPA steps.
These are recorded-step totals, not estimates for missing minutes.

**Additional daily calculations:** Steps within a cadence band are the sum of
recorded step counts for minutes in that band. Peak 1-, 30-, and 60-minute
cadence are the means of the highest 1, 30, or 60 recorded minute-level step
counts, respectively (steps/min). These minutes need not be consecutive.
Explicit recorded zeros are eligible; missing minutes are excluded and never
replaced with zero. A peak is NA when fewer than the required number of recorded
minutes are available. These additions were informed by
[stepmetrics](https://github.com/jhmigueles/stepmetrics)
(Migueles, *stepmetrics: Calculate Step and Cadence Metrics from Wearable Data*,
[doi:10.5281/zenodo.7858094](https://doi.org/10.5281/zenodo.7858094)).
        """)

with st.expander("Step 6: Processing a New Participant", expanded=False):
    st.markdown("""
To prevent data from one participant from carrying over to the next, 
**refresh your browser before uploading files for a new participant.** 
This clears the session and fully resets all settings.
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


def upload_error_details(error):
    """Return a plain-language reason and recovery action for a rejected file."""
    messages = {
        "CSV requires timestamp, steps, and data source columns.": (
            "This CSV is not in the supported Google Takeout steps format.",
            "Choose a steps_YYYY-MM-DD.csv file from Physical Activity_GoogleData / Steps."),
        "Multiple data sources found; upload steps from one source at a time.": (
            "This file contains records from more than one data source.",
            "Provide step records for one participant and one data source at a time."),
        "CSV timestamps require Z (UTC) or an explicit timezone offset.": (
            "The timestamps do not include the required timezone information.",
            "Upload the original Google Takeout steps CSV without changing its timestamps."),
        "Expected a nonempty list of Fitbit step records.": (
            "This JSON file is empty or is not a supported Fitbit step-record file.",
            "Choose an original steps-YYYY-MM-DD.json file from the Fitbit export."),
        "JSON requires dateTime and value fields.": (
            "This JSON file does not contain the required step-record information.",
            "Choose a steps-YYYY-MM-DD.json file, rather than another Fitbit data file."),
        "Upload a steps JSON or CSV file.": (
            "This file type is not supported.", "Upload a steps CSV or JSON file; unzip downloaded archives first."),
        "The file contains no step records.": (
            "This file contains no step records.", "Remove this file or replace it with an export that contains step records."),
        "Step counts must be nonnegative whole numbers, without blanks.": (
            "One or more step counts are blank, nonnumeric, negative, fractional, or outside the supported numeric range.",
            "Check that this is an original step-data export. Replace or correct the file before retrying; do not replace missing data with zero."),
        "Missing timestamps are not supported.": (
            "One or more step records have no timestamp.", "Replace the file with an intact original export, or correct the timestamps before retrying."),
        "Invalid step timestamps.": (
            "One or more timestamps cannot be read as a date and time.", "Use the original export without reformatting its dates or times."),
        "Expected minute-aligned timestamps.": (
            "Some timestamps contain seconds or fractions of a second instead of whole minutes.",
            "Choose minute-level step files. Do not round or change timestamps just to make the file load."),
    }
    if str(error) in messages:
        return messages[str(error)]
    if isinstance(error, pd.errors.EmptyDataError):
        return ("This CSV file is empty.", "Remove it or upload an export containing step records.")
    if isinstance(error, (json.JSONDecodeError, pd.errors.ParserError, UnicodeDecodeError)):
        return ("The file could not be read in its expected CSV or JSON format.",
                "Upload the original downloaded file. If it is damaged, download a fresh copy.")
    return ("The tool could not read this file.",
            "Check that it is an original supported step-data export. Replace it or remove it before continuing.")


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
        try:
            times = raw_times.map(lambda value: pd.to_datetime(value, errors='raise', utc=True))
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError("Invalid step timestamps.") from error
        frame = frame.rename(columns={'timestamp': 'dateTime', 'steps': 'value'})
    elif file.name.lower().endswith('.json'):
        data = json.load(file)
        if not isinstance(data, list) or not data:
            raise ValueError("Expected a nonempty list of Fitbit step records.")
        frame = pd.DataFrame(data)
        if not {'dateTime', 'value'}.issubset(frame.columns):
            raise ValueError("JSON requires dateTime and value fields.")
        try:
            times = pd.to_datetime(frame['dateTime'], errors='raise', utc=True)
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError("Invalid step timestamps.") from error
    else:
        raise ValueError("Upload a steps JSON or CSV file.")
    if frame.empty:
        raise ValueError("The file contains no step records.")
    try:
        counts = pd.to_numeric(frame['value'], errors='raise')
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError("Step counts must be nonnegative whole numbers, without blanks.") from error
    if counts.isna().any() or ((counts < 0) | (counts >= 2**63) | (counts % 1 != 0)).any():
        raise ValueError("Step counts must be nonnegative whole numbers, without blanks.")
    if times.isna().any():
        raise ValueError("Missing timestamps are not supported.")
    if ((times.dt.second != 0) | (times.dt.microsecond != 0) | (times.dt.nanosecond != 0)).any():
        raise ValueError("Expected minute-aligned timestamps.")
    return pd.DataFrame({'dateTime': times, 'value': counts.astype('int64')})


# --- SIDEBAR ---
st.sidebar.caption('See Step 2 under "How to Use This Tool".')
st.sidebar.markdown("#### A. Time Zone")
# Representative regions preserve their own historical timezone and DST rules.
TIMEZONE_CHOICES = {
    "UTC": "UTC — keep original timestamps",
    "America/New_York": "American - Eastern",
    "America/Chicago": "American - Central",
    "America/Denver": "American - Mountain",
    "America/Los_Angeles": "American - Pacific",
    "America/Anchorage": "American - Alaska",
    "Pacific/Honolulu": "American - Hawaii",
    "America/Phoenix": "American - Arizona",
    "America/Halifax": "Atlantic — e.g., Nova Scotia, Canada",
    "America/Sao_Paulo": "Brasília — e.g., São Paulo, Brazil",
    "Europe/London": "UK time — United Kingdom",
    "Europe/Paris": "Central European — e.g., France, Germany",
    "Europe/Helsinki": "Eastern European — e.g., Finland",
    "Europe/Moscow": "Moscow — western Russia",
    "Africa/Johannesburg": "South Africa",
    "Asia/Dubai": "Gulf — e.g., United Arab Emirates",
    "Asia/Kolkata": "India",
    "Asia/Bangkok": "Indochina — e.g., Thailand, Vietnam",
    "Asia/Shanghai": "China",
    "Asia/Tokyo": "Japan",
    "Australia/Perth": "Australian Western — e.g., Perth",
    "Australia/Adelaide": "Australian Central — e.g., Adelaide",
    "Australia/Sydney": "Australian Eastern — e.g., Sydney",
    "Pacific/Auckland": "New Zealand — main islands",
}
# Keep common choices first; retain remaining locations for city/country search.
countries_by_zone = {}
for country_code, zone_names in pytz.country_timezones.items():
    for zone_name in zone_names:
        countries_by_zone.setdefault(zone_name, []).append(str(pytz.country_names[country_code]))
for zone_name in sorted(pytz.common_timezones):
    if zone_name not in TIMEZONE_CHOICES and not zone_name.startswith(('US/', 'Canada/')):
        country_label = ", ".join(countries_by_zone.get(zone_name, []))
        location_label = zone_name.replace('_', ' ')
        TIMEZONE_CHOICES[zone_name] = (
            f"{location_label} — {country_label}" if country_label else location_label
        )
timezone_options = list(TIMEZONE_CHOICES)
st.sidebar.caption("Files use UTC. Select the participant’s time zone, or keep UTC.")
timezone = st.sidebar.selectbox(
    "Select participant timezone", timezone_options,
    format_func=lambda name: TIMEZONE_CHOICES[name],
    help="Type a city or country to search. Choose the location whose clock and daylight-saving rules match the collection location."
)
zone = pytz.timezone(timezone)
# Subtract DST from UTC offset; this supports fractional and negative DST rules.
offset_reference_year = datetime.now().year
zone_probes = [zone.localize(datetime(offset_reference_year, month, 15, 12))
               for month in range(1, 13)]
standard_offset = Counter(int((probe.utcoffset() - probe.dst()).total_seconds() / 60)
                          for probe in zone_probes).most_common(1)[0][0]
seasonal_zone = any(probe.dst().total_seconds() != 0 for probe in zone_probes)
observes_dst = st.sidebar.checkbox(
    "This location observes daylight saving time",
    value=seasonal_zone, disabled=timezone == 'UTC', key=f"observes_dst_{timezone}",
    help="Indicate whether the location observed seasonal clock changes during data collection. Historical date-specific changes are applied when selected."
)
if observes_dst:
    analysis_timezone = pytz.timezone(timezone)
    timezone_description = f"{timezone}; date-specific daylight-saving adjustments enabled"
else:
    analysis_timezone = pytz.FixedOffset(standard_offset)
    offset_sign = '+' if standard_offset >= 0 else '-'
    offset_hours, offset_minutes = divmod(abs(standard_offset), 60)
    timezone_description = (
        f"{timezone}; fixed UTC{offset_sign}{offset_hours:02d}:{offset_minutes:02d}; no daylight-saving adjustments (standard offset reference year {offset_reference_year})"
    )
st.sidebar.caption(
    f"{timezone} · automatic daylight-saving adjustments"
    if observes_dst else
    f"Fixed UTC{offset_sign}{offset_hours:02d}:{offset_minutes:02d} · no daylight-saving adjustments"
)
timezone_confirmed = st.sidebar.checkbox(
    "I confirm the timezone and daylight-saving settings above",
    value=False, key=f"timezone_confirmed_{timezone}_{observes_dst}"
)

st.sidebar.markdown("#### B. Participant Information")
manual_participant_id = st.sidebar.text_input("Enter Participant ID", value="Participant_1")

st.sidebar.markdown("#### C. Intensity Thresholds (spm)")
mpa = st.sidebar.number_input("MPA (Moderate Physical Activity) lower limit", value=100)
vpa = st.sidebar.number_input("VPA (Vigorous Physical Activity) lower limit", value=130)

st.sidebar.markdown("#### D. Cadence Band Thresholds (spm)")
b1 = st.sidebar.number_input("Incidental movement lower limit", value=1)
b2 = st.sidebar.number_input("Sporadic movement lower limit", value=20)
b3 = st.sidebar.number_input("Purposeful steps lower limit", value=40)
b4 = st.sidebar.number_input("Slow walking lower limit", value=60)
b5 = st.sidebar.number_input("Medium walking lower limit", value=80)
b6 = st.sidebar.number_input("Brisk walking lower limit", value=100)
b7 = st.sidebar.number_input("Faster locomotion/ambulation lower limit", value=120)

st.sidebar.markdown("#### E. Data Upload")
uploaded_files = st.sidebar.file_uploader(
    "Upload Google Takeout steps CSV files or Fitbit JSON",
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
    accepted_files = []
    rejected_files = []
    batch_hash = hashlib.sha256(manual_participant_id.encode('utf-8'))

    # Validate each file completely. No records from rejected files enter the analysis.
    for file in uploaded_files:
        file.seek(0)
        contents = file.read()
        if isinstance(contents, str):
            contents = contents.encode('utf-8')
        batch_hash.update(file.name.encode('utf-8'))
        batch_hash.update(hashlib.sha256(contents).digest())
        try:
            temp_df = read_step_file(file)
        except Exception as error:
            reason, action = upload_error_details(error)
            rejected_files.append({'File': file.name, 'Why it could not be used': reason, 'What to do': action})
            continue
        all_raw_dfs.append(temp_df)
        accepted_files.append({'File': file.name, 'Step records': len(temp_df)})

    if accepted_files and not rejected_files:
        st.success("✅ Files Reviewed")

    if rejected_files:
        st.subheader("Upload Review")
        st.write(f"**Accepted files: {len(accepted_files)}**")
        st.warning(f"{len(rejected_files)} file(s) could not be used. No records from these files will be analyzed.")
        for item in rejected_files:
            st.text(item['File'])
            st.write(item['Why it could not be used'])
            st.caption("What to do: " + item['What to do'])
        if not accepted_files:
            st.error("No usable files remain. Remove or replace the rejected files in E. Data Upload to continue.")
            st.session_state.pop('prepared_output_context', None)
            st.stop()
        st.info("Remove or replace the rejected files in E. Data Upload, or explicitly continue with the accepted files only. Continuing may leave gaps in your analysis.")
        continue_accepted = st.checkbox(
            "Continue with accepted files only",
            value=False, key=f"accept_partial_upload_{batch_hash.hexdigest()}"
        )
        if not continue_accepted:
            st.session_state.pop('prepared_output_context', None)
            st.stop()

    if all_raw_dfs:
        df = pd.concat(all_raw_dfs)
        df = df.drop_duplicates(subset=['dateTime'])
        df = df.set_index('dateTime').tz_convert(analysis_timezone)
        df = df[df.index.notna()]

        earliest_available_date = df.index.min().date()
        latest_available_date = df.index.max().date()

        date_context = hashlib.sha256(
            (batch_hash.hexdigest() + timezone_description).encode('utf-8')
        ).hexdigest()
        confirmed_dates = st.session_state.get('confirmed_analysis_dates')
        if confirmed_dates and confirmed_dates['context'] != date_context:
            st.session_state.pop('confirmed_analysis_dates', None)
            confirmed_dates = None
        date_revision = st.session_state.get('date_selection_revision', 0)

        if confirmed_dates:
            analysis_start_date = confirmed_dates['start']
            analysis_end_date = confirmed_dates['end']
            confirmed_dates_col, change_dates_col = st.columns([5, 1])
            with confirmed_dates_col:
                st.success(
                    f"✅ Confirmed dates: {analysis_start_date:%B %d, %Y} through {analysis_end_date:%B %d, %Y}"
                )
            with change_dates_col:
                change_dates_clicked = st.button(
                    "Change dates", key=f"change_dates_{date_context}_{date_revision}",
                    use_container_width=True
                )
            if change_dates_clicked:
                st.session_state['date_selection_draft'] = confirmed_dates
                st.session_state.pop('confirmed_analysis_dates', None)
                st.session_state.pop('prepared_output_context', None)
                st.session_state['date_selection_revision'] = date_revision + 1
                st.rerun()
        else:
            st.write("### Select Analysis Date Range")
            st.info(
                f"Available local dates: **{earliest_available_date:%B %d, %Y}** "
                f"through **{latest_available_date:%B %d, %Y}**"
            )
            draft = st.session_state.get('date_selection_draft', {})
            if draft.get('context') != date_context:
                draft = {}
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                analysis_start_date = st.date_input(
                    "Analysis start date",
                    value=draft.get('start', earliest_available_date),
                    min_value=earliest_available_date, max_value=latest_available_date,
                    key=f"analysis_start_{date_context}_{date_revision}"
                )
            with date_col2:
                analysis_end_date = st.date_input(
                    "Analysis end date",
                    value=draft.get('end', latest_available_date),
                    min_value=earliest_available_date, max_value=latest_available_date,
                    key=f"analysis_end_{date_context}_{date_revision}"
                )
            valid_date_range = analysis_start_date <= analysis_end_date
            if not valid_date_range:
                st.error("❌ The analysis start date must be on or before the end date.")
            date_range_confirmed = st.checkbox(
                f"I confirm that the analysis should include {analysis_start_date:%B %d, %Y} through {analysis_end_date:%B %d, %Y}",
                value=False, disabled=not valid_date_range,
                key=f"confirm_date_selection_{date_context}_{date_revision}_{analysis_start_date}_{analysis_end_date}"
            )
            if date_range_confirmed and valid_date_range:
                st.session_state['confirmed_analysis_dates'] = {
                    'context': date_context, 'start': analysis_start_date, 'end': analysis_end_date
                }
                st.rerun()
            st.info("Confirm the analysis date range to review days and generate outputs.")
            st.stop()

        local_dates = pd.Series(df.index.date, index=df.index)
        selected_date_mask = (
            (local_dates >= analysis_start_date) & (local_dates <= analysis_end_date)
        )
        df = df.loc[selected_date_mask.to_numpy()]
        if df.empty:
            st.warning("No source records occur in this range. Outputs will mark every minute as NA.")

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
            + repr((batch_hash.hexdigest(), manual_participant_id, timezone_description, observes_dst, analysis_start_date, analysis_end_date,
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
            st.subheader("Day Selection")
            st.write("Days may be excluded for any study-specific reason. Red Flag indicators are summarized, but individual days must still be selected for exclusion.")
            include_all = st.checkbox(
                "Include all dates",
                value=False, key=f"include_all_v2_{review_context}"
            )
            if include_all:
                st.info("Uncheck Include all dates to edit exclusions and reasons.")
            with st.expander("About red flags and exclusions", expanded=False):
                st.markdown("""
**How red flags are calculated**

Flags are calculated for each calendar day in your selected timezone, using recorded step values.

- **No recorded data:** No minutes have a step record.
- **Recorded steps total zero:** At least one minute has a record, but all recorded step counts are zero.
- **Recorded steps below 1,000:** The sum of recorded steps is less than 1,000.
- **Steps in only one daypart:** Minutes with one or more steps occur in exactly one of four periods: Overnight (midnight–5:59 a.m.), Morning (6 a.m.–11:59 a.m.), Afternoon (noon–5:59 p.m.), or Evening (6 p.m.–11:59 p.m.).
- **First-to-last positive minute span below 6 hours:** Fewer than 360 elapsed minutes separate the first and last minutes with steps. A day with only one step-positive minute has a span of zero; a day with none does not receive this flag.

**Number of red flags** counts how many of these five criteria are met. Criteria can overlap.

**Additional information in the Red Flag Summary**

- Daily and daypart step totals sum recorded counts. Step-positive minutes count records with one or more steps.
- Recorded minutes have a source record, including explicit zeros. Missing minutes have no record and are labeled NA. Expected minutes reflect the selected timezone and daylight-saving settings.
- Zero-step intervals consist of consecutive minutes with explicitly recorded zeros. Missing minutes interrupt these intervals. The file reports the longest interval within each day and the number of intervals lasting at least 90 minutes that overlap that day. Intervals may cross midnight. These measures do not add to the red flag count.

**How to use the indicators**

- Flags suggest days to review; they do not establish nonwear or automatically exclude days. Apply and report your study's inclusion criteria.
- Missing minutes do not establish inactivity or nonwear.
- **Include all dates** overrides individual exclusions.
- The Red Flag Summary retains every date and any exclusion reasons. Excluded dates are removed from the other analysis exports and participant averages.
                """)
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
            review.insert(0, 'Exclude_from_Analysis', False)
            review.insert(1, 'Exclusion_Reason', '')
            leading_columns = [
                'Exclude_from_Analysis', 'Date', 'Exclusion_Reason', 'Flag_Reasons',
                'Total_Steps', 'Recorded_Minutes', 'Missing_Minutes',
                'Total_Step_Positive_Minutes', 'Number_of_Red_Flags',
            ]
            review = review[leading_columns]
            with st.expander("Red Flag Summary", expanded=True):
                flagged = review.loc[review['Flag_Reasons'].ne('')]
                if flagged.empty:
                    st.write("No dates meet the current red flag criteria.")
                for _, row in flagged.iterrows():
                    st.markdown(f"**{row['Date']}** — {row['Flag_Reasons']}")
            st.write("Check **Exclude** to remove a day from analysis outputs. The Red Flag Summary retains all dates.")
            st.caption("To add an optional reason, double-click its cell, type your note, and press Enter.")
            edited_review = st.data_editor(
                review, hide_index=True, use_container_width=True,
                key=f"day_review_v4_{review_context}_{include_all}",
                disabled=True if include_all else [
                    c for c in review.columns if c not in ('Exclude_from_Analysis', 'Exclusion_Reason')
                ],
                column_config={
                    'Exclude_from_Analysis': st.column_config.CheckboxColumn('Exclude', width='small'),
                    'Date': st.column_config.DateColumn('Date', format='YYYY-MM-DD', width='small'),
                    'Flag_Reasons': st.column_config.TextColumn('Red flag reasons', width='large'),
                    'Exclusion_Reason': st.column_config.TextColumn('Exclusion reason (optional)', width='large'),
                }
            )
            decisions = edited_review[['Date', 'Exclude_from_Analysis', 'Exclusion_Reason']].copy()
            if include_all:
                decisions['Exclude_from_Analysis'] = False
            decisions['Included_in_Participant_Summary'] = ~decisions['Exclude_from_Analysis'].fillna(False).astype(bool)
            decisions['Exclusion_Reason'] = decisions['Exclusion_Reason'].fillna('').where(
                ~decisions['Included_in_Participant_Summary'], ''
            )
            decisions = decisions[['Date', 'Included_in_Participant_Summary', 'Exclusion_Reason']]
        else:
            st.info("All dates will be included. A Red Flag Summary will still be available as a download.")
        final_summary = final_summary.merge(decisions, on='Date', validate='one_to_one')
        red_flag_summary = red_flag_summary.merge(decisions, on='Date', validate='one_to_one')
        included_count = int(final_summary['Included_in_Participant_Summary'].sum())
        st.caption(f"{included_count} included day(s); {len(final_summary) - included_count} excluded day(s). Excluded dates are retained only in the Red Flag Summary.")
        if included_count == 0:
            st.warning("No dates are included. Daily, minute-level, and hourly files will contain headers only. Participant means will be NA with zero contributing days; the Red Flag Summary will retain all dates.")
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
        # Build averages before filtering so selection counts retain the full date range.
        included_dates = final_summary.loc[
            final_summary['Included_in_Participant_Summary'], 'Date'
        ]
        final_summary = final_summary.loc[final_summary['Date'].isin(included_dates)].copy()
        final_min_by_min = final_min_by_min.loc[final_min_by_min['Date'].isin(included_dates)].copy()
        hourly_steps_summary = hourly_steps_summary.loc[hourly_steps_summary['Date'].isin(included_dates)].copy()
        # The red-flag export remains the complete audit of dates and exclusion reasons.
        for output_frame in (final_summary, final_min_by_min, hourly_steps_summary, red_flag_summary):
            output_frame['Analysis_Timezone'] = timezone_description
            output_frame['Daylight_Saving_Observed'] = observes_dst
        st.success("Your five analysis files are ready.")
        st.caption(
            f"Dates are based on {timezone_description}. Excluded dates are retained only in the Red Flag Summary. "
            "Missing values are exported as NA."
        )
        downloads = [
            ("Daily Summary", final_summary, "Daily_Summaries", """
Daily recorded steps; step-positive minutes; MPA, VPA and MVPA minutes and steps;
minutes and steps in each cadence band; peak 1-, 30- and 60-minute cadence; and coverage counts.
MPA is at least the selected MPA threshold and below VPA; VPA is at least the VPA threshold.
MVPA combines MPA and VPA. Band steps sum the recorded counts within each band.
Peak cadence averages the highest N recorded minute counts, which need not be consecutive.
A peak is NA if fewer than N recorded minutes exist. Recorded zeros remain eligible.
Only included dates appear in this file. Exclusion decisions and reasons are retained in the Red Flag Summary.
"""),
            ("Minute-by-Minute Log", final_min_by_min, "Min_by_Min", """
Participant ID, local date, local time and steps for every minute in the selected range.
Absent records are NA; explicitly recorded zeros stay zero. Days follow the selected timezone,
with daylight-saving changes only when enabled. Excluded dates are removed from this file.
"""),
            ("Hourly Steps Summary", hourly_steps_summary, "Hourly_Steps_Summary", """
Recorded step totals for each local clock hour, with recorded- and missing-minute counts.
Hours with no records have NA totals. A repeated daylight-saving hour is combined under its
clock-hour label when daylight-saving adjustments are enabled. With adjustments disabled,
every selected day has 24 clock hours. Excluded dates are removed from this file.
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






