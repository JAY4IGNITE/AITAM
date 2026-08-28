# Dataset Evaluation Pipeline

The Dataset Evaluation Pipeline enables the automated testing of the Multi-Agent Autonomous SOC against real-world datasets (e.g. PhishTank, SpamAssassin) to empirically measure its precision, recall, and real-world efficacy.

## 1. Architecture

1. **Dataset Ingestion**: `POST /api/datasets/import` accepts CSV/JSON/JSONL files.
2. **Normalization**: The `DatasetRegistry` streams the file and parses raw records. The `universal.py` normalizer maps disparate fields (url, text, email) into standard `DatasetSample` entities and standardizes the ground-truth `label`.
3. **Evaluation Runner**: Triggered via `POST /api/evaluation/run`. Uses Celery and Asyncio Semaphores to dispatch isolated investigations against the Sandbox/Agents concurrently.
4. **Metrics Engine**: Maps the continuous 0-100 `Risk Score` output by the agents to categorical labels (BENIGN, SUSPICIOUS, MALICIOUS) using customizable thresholds. Calculates multi-class Confusion Matrix and F1 statistics.

## 2. Ground-Truth Isolation Constraint

**Crucial Security Measure:** The ground-truth `label` assigned to a dataset sample is *strictly isolated* at the Evaluation Pipeline layer. When an `Investigation` is created for the multi-agent system, the `label` is intentionally excluded from the database model and context payload. Agents classify the content entirely blind to its true label.

## 3. Running an Evaluation

1. Navigate to the **Datasets** tab in the Dashboard.
2. Upload a CSV file (must contain a `content` column and a `label` column).
3. Click **Evaluate**.
4. Set **Sample Limit** and **Parallelism** (concurrency). *Note: Keep parallelism below 5 if running on a single laptop to avoid Sandbox/Chromium timeouts.*
5. View the final Confusion Matrix on the Results page.
