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
6. Migration version 3 creates a SQLite backup beside the working DB before adding
   `houses.owner_id`, `houses.created_at`, and `house_members.joined_at`.
7. Existing rows are preserved. Resolvable legacy members are linked to `users`,
   timestamps are backfilled, and legacy invite codes outside the 6–8 character
   uppercase alphanumeric rule are replaced with unique 8-character codes.
8. Migration version 4 creates another working-DB backup before adding chore
   descriptions, linked assignee and creator IDs, scheduled/completed timestamps,
   and creation timestamps. Legacy `assigned_to`, `due_date`, and `status` columns
   remain in place and are synchronized for compatibility.
