Fetches upcoming bin collection dates from East Suffolk Council and exposes them as Home Assistant sensors.

**Sensors created:**
- `sensor.bin_collection_data` — raw data with `collections` attribute (list of upcoming dates)
- `sensor.bins_due_today` — labels of bins due today, or "None"
- `sensor.bins_due_tomorrow` — labels of bins due tomorrow, or "None"

Data refreshes every 4 hours. Requires your property's UPRN.
