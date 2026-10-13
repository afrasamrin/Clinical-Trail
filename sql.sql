CREATE DATABASE IF NOT EXISTS clinical_data_proj ;
use clinical_data_proj;

DROP TABLE IF EXISTS dm;
DROP TABLE IF EXISTS ae;
DROP TABLE IF EXISTS lb;


CREATE TABLE dm (
    USUBJID  VARCHAR(30) PRIMARY KEY,
    SITEID   INT,
    AGE      INT,
    SEX      CHAR(1),
    ARM      VARCHAR(20),
    RFICDTC  DATE,          -- informed consent date
    RFSTDTC  DATE           -- first dose date
);
 
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.1/Uploads/dm.csv'
INTO TABLE dm
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(USUBJID, SITEID, AGE, SEX, ARM, @rficdtc, @rfstdtc)
SET
RFICDTC = CASE
    -- Format 1: 2025-04-03 (ISO, what the CSV contains)
    WHEN TRIM(@rficdtc) REGEXP '^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$'
        THEN STR_TO_DATE(TRIM(@rficdtc), '%Y-%m-%d')
    -- Format 2: 03-04-2025 (dd-mm-yyyy, if Excel re-saved the file)
    WHEN TRIM(@rficdtc) REGEXP '^[0-9]{1,2}-[0-9]{1,2}-[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@rficdtc), '%d-%m-%Y')
    -- Format 3: 03/04/2025 (dd/mm/yyyy)
    WHEN TRIM(@rficdtc) REGEXP '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@rficdtc), '%d/%m/%Y')
    -- Anything else (including blank) -> NULL
    ELSE NULL
END,
RFSTDTC = CASE
    WHEN TRIM(@rfstdtc) REGEXP '^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$'
        THEN STR_TO_DATE(TRIM(@rfstdtc), '%Y-%m-%d')
    WHEN TRIM(@rfstdtc) REGEXP '^[0-9]{1,2}-[0-9]{1,2}-[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@rfstdtc), '%d-%m-%Y')
    WHEN TRIM(@rfstdtc) REGEXP '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@rfstdtc), '%d/%m/%Y')
    ELSE NULL
END;
 

CREATE TABLE ae (
    AE_ID    INT AUTO_INCREMENT PRIMARY KEY,
    USUBJID  VARCHAR(30),
    AETERM   VARCHAR(50),
    AESTDTC  DATE,
    AEENDTC  DATE,
    AESEV    VARCHAR(10) NULL,   -- has blanks -> NULL
    AESER    CHAR(1)
);
 
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.1/Uploads/ae.csv'
INTO TABLE ae
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(USUBJID, AETERM, @aestdtc, @aeendtc, @aesev, AESER)
SET
AESTDTC = CASE
    WHEN TRIM(@aestdtc) REGEXP '^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$'
        THEN STR_TO_DATE(TRIM(@aestdtc), '%Y-%m-%d')
    WHEN TRIM(@aestdtc) REGEXP '^[0-9]{1,2}-[0-9]{1,2}-[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@aestdtc), '%d-%m-%Y')
    WHEN TRIM(@aestdtc) REGEXP '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@aestdtc), '%d/%m/%Y')
    ELSE NULL
END,
AEENDTC = CASE
    WHEN TRIM(@aeendtc) REGEXP '^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$'
        THEN STR_TO_DATE(TRIM(@aeendtc), '%Y-%m-%d')
    WHEN TRIM(@aeendtc) REGEXP '^[0-9]{1,2}-[0-9]{1,2}-[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@aeendtc), '%d-%m-%Y')
    WHEN TRIM(@aeendtc) REGEXP '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@aeendtc), '%d/%m/%Y')
    ELSE NULL
