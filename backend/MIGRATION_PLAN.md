# RoomSync database migration plan

The root `sharemate.db` remains the untouched Streamlit source database.

1. `python -m backend.scripts.prepare_database` copies the source to
   `backend/data/roomsync.db` when the working copy does not exist.
2. A timestamped copy is written to `backend/backups/` before the auth migration.
3. Migration version 1 adds `users`, `auth_sessions`, a nullable `user_id` link on
   `house_members`, and supporting indexes while preserving all legacy columns and data.
   Existing legacy memberships remain unclaimed until a later verified migration.
4. The FastAPI app reads and writes only the working copy by default.
5. Pointing FastAPI directly at the root database requires a later explicit approval
   and a tested rollback plan.
