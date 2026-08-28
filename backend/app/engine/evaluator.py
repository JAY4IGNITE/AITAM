import asyncio
import uuid
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import List, Dict

from ..models.dataset import Dataset, DatasetSample, LabelType
from ..models.evaluation import EvaluationRun, EvaluationResult
from ..models.investigation import Investigation, InvestigationStatus
from ..engine.coordinator import InvestigationCoordinator
from ..engine.metrics import compute_metrics, calculate_baseline
from ..worker import celery_app

class DatasetEvaluator:
    @staticmethod
    def _map_risk_to_label(final_risk_score: float, thresholds: Dict[str, float]) -> str:
        if final_risk_score is None:
            return "UNKNOWN"
        if final_risk_score >= thresholds.get("CRITICAL", 80):
            return "MALICIOUS"
        elif final_risk_score >= thresholds.get("HIGH", 60):
            return "PHISHING"
        elif final_risk_score >= thresholds.get("MEDIUM", 30):
            return "SUSPICIOUS"
        else:
            return "BENIGN"

    @staticmethod
    async def execute_run(run_id: str, db: AsyncSession):
        """Executes the evaluation pipeline over all samples in the dataset."""
        run = await db.get(EvaluationRun, run_id)
        if not run:
            return
            
        dataset_id = run.dataset_id
        samples = (await db.execute(select(DatasetSample).where(DatasetSample.dataset_id == dataset_id))).scalars().all()
        
        run.total_samples = len(samples)
        await db.commit()
        
        thresholds = run.thresholds or {"CRITICAL": 80, "HIGH": 60, "MEDIUM": 30}
        parallelism = run.configuration.get("parallelism", 2)
        
        # We will dispatch investigations asynchronously.
        # However, to prevent crushing the sandbox, we limit concurrency via asyncio.Semaphore
        semaphore = asyncio.Semaphore(parallelism)
        
        async def evaluate_sample(sample: DatasetSample):
            async with semaphore:
                start_time = time.time()
                
                # 1. Create completely isolated investigation
                inv = Investigation(
                    display_id=f"EVAL-{uuid.uuid4().hex[:8].upper()}",
                    input_type=sample.input_type,
                    target=sample.content,
                    normalized_input=sample.content,
                    status=InvestigationStatus.CREATED
                )
                db.add(inv)
                await db.commit()
                await db.refresh(inv)
                
                # 2. Track result
                eval_result = EvaluationResult(
                    id=str(uuid.uuid4()),
                    evaluation_run_id=run.id,
                    sample_id=sample.id,
                    investigation_id=inv.id,
                    status="RUNNING"
                )
                db.add(eval_result)
                await db.commit()
                
                # 3. Run Autonomous Investigation Coordinator
                try:
                    await InvestigationCoordinator.run_loop(inv.id, db)
                    
                    # Reload investigation to get final state
                    await db.refresh(inv)
                    
                    eval_result.predicted_label = DatasetEvaluator._map_risk_to_label(inv.final_risk_score, thresholds)
                    eval_result.status = "COMPLETED"
                    eval_result.total_latency = time.time() - start_time
                    
                    # Optional: extract agent latencies
                    agent_latencies = {}
                    for a_run in inv.agent_runs:
                        agent_latencies[a_run.agent_name] = a_run.duration
                    eval_result.agent_latencies = agent_latencies
                    
                except Exception as e:
                    eval_result.status = "FAILED"
                    eval_result.error_message = str(e)
                    
                await db.commit()
                return eval_result

        # Run all
        tasks = [evaluate_sample(s) for s in samples[:run.configuration.get("sample_limit", len(samples))]]
        results = await asyncio.gather(*tasks)
        
        # Post-Processing & Metrics
        y_true = []
        y_pred = []
        
        completed = 0
        failed = 0
        
        for res, sample in zip(results, samples):
            if res.status == "COMPLETED":
                y_true.append(sample.label.value)
                y_pred.append(res.predicted_label)
                completed += 1
            else:
                failed += 1
                
        labels = [l.value for l in LabelType]
        metrics = compute_metrics(y_true, y_pred, labels)
        
        run.completed_samples = completed
        run.failed_samples = failed
        run.accuracy = metrics.get("accuracy")
        run.precision = metrics.get("precision")
        run.recall = metrics.get("recall")
        run.f1_score = metrics.get("f1_score")
        run.false_positive_rate = metrics.get("false_positive_rate")
        run.false_negative_rate = metrics.get("false_negative_rate")
        run.confusion_matrix = metrics.get("confusion_matrix")
        
        run.status = "COMPLETED"
        run.updated_at = datetime.utcnow()
        await db.commit()
