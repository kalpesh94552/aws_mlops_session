"""
Fix script for ModuleNotFoundError: No module named 'sagemaker.workflow'

This script:
1. Checks if SageMaker SDK is installed
2. Verifies the version (needs >= 2.0.0)
3. Installs/upgrades if needed
4. Verifies workflow module is available
"""

import sys
import subprocess

def check_and_install_sagemaker():
    """Check SageMaker SDK and install/upgrade if needed."""
    
    print("=" * 60)
    print("SageMaker SDK Installation Check")
    print("=" * 60)
    
    # Check Python version
    print(f"\nPython version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Check if sagemaker is installed
    try:
        import sagemaker
        version = sagemaker.__version__
        print(f"\n✓ SageMaker SDK found: version {version}")
        
        # Check version
        major, minor = map(int, version.split('.')[:2])
        if major < 2:
            print(f"✗ Version {version} is too old. Need >= 2.0.0")
            needs_upgrade = True
        else:
            print(f"✓ Version {version} is compatible (>= 2.0.0)")
            needs_upgrade = False
            
    except ImportError:
        print("\n✗ SageMaker SDK not found")
        needs_upgrade = True
        version = None
    
    # Check if workflow module is available
    workflow_available = False
    if not needs_upgrade:
        try:
            from sagemaker.workflow.pipeline import Pipeline
            from sagemaker.workflow.parameters import ParameterString
            from sagemaker.workflow.steps import ProcessingStep
            print("✓ sagemaker.workflow module is available")
            workflow_available = True
        except ImportError as e:
            print(f"✗ sagemaker.workflow module not available: {e}")
            needs_upgrade = True
    
    # Install/upgrade if needed
    if needs_upgrade:
        print("\n" + "=" * 60)
        print("Installing/Upgrading SageMaker SDK...")
        print("=" * 60)
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "--upgrade", "sagemaker>=2.0.0"
            ])
            print("\n✓ Installation complete!")
            
            # Verify installation
            import sagemaker
            print(f"✓ New version: {sagemaker.__version__}")
            
            # Check workflow module again
            try:
                from sagemaker.workflow.pipeline import Pipeline
                print("✓ sagemaker.workflow module is now available")
                workflow_available = True
            except ImportError as e:
                print(f"✗ Still cannot import workflow module: {e}")
                print("  Please restart your Python kernel/IDE and try again")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"\n✗ Installation failed: {e}")
            print("\nTry installing manually:")
            print(f"  {sys.executable} -m pip install --upgrade sagemaker>=2.0.0")
            return False
    
    print("\n" + "=" * 60)
    if workflow_available:
        print("✓ All checks passed! SageMaker workflow module is ready.")
        print("\nNext steps:")
        print("1. If you're in a Jupyter notebook, restart the kernel")
        print("2. Re-run your notebook cells")
        print("3. The sagemaker.workflow imports should work now")
    else:
        print("✗ Some issues remain. Please check the errors above.")
    print("=" * 60)
    
    return workflow_available

if __name__ == "__main__":
    success = check_and_install_sagemaker()
    sys.exit(0 if success else 1)

