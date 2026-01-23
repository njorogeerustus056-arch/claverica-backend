-- Make notification_id nullable or add default
ALTER TABLE notifications_notification 
ALTER COLUMN notification_id DROP NOT NULL;

-- Or if you prefer to add a default:
-- ALTER TABLE notifications_notification 
-- ALTER COLUMN notification_id SET DEFAULT 'NOTIF_' || nextval('notifications_notification_id_seq'::regclass)::text;
