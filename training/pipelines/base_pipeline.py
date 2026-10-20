from abc import ABC, abstractmethod
from loguru import logger
from training.utils.progress import ProgressReporter
from training.utils.gpu import check_gpu_available, get_gpu_info

class BasePipeline(ABC):
    """
    Abstract base pipeline enforcing the 16-phase training contract.
    """
    def __init__(self, config):
        self.config = config
        self.reporter = ProgressReporter(config.model_name, config.dataset, total_phases=16)

    def run(self):
        """Execute all 16 phases."""
        try:
            self._phase_1_validate_environment()
            self._phase_2_validate_gpu()
            self._phase_3_validate_dataset()
            self._phase_4_compute_dataset_statistics()
            self._phase_5_preprocess_dataset()
            self._phase_6_verify_splits()
            self._phase_7_load_model()
            self._phase_8_run_baseline_evaluation()
            self._phase_9_train()
            self._phase_10_validate()
            self._phase_11_save_checkpoint()
            self._phase_12_evaluate_test()
            self._phase_13_generate_metrics()
            self._phase_14_compare_baseline()
            self._phase_15_export_model()
            self._phase_16_generate_summary()
            logger.success("Pipeline completed successfully.")
        except Exception as e:
            logger.error(f"Pipeline failed at phase {self.reporter.current_phase}: {e}")
            raise

    # -------------------------------------------------------------------------
    # The 16-Phase Contract
    # -------------------------------------------------------------------------

    def _phase_1_validate_environment(self):
        self.reporter.start_phase("Environment Validation")
        self.validate_environment()
        self.reporter.finish_phase("Environment Validation")

    def _phase_2_validate_gpu(self):
        self.reporter.start_phase("GPU Validation")
        check_gpu_available()
        self.validate_gpu()
        self.reporter.finish_phase("GPU Validation")

    def _phase_3_validate_dataset(self):
        self.reporter.start_phase("Dataset Validation")
        self.validate_dataset()
        self.reporter.finish_phase("Dataset Validation")

    def _phase_4_compute_dataset_statistics(self):
        self.reporter.start_phase("Compute Dataset Statistics")
        self.compute_dataset_statistics()
        self.reporter.finish_phase("Compute Dataset Statistics")

    def _phase_5_preprocess_dataset(self):
        self.reporter.start_phase("Preprocess Dataset")
        self.preprocess_dataset()
        self.reporter.finish_phase("Preprocess Dataset")

    def _phase_6_verify_splits(self):
        self.reporter.start_phase("Verify Splits")
        self.verify_splits()
        self.reporter.finish_phase("Verify Splits")

    def _phase_7_load_model(self):
        self.reporter.start_phase("Load Model")
        self.load_model()
        self.reporter.finish_phase("Load Model")

    def _phase_8_run_baseline_evaluation(self):
        self.reporter.start_phase("Baseline Evaluation")
        self.run_baseline_evaluation()
        self.reporter.finish_phase("Baseline Evaluation")

    def _phase_9_train(self):
        self.reporter.start_phase("Training")
        self.train()
        self.reporter.finish_phase("Training")

    def _phase_10_validate(self):
        self.reporter.start_phase("Validation")
        self.validate()
        self.reporter.finish_phase("Validation")

    def _phase_11_save_checkpoint(self):
        self.reporter.start_phase("Save Checkpoint")
        self.save_checkpoint()
        self.reporter.finish_phase("Save Checkpoint")

    def _phase_12_evaluate_test(self):
        self.reporter.start_phase("Test Evaluation")
        self.evaluate_test()
        self.reporter.finish_phase("Test Evaluation")

    def _phase_13_generate_metrics(self):
        self.reporter.start_phase("Generate Metrics")
        self.generate_metrics()
        self.reporter.finish_phase("Generate Metrics")

    def _phase_14_compare_baseline(self):
        self.reporter.start_phase("Compare Baseline")
        self.compare_baseline()
        self.reporter.finish_phase("Compare Baseline")

    def _phase_15_export_model(self):
        self.reporter.start_phase("Export Model")
        self.export_model()
        self.reporter.finish_phase("Export Model")

    def _phase_16_generate_summary(self):
        self.reporter.start_phase("Generate Summary")
        self.generate_summary()
        self.reporter.finish_phase("Generate Summary")

    # -------------------------------------------------------------------------
    # Abstract Methods to be implemented by child classes
    # -------------------------------------------------------------------------
    @abstractmethod
    def validate_environment(self): pass
    @abstractmethod
    def validate_gpu(self): pass
    @abstractmethod
    def validate_dataset(self): pass
    @abstractmethod
    def compute_dataset_statistics(self): pass
    @abstractmethod
    def preprocess_dataset(self): pass
    @abstractmethod
    def verify_splits(self): pass
    @abstractmethod
    def load_model(self): pass
    @abstractmethod
    def run_baseline_evaluation(self): pass
    @abstractmethod
    def train(self): pass
    @abstractmethod
    def validate(self): pass
    @abstractmethod
    def save_checkpoint(self): pass
    @abstractmethod
    def evaluate_test(self): pass
    @abstractmethod
    def generate_metrics(self): pass
    @abstractmethod
    def compare_baseline(self): pass
    @abstractmethod
    def export_model(self): pass
    @abstractmethod
    def generate_summary(self): pass
