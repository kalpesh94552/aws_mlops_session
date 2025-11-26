# Fix for ModuleNotFoundError: No module named 'sagemaker.workflow.experiment_config'

## Problem
The import `from sagemaker.workflow.experiment_config import ExperimentConfig` is incorrect because this module doesn't exist in the SageMaker SDK.

## Solution
Experiment configuration in SageMaker Pipelines is passed as a **dictionary** to `pipeline.start()`, not as an imported class.

## Changes Made

### 1. Removed incorrect import from `pipeline.py`
- Removed: `from sagemaker.workflow.experiment_config import ExperimentConfig`
- Removed: `from sagemaker.feature_store.feature_group import FeatureGroup` (not used in pipeline.py)

### 2. Updated notebook to use correct experiment config format

**Before (incorrect):**
```python
from sagemaker.workflow.experiment_config import ExperimentConfig

execution = pipeline.start()
```

**After (correct):**
```python
import time
from sagemaker.experiments import Experiment

# Create or get experiment
sm_client = boto3.client("sagemaker")
try:
    experiment = Experiment.load(
        experiment_name=experiment_name,
        sagemaker_boto_client=sm_client
    )
except Exception:
    experiment = Experiment.create(
        experiment_name=experiment_name,
        description="Abalone pipeline experiment",
        sagemaker_boto_client=sm_client
    )

# Start pipeline with experiment config as a dictionary
trial_name = f"{pipeline_name}-trial-{int(time.time())}"
run_name = f"{pipeline_name}-run-{int(time.time())}"

execution = pipeline.start(
    experiment_config={
        "ExperimentName": experiment_name,
        "TrialName": trial_name,
        "RunName": run_name
    }
)
```

## Key Points

1. **No import needed**: There's no `ExperimentConfig` class to import
2. **Dictionary format**: Pass experiment config as a dictionary with keys:
   - `"ExperimentName"`: Name of the experiment
   - `"TrialName"`: Name of the trial (unique for each execution)
   - `"RunName"`: (Optional) Name of the run
3. **Create experiment first**: Use `sagemaker.experiments.Experiment` to create/load the experiment before starting the pipeline

## Updated Notebook Cells

The notebook has been updated with:
1. **Cell 1**: Removed incorrect import, added `import time`
2. **New Cell 15**: Creates/loads the experiment
3. **Cell 16**: Updated to pass `experiment_config` as a dictionary
4. **Cell 24**: Updated parameterized execution to also include experiment config

## Testing

After these changes, you should be able to:
1. Run the notebook without import errors
2. Start pipeline executions with experiment tracking
3. View trials in SageMaker Studio Experiments UI

