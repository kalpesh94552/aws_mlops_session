# Fix: ModuleNotFoundError: No module named 'sagemaker.workflow'

## Quick Fix

### Option 1: Run the Fix Script

```bash
python fix_sagemaker_workflow_import.py
```

### Option 2: Manual Fix in Notebook

**Step 1: Update the first cell in the notebook**

Remove this line:
```python
from sagemaker.workflow.experiment_config import ExperimentConfig
```

Replace the first cell with:
```python
# Check SageMaker SDK installation
try:
    import sagemaker
    print(f"SageMaker SDK version: {sagemaker.__version__}")
    from sagemaker.workflow.pipeline import Pipeline
    print("✓ sagemaker.workflow module is available")
except ImportError as e:
    print(f"Error: {e}")
    print("Installing SageMaker SDK...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "sagemaker>=2.0.0"])
    import sagemaker
    print(f"Installed version: {sagemaker.__version__}")
    print("Please restart the kernel!")

import boto3
import sagemaker
import time

region = boto3.Session().region_name
role = sagemaker.get_execution_role()
default_bucket = sagemaker.session.Session().default_bucket()

model_package_group_name = f"AbaloneModelPackageGroup-Example"
pipeline_name = f"AbalonePipeline-Example"

experiment_name = f"{pipeline_name}-Experiment"
feature_group_name = f"Abalone-feature-group"
```

**Step 2: Install SageMaker SDK (if needed)**

In a notebook cell, run:
```python
!pip install --upgrade sagemaker>=2.0.0
```

**Step 3: Restart Kernel**

After installation, restart your Jupyter kernel and re-run all cells.

## Root Cause

The error occurs because:
1. The incorrect import `from sagemaker.workflow.experiment_config import ExperimentConfig` was in the notebook
2. This module doesn't exist (experiment config is passed as a dictionary, not a class)
3. The `sagemaker.workflow` module requires SageMaker SDK >= 2.0.0

## Verification

After fixing, verify with:

```python
import sagemaker
print(f"Version: {sagemaker.__version__}")

from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.parameters import ParameterString
from sagemaker.workflow.steps import ProcessingStep
print("✓ All imports successful!")
```

## Files Fixed

1. ✅ `seedcode/pipelines/abalone/pipeline.py` - Removed incorrect import
2. ⚠️ `seedcode/sagemaker-pipelines-project.ipynb` - **Needs manual update** (see above)

## Additional Resources

- See `TROUBLESHOOTING_SAGEMAKER_WORKFLOW.md` for detailed troubleshooting
- See `FIX_EXPERIMENT_CONFIG.md` for experiment config usage

