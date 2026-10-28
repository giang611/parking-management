# Kaggle CPU baseline 20261028T182659Z-m8jDvhHE

See `environment.txt` for hardware, runtime, and load settings.
The API and Locust load generator run on the same Kaggle runtime unless the run configuration says otherwise.

| Metric | Result |
|---|---:|
| Requests | 4868 |
| Failures | 0 |
| Throughput (requests/sec) | 82.3296292267647 |
| Failure rate (failures/sec) | 0.0 |
| Average response time (ms) | 17.17313396877762 |
| Median response time (ms) | 13 |
| 95th percentile (ms) | 46 |
| Maximum response time (ms) | 360.7598269995833 |

The final Locust console table reports 4,918 requests and 0 failures; see `locust.log`. The CSV and this table report 4,868 requests and 0 failures. Locust writes CSV statistics periodically, so the last CSV snapshot can precede the final console totals at shutdown. Keep both raw artifacts when interpreting this run.

Artifacts: `locust_stats.csv`, `locust_stats_history.csv`, `locust_failures.csv`, `report.html`, `locust.log`.
