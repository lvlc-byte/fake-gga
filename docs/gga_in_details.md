The **GGA** (Global Positioning System Fix Data) sentence is arguably the most important and commonly used message in the **NMEA 0183** standard. If you are working with GPS/GNSS receivers, this is the primary sentence used to provide 3D location, time, and fix quality data.


---

### 1. General Structure
Like all NMEA sentences, the GGA message is a comma-separated string of ASCII characters. It begins with a `$` sign and ends with a checksum preceded by an asterisk `*`.

**The standard format looks like this:**
`$--GGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh`

*   **Talker ID:** The first two letters after the `$` (e.g., `GP` for GPS, `GL` for GLONASS, or `GN` for GNSS/Multi-constellation).
*   **Sentence Formatter:** The letters `GGA`.

---

### 2. Field-by-Field Breakdown
Let’s look at a real-world example and parse every field:
`$GPGGA,123519.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47`

| Field # | Data Example | Description |
| :--- | :--- | :--- |
| 1 | `123519.00` | **UTC Time:** 12:35:19.00 (HHMMSS.ss) |
| 2 | `4807.038` | **Latitude:** 48 degrees, 07.038 minutes |
| 3 | `N` | **N/S Indicator:** North (N) or South (S) |
| 4 | `01131.000` | **Longitude:** 11 degrees, 31.000 minutes |
| 5 | `E` | **E/W Indicator:** East (E) or West (W) |
| 6 | `1` | **Fix Quality:** (See Section 3 below) |
| 7 | `08` | **Satellites Used:** Number of satellites in use (00-12) |
| 8 | `0.9` | **HDOP:** Horizontal Dilution of Precision |
| 9 | `545.4` | **Altitude:** Height above mean sea level |
| 10 | `M` | **Units:** Meters (for altitude) |
| 11 | `46.9` | **Geoid Separation:** Height of geoid (mean sea level) above WGS84 ellipsoid |
| 12 | `M` | **Units:** Meters (for Geoid separation) |
| 13 | *(empty)* | **Age of DGPS Data:** Time in seconds since last DGPS update |
| 14 | *(empty)* | **DGPS Station ID:** ID of the differential reference station |
| 15 | `*47` | **Checksum:** Used for error checking |

---

### 3. Understanding the Fix Quality (Field 6)
This is one of the most critical fields in the GGA message because it tells the user whether the position data is reliable.

*   **0:** Fix not available (Invalid).
*   **1:** GPS fix (SPS) – Standard point positioning.
*   **2:** Differential GPS (DGPS) fix – Higher accuracy (SBAS).
*   **3:** PPS fix.
*   **4:** Real-Time Kinematic (RTK) **Fixed** – Centimeter-level accuracy.
*   **5:** Real-Time Kinematic (RTK) **Float** – Decimeter-level accuracy.
*   **6:** Estimated (dead reckoning).

---

### 4. Key Concepts within GGA

#### Coordinate Format
It is important to note that NMEA uses **DDMM.MMMM** (Degrees and Decimal Minutes) rather than Decimal Degrees (DD.DDDD). 
*   *Example:* `4807.038` is 48 degrees and 7.038 minutes. 
*   To convert to decimal degrees: $48 + (7.038 / 60) = 48.1173^\circ$.

#### Altitude vs. Geoid Separation
*   **Altitude (Field 9):** This is the Orthometric height (height above the Mean Sea Level).
*   **Geoid Separation (Field 11):** This is the difference between the WGS84 ellipsoid and the Geoid (sea level). 
*   **To get the Ellipsoidal Height (H):** $H = \text{Altitude} + \text{Geoid Separation}$.

#### HDOP (Horizontal Dilution of Precision)
This represents the geometric quality of the satellite configuration. 
*   **Under 1.0:** Ideal.
*   **1.0 – 2.0:** Excellent.
*   **Above 5.0:** Poor accuracy; the satellites are likely bunched together in the sky.

---

### 5. Why use GGA instead of RMC?
The two most common NMEA sentences are **GGA** and **RMC** (Recommended Minimum Navigation Information). 

*   Use **GGA** if you need **altitude (elevation)** and **vertical precision** data.
*   Use **RMC** if you need **Speed Over Ground (SOG)** and **Course Over Ground (COG)**, which GGA does not provide.
*   Most professional applications parse both to get a complete 3D position and velocity vector.

### 6. Example
If you receive:
`$GNGGA,092204.00,3401.123,N,11824.456,W,2,12,0.8,10.5,M,-30.2,M,,*6D`

**Interpretation:** Your device has a DGPS fix (Quality 2) using 12 satellites. You are at 34.0187° N, 118.4076° W at an altitude of 10.5 meters above sea level. The signal precision is excellent (0.8 HDOP).



