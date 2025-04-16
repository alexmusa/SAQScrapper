echo "\l List databases"
echo "\c Connect to a database"
echo "\dt Display tables"
echo "\d and \d+ Display columns (field names) of a table"
docker exec -ti saqscrapper_db_1 psql -U postgres