@echo off
echo Starting Backup Process...
set timestamp=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%

if not exist "backups" mkdir backups

echo Backing up database...
copy ottoman_assistant.db backups\ottoman_assistant_%timestamp%.db

echo Backing up uploads...
xcopy /E /I /Y uploads backups\uploads_%timestamp%

echo Backup Complete!
