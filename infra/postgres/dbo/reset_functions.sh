DB_NAME="chapflix"
DB_USER="postgres"

psql -U "$DB_USER" -d "$DB_NAME" -h 0.0.0.0 -f /media/idr/ExtDrive/Chapflix2/dbo/drop_functions.sql

for f in /media/idr/ExtDrive/Chapflix2/dbo/functions/*.sql; do
    echo "Applying $f"
    psql -U "$DB_USER" -d "$DB_NAME" -h 0.0.0.0 -f "$f"
done
echo "Finished dropping and creating functions"
