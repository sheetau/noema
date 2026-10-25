# Project ledger

`ledger.sqlite` is the authoritative local handoff and searchable document archive. It is not disposable cache. Read [the commands and recovery rules](../docs/project-records.md). No web UI, server, scheduler or goal runner is provided.

The database, archived originals and backups are private and excluded from Git. A clone without the database must restore a backup; an absent ledger must never be interpreted as an empty backlog. The language specifications, source works and verification evidence remain tracked files.