To store GGA data in PostgreSQL, you need a schema that accounts for the specific formatting of NMEA strings (like the DDMM.MMMM coordinate format).

Below is a guide on how to design the table and use the `COPY` command.

---

### 7. The PostgreSQL Table Schema

We will create a table that stores the raw components. Note that we use `NUMERIC` or `DOUBLE PRECISION` for coordinates and altitude.

```sql
CREATE TABLE gps_gga_data (
    id SERIAL PRIMARY KEY,
    talker_id CHAR(2),              -- GP, GN, GL
    utc_time TIME,                  -- HH:MM:SS
    latitude_ddmm NUMERIC,          -- Raw format: 4807.038
    lat_direction CHAR(1),          -- N or S
    longitude_ddmm NUMERIC,         -- Raw format: 01131.000
    lon_direction CHAR(1),          -- E or W
    fix_quality INT,                -- 0, 1, 2, 4, 5...
    satellites_used INT,
    hdop NUMERIC(4,2),
    altitude NUMERIC,               -- Height above MSL
    altitude_units CHAR(1),         -- M
    geoid_separation NUMERIC,
    geoid_units CHAR(1),            -- M
    dgps_age NUMERIC,               -- Age of DGPS data
    dgps_station_id INT,
    checksum CHAR(2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```


### 8: Enable the Extension and Server
First, you must enable the `file_fdw` extension and create a server object that points to your file system.

```sql
-- Run as superuser
CREATE EXTENSION IF NOT EXISTS file_fdw;

CREATE SERVER log_server FOREIGN DATA WRAPPER file_fdw;
```


In the FDW, we define the structure exactly as it appears in the text file. 
**Note on the Checksum:** In a GGA sentence, the last comma is followed by the `DGPS Station ID` and then the `*Checksum`. If the DGPS ID is empty, the field looks like `*47`. If it has a value, it looks like `0001*47`. Therefore, we treat the last column as a single string.

```sql
CREATE FOREIGN TABLE gga_raw_log (
    raw_talker_type text,      -- This will hold "$GPGGA"
    utc_time text,
    lat text,
    ns text,
    lon text,
    ew text,
    fix_qual text,
    sats text,
    hdop text,
    alt text,
    alt_unit text,
    geoid text,
    geoid_unit text,
    dgps_age text,
    dgps_id_and_checksum text  -- This will hold "station_id*checksum" or "*checksum"
) 
SERVER log_server 
OPTIONS ( filename '/path/to/your/gps_log.txt', format 'csv', delimiter ',' );
```
*Note: Ensure the `postgres` system user has read permissions for the file at that path.*


### 9. Loading from GGA log file

```sql
INSERT INTO gps_gga_data (
    talker_id, 
    utc_time, 
    latitude_ddmm, 
    lat_direction, 
    longitude_ddmm, 
    lon_direction, 
    fix_quality, 
    satellites_used, 
    hdop, 
    altitude, 
    altitude_units, 
    geoid_separation, 
    geoid_units, 
    dgps_age, 
    dgps_station_id, 
    checksum
)
SELECT 
    -- 1. Extract Talker ID (e.g., "$GPGGA" -> "GP")
    substring(raw_talker_type from 2 for 2),

    -- 2. Cast Time (handle empty strings safely)
    NULLIF(utc_time, '')::TIME,

    -- 3. Cast Coordinates
    NULLIF(lat, '')::NUMERIC,
    ns, -- No casting needed, char(1)
    NULLIF(lon, '')::NUMERIC,
    ew, -- No casting needed, char(1)

    -- 4. Cast Integer Metrics
    NULLIF(fix_qual, '')::INT,
    NULLIF(sats, '')::INT,

    -- 5. Cast Precision & Altitude
    NULLIF(hdop, '')::NUMERIC,
    NULLIF(alt, '')::NUMERIC,
    alt_unit,

    -- 6. Cast Geoid Data
    NULLIF(geoid, '')::NUMERIC,
    geoid_unit,
    NULLIF(dgps_age, '')::NUMERIC,

    -- 7. Handle the "Split" Field (DGPS ID * Checksum)
    -- Part 1: The Station ID (before the *)
    NULLIF(split_part(dgps_id_and_checksum, '*', 1), '')::INT,
    
    -- Part 2: The Checksum (after the *)
    split_part(dgps_id_and_checksum, '*', 2)

FROM gga_raw_log
-- Ensure we only process GGA lines (ignores $GPRMC, header lines, etc.)
WHERE raw_talker_type LIKE '$%GGA';
```