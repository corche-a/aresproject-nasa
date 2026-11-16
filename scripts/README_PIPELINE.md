# Offline pipeline

The current JSON has no EMIT results (`emit_integrated: false`). When the finished
AppEEARS request is available, ingest `EMIT_L2B_MIN.001` layers `group_1/2_mineral_id`
and `band_depth` for 2023–2025 into the offline processing scripts, then regenerate
`analogs_data.json`. Do not add a mineral result until the downloaded scenes have been
quality checked and associated with a basin.
