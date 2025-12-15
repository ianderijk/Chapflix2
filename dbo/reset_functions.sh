DB_NAME="chapflix"
DB_USER="buildusr"

psql -U "$DB_USER" -d "$DB_NAME" -h 127.0.0.1 -f /media/idr/ExtDrive/Chapflix/dbo/drop_functions.sql

for f in /media/idr/ExtDrive/Chapflix/dbo/functions/*.sql; do
    echo "Applying $f"
    psql -U "$DB_USER" -d "$DB_NAME" -h 127.0.0.1 -f "$f"
done
echo "Finished dropping and creating functions"