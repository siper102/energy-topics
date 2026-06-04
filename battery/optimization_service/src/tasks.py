import logging
from worker import celery_app
from optimization.optimization_pipeline import OptimizationPipeline, Hyperparameters

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.run_optimization_task", bind=True)
def run_optimization_task(self, alpha: float, grid_fee: float, setup_id: int):
    """
    Celery task that wraps the existing optimization pipeline.
    """
    logger.info(f"Starting optimization task for setup_id={setup_id} with alpha={alpha}, grid_fee={grid_fee}")
    
    try:
        # 1. Initialize hyperparameters
        params = Hyperparameters(alpha=alpha, grid_fee=grid_fee)
        
        # 2. Initialize pipeline
        pipeline = OptimizationPipeline(hyper_params=params, setup_id=setup_id)
        
        # 3. Execute
        pipeline.run_pipeline()
        
        logger.info("Optimization task completed successfully.")
        return {"status": "success", "message": "Optimization completed and results saved to DB."}
        
    except Exception as e:
        logger.error(f"Optimization task failed: {e}")
        # Re-raise to let Celery handle the failure status
        raise e
