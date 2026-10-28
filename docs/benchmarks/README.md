# Kaggle CPU benchmark results

Run `bash loadtest/kaggle_runner.sh` from the project root after installing `requirements-loadtest.txt` and starting the API. The runner creates a timestamped directory here with:

- `environment.txt`: Kaggle hardware, software versions, API target and load configuration.
- `locust_stats.csv`, `locust_stats_history.csv`, and `locust_failures.csv`: request count, failure count, throughput and response-time percentiles.
- `report.html`: Locust summary report.
- `summary.md`: concise baseline metrics for the aggregate row.

The default profile is 10 concurrent users, 2 users spawned per second and a 60-second run. Set `USERS`, `SPAWN_RATE`, `RUN_TIME`, and `BASE_URL` to repeat a different profile, and preserve these values when comparing runs. The API and Locust share a Kaggle CPU if both run on the same notebook instance; report that arrangement with each result.

No Kaggle measurements are recorded in the repository yet. Commit a run directory only after executing the runner on the Kaggle CPU required by the project.
