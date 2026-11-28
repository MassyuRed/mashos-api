-- Apply Piece cleanup in the existing Auth account deletion transaction.
-- A single Piece deletion still retains the account's quota and receipts.
BEGIN;

ALTER TABLE public.piece_records
    ADD CONSTRAINT piece_records_owner_auth_fk
    FOREIGN KEY (owner_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.piece_quota_month_locks
    ADD CONSTRAINT piece_quota_month_locks_owner_auth_fk
    FOREIGN KEY (owner_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.piece_quota_consumptions
    ADD CONSTRAINT piece_quota_consumptions_owner_auth_fk
    FOREIGN KEY (owner_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.piece_export_receipts
    ADD CONSTRAINT piece_export_receipts_owner_auth_fk
    FOREIGN KEY (owner_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.piece_delete_receipts
    ADD CONSTRAINT piece_delete_receipts_owner_auth_fk
    FOREIGN KEY (owner_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

ALTER TABLE public.piece_record_reads
    ADD CONSTRAINT piece_record_reads_viewer_auth_fk
    FOREIGN KEY (viewer_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;

COMMIT;
