# Kaggle CPU benchmark results

Run `bash loadtest/kaggle_runner.sh` from the project root after installing `requirements-loadtest.txt` and starting the API. The runner creates a timestamped directory here with:

- `environment.txt`: Kaggle hardware, software versions, API target and load configuration.
- `locust_stats.csv`, `locust_stats_history.csv`, and `locust_failures.csv`: request count, failure count, throughput and response-time percentiles.
- `report.html`: Locust summary report.
- `summary.md`: concise baseline metrics for the aggregate row.

The default profile is 10 concurrent users, 2 users spawned per second and a 60-second run. Set `USERS`, `SPAWN_RATE`, `RUN_TIME`, and `BASE_URL` to repeat a different profile, and preserve these values when comparing runs. The API and Locust share a Kaggle CPU if both run on the same notebook instance; report that arrangement with each result.

## Recorded baseline

The first Kaggle CPU baseline is stored in [`20261028T182659Z-m8jDvhHE/`](20261028T182659Z-m8jDvhHE/). It used 10 users, a spawn rate of 2 users/second, and ran for 60 seconds on a 4-CPU Intel Xeon Kaggle runtime. Locust exited with code 0 and recorded zero failures. Its final console table reports 4,918 requests; the last periodic CSV snapshot and `summary.md` report 4,868. Locust refreshes CSV statistics periodically, so the final console total can be newer than that snapshot. The raw log and CSV are both retained in the run directory.