END,
AESEV = NULLIF(TRIM(@aesev), '');      -- blank -> NULL
 
 
CREATE TABLE lb (
    LB_ID     INT AUTO_INCREMENT PRIMARY KEY,
    USUBJID   VARCHAR(30),
    VISIT     VARCHAR(20),
    LBTESTCD  VARCHAR(10),
    LBORRES   FLOAT NULL,          -- has blanks -> NULL
    LBORRESU  VARCHAR(10),
    LBSTNRLO  FLOAT,
    LBSTNRHI  FLOAT,
    LBDTC     DATE
);
 
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.1/Uploads/lb.csv'
INTO TABLE lb
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(USUBJID, VISIT, LBTESTCD, @lborres, LBORRESU, LBSTNRLO, LBSTNRHI, @lbdtc)
SET
LBORRES = NULLIF(TRIM(@lborres), ''),  -- without this a blank becomes 0 or errors
LBDTC = CASE
    WHEN TRIM(@lbdtc) REGEXP '^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}$'
        THEN STR_TO_DATE(TRIM(@lbdtc), '%Y-%m-%d')
    WHEN TRIM(@lbdtc) REGEXP '^[0-9]{1,2}-[0-9]{1,2}-[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@lbdtc), '%d-%m-%Y')
    WHEN TRIM(@lbdtc) REGEXP '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$'
        THEN STR_TO_DATE(TRIM(@lbdtc), '%d/%m/%Y')
    ELSE NULL
END;
 


-- =====================================================================
-- VERIFY THE LOAD
-- =====================================================================
 
-- Row counts: expect dm = 60, ae = 96, lb = 720
SELECT 'dm' AS tbl, COUNT(*) AS row_count FROM dm
UNION ALL SELECT 'ae', COUNT(*) FROM ae
UNION ALL SELECT 'lb', COUNT(*) FROM lb;
 
-- Dates that failed to parse (expect 0 rows each)
SELECT * FROM dm WHERE RFICDTC IS NULL OR RFSTDTC IS NULL;
SELECT * FROM ae WHERE AESTDTC IS NULL OR AEENDTC IS NULL;
SELECT * FROM lb WHERE LBDTC IS NULL;
 
-- Expected NULLs from the source data: AESEV = 4, LBORRES = 5
SELECT COUNT(*) AS missing_aesev  FROM ae WHERE AESEV   IS NULL;
SELECT COUNT(*) AS missing_lborres FROM lb WHERE LBORRES IS NULL;
 
-- Check for stray carriage returns (expect 0)
SELECT COUNT(*) AS bad_rows FROM ae WHERE AESER NOT IN ('Y','N');


-- ----Data Validation-----

-- name: orphan_ae_subjects
SELECT *,a.USUBJID, a.AETERM FROM ae a LEFT JOIN dm d ON a.USUBJID = d.USUBJID WHERE d.USUBJID IS NULL;

-- name: ae_start_before_consent
SELECT a.USUBJID, a.AETERM, a.AESTDTC, d.RFICDTC FROM ae a JOIN dm d ON a.USUBJID = d.USUBJID WHERE a.AESTDTC < d.RFICDTC;

-- name: ae_end_before_start
SELECT USUBJID, AETERM, AESTDTC, AEENDTC FROM ae WHERE AEENDTC < AESTDTC;

-- name: ae_missing_severity
SELECT *,USUBJID, AETERM, AESTDTC FROM ae WHERE AESEV IS NULL OR TRIM(AESEV) = '';

-- name: duplicate_ae_records
SELECT USUBJID, AETERM, AESTDTC, COUNT(*) AS n FROM ae GROUP BY USUBJID, AETERM, AESTDTC, AEENDTC HAVING COUNT(*) > 1;

-- name: age_out_of_range
SELECT USUBJID, AGE FROM dm WHERE AGE < 18 OR AGE > 100;

-- name: lab_missing_results
SELECT USUBJID, VISIT, LBTESTCD,LBORRES FROM lb WHERE LBORRES IS NULL;

-- name: lab_before_consent
SELECT l.USUBJID, l.VISIT, l.LBTESTCD, l.LBDTC, d.RFICDTC FROM lb l JOIN dm d ON l.USUBJID = d.USUBJID WHERE l.LBDTC < d.RFICDTC;

-- name: hgb_implausible
SELECT USUBJID, VISIT, LBORRES FROM lb WHERE LBTESTCD = 'HGB' AND (LBORRES < 3 OR LBORRES > 25);

-- name: subjects_with_most_aes
SELECT USUBJID, COUNT(*) AS ae_count FROM ae GROUP BY USUBJID ORDER BY ae_count DESC LIMIT 5;

-- name: serious_aes_listing
SELECT USUBJID, AETERM, AESTDTC, AESEV FROM ae WHERE AESER = 'Y' ORDER BY AESTDTC;

 
