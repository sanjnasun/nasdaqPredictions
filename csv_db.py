import sqlite3 as sl

# Create/Connect database
conn = sl.connect('ndaq_data.db')
curs = conn.cursor()

# Create our table
curs.execute('DROP TABLE IF EXISTS stock_data')
curs.execute('CREATE TABLE IF NOT EXISTS '
             'stock_data (`Date` text, `Open` real, `High` real, `Low` real, `Close` real, `Adj Close` real, `Volume` integer)')
conn.commit()

values = []
with open('ndaq.csv') as fin:
    for line in fin:
        line = line.strip()
        if line:
            line = line.replace('\"', '')
            lineList = line.split(',')
            if lineList and lineList[-1].strip().isnumeric():
                # Use the date string as is, assuming it's already in 'YYYY-MM-DD' format
                date_str = lineList[0]
                valTuple = (date_str, float(lineList[1]), float(lineList[2]), float(lineList[3]),
                            float(lineList[4]), float(lineList[5]), int(lineList[6]))
                values.append(valTuple)

for valTuple in values:
    stmt = 'INSERT OR IGNORE INTO stock_data VALUES (?, ?, ?, ?, ?, ?, ?)'
    curs.execute(stmt, valTuple)

# Commit the changes and close the connection
conn.commit()
conn.close()
