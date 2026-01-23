-- Fix transactions_transaction user_id type issue
DO $$
BEGIN
    -- Check current type
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='transactions_transaction' 
        AND column_name='user_id' 
        AND data_type='character varying'
    ) THEN
        -- Create backup column
        ALTER TABLE transactions_transaction ADD COLUMN user_id_backup VARCHAR(255);
        UPDATE transactions_transaction SET user_id_backup = user_id;
        
        -- Drop old column with its indexes
        ALTER TABLE transactions_transaction DROP COLUMN user_id;
        
        -- Create new column with correct type
        ALTER TABLE transactions_transaction ADD COLUMN user_id BIGINT;
        
        -- Copy data back (convert where possible)
        UPDATE transactions_transaction 
        SET user_id = CAST(user_id_backup AS BIGINT) 
        WHERE user_id_backup ~ '^[0-9]+$';
        
        -- Drop backup
        ALTER TABLE transactions_transaction DROP COLUMN user_id_backup;
        
        RAISE NOTICE '✅ Converted user_id from varchar to bigint';
    ELSE
        RAISE NOTICE '✓ user_id already bigint';
    END IF;
END $$;
