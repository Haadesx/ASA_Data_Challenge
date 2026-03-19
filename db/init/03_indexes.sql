-- Light indexes on common IDs and join keys.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'raw' AND table_name = 'wwc_original' AND column_name = 'f_findingid'
  ) THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_wwc_original_f_findingid ON raw.wwc_original (f_findingid)';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'raw' AND table_name = 'wwc_original' AND column_name = 's_studyid'
  ) THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_wwc_original_s_studyid ON raw.wwc_original (s_studyid)';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'raw' AND table_name = 'wwc_original' AND column_name = 'i_interventionid'
  ) THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_wwc_original_i_interventionid ON raw.wwc_original (i_interventionid)';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'raw' AND table_name = 'wwc_aggregated' AND column_name = 'f_findingid'
  ) THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_wwc_aggregated_f_findingid ON raw.wwc_aggregated (f_findingid)';
  END IF;
END $$;
