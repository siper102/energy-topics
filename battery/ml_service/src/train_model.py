import os
import logging
from pipelines.data_pipeline import run_data_pipeline
from pipelines.ml_pipeline import run_ml_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def train_and_register_model():
    """
    Consolidated routine to:
    1. Fetch/Generate data (Data Pipeline)
    2. Train and register model to BentoML (ML Pipeline)
    """
    data_path = "data/training_data.parquet"

    # 1. Run Data Pipeline
    logger.info("📥 Starting Data Pipeline (fetching/generating training data)...")
    try:
        run_data_pipeline()
        logger.info("✅ Data Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"❌ Data Pipeline failed: {e}")
        raise

    # 2. Run ML Pipeline
    logger.info("🧠 Starting ML Pipeline (training and registering model)...")
    try:
        # Ensure data file exists before training
        if not os.path.exists(data_path):
            # If the data pipeline saves it relative to the root, check that too
            # Typically run from root, so 'data/...' should work
            logger.warning(
                f"Data file {data_path} not found in CWD. Checking ml_service/data/..."
            )
            alt_path = os.path.join("ml_service", data_path)
            if os.path.exists(alt_path):
                data_path = alt_path

        run_ml_pipeline(data_path=data_path)
        logger.info("✅ ML Pipeline completed successfully. Model registered.")
    except Exception as e:
        logger.error(f"❌ ML Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    train_and_register_model()
