# Troubleshooting: ModuleNotFoundError: No module named 'sagemaker.workflow'

## Problem
The error `ModuleNotFoundError: No module named 'sagemaker.workflow'` occurs when:
1. SageMaker SDK is not installed
2. SageMaker SDK version is too old (< 2.0.0)
3. The SDK is installed in a different Python environment

## Solution

### Step 1: Check SageMaker SDK Installation

Run this in your notebook or Python environment:

```python
import sagemaker
print(f"SageMaker SDK version: {sagemaker.__version__}")

# Check if workflow module exists
try:
    from sagemaker.workflow import pipeline
    print("✓ sagemaker.workflow module is available")
except ImportError as e:
    print(f"✗ Error: {e}")
```

### Step 2: Install/Upgrade SageMaker SDK

If the SDK is not installed or version is < 2.0.0, install/upgrade it:

```bash
pip install --upgrade sagemaker>=2.0.0
```

Or in a notebook cell:

```python
import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "sagemaker>=2.0.0"])
```

### Step 3: Verify Installation

After installation, restart your kernel and verify:

```python
import sagemaker
print(f"Version: {sagemaker.__version__}")

# Test workflow imports
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.parameters import ParameterString, ParameterInteger
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
print("✓ All workflow imports successful")
```

## Minimum Requirements

- **Python**: 3.6 or higher
- **SageMaker SDK**: 2.0.0 or higher (workflow module was introduced in v2.0.0)
- **Recommended**: SageMaker SDK 2.93.0 or higher (as specified in setup.py)

## Common Issues

### Issue 1: Multiple Python Environments
If you have multiple Python environments, ensure you're installing in the correct one:

```python
import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
```

### Issue 2: Jupyter Kernel vs System Python
In Jupyter notebooks, the kernel might use a different Python than your system. Install directly in the notebook:

```python
!pip install --upgrade sagemaker>=2.0.0
```

### Issue 3: Conda Environment
If using Conda:

```bash
conda install -c conda-forge sagemaker
# or
pip install --upgrade sagemaker>=2.0.0
```

### Issue 4: SageMaker Studio
In SageMaker Studio, the SDK should be pre-installed. If not:

1. Check the kernel environment
2. Install via terminal: `pip install --upgrade sagemaker`
3. Or use the notebook: `!pip install --upgrade sagemaker`

## Verification Script

Run this complete verification script:

```python
import sys
import subprocess

def check_sagemaker():
    try:
        import sagemaker
        version = sagemaker.__version__
        print(f"✓ SageMaker SDK installed: {version}")
        
        # Check version
        major, minor = map(int, version.split('.')[:2])
        if major < 2:
            print(f"✗ Version {version} is too old. Need >= 2.0.0")
            return False
        
        # Check workflow module
        from sagemaker.workflow.pipeline import Pipeline
        from sagemaker.workflow.parameters import ParameterString
        from sagemaker.workflow.steps import ProcessingStep
        print("✓ sagemaker.workflow module is available")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Installing SageMaker SDK...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "sagemaker>=2.0.0"])
        print("✓ Installation complete. Please restart your kernel.")
        return False

if check_sagemaker():
    print("\n✓ All checks passed!")
else:
    print("\n✗ Please restart your kernel after installation")
```

## After Fixing

Once the SDK is properly installed:

1. **Restart your kernel** (important!)
2. Re-run the notebook cells from the beginning
3. The `sagemaker.workflow` imports should work correctly

## Additional Notes

- The `sagemaker.workflow` module is part of the core SageMaker SDK (v2.0+)
- No separate package installation is needed
- The workflow module includes:
  - `sagemaker.workflow.pipeline`
  - `sagemaker.workflow.parameters`
  - `sagemaker.workflow.steps`
  - `sagemaker.workflow.conditions`
  - And more...

