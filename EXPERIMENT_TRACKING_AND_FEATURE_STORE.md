# Experiment Tracking and Feature Store Integration

This document describes the updates made to the SageMaker pipeline to incorporate experiment tracking and Feature Store integration.

## Changes Made

### 1. Pipeline Updates (`seedcode/pipelines/abalone/pipeline.py`)

#### Experiment Tracking
- Added `ExperimentConfig` import from `sagemaker.workflow.experiment_config`
- Pipeline now automatically creates trials for each execution
- Hyperparameters are now pipeline parameters (NumRound, MaxDepth, Eta) for tracking
- Each pipeline execution is automatically associated with an experiment

#### Feature Store Integration
- Added Feature Store parameters:
  - `FeatureGroupName`: Name of the Feature Store feature group
  - `EnableFeatureStore`: Boolean flag to enable/disable Feature Store
- Preprocessing step now outputs features for Feature Store ingestion
- Features are written to Feature Store during preprocessing

### 2. Preprocessing Script Updates (`seedcode/pipelines/abalone/preprocess.py`)

#### Feature Store Support
- Added `write_to_feature_store()` function to ingest features into Feature Store
- Features are automatically written to Feature Store if enabled
- Feature group is created automatically if it doesn't exist
- Original features (before preprocessing) are saved for Feature Store ingestion
- Added command-line arguments:
  - `--feature-group-name`: Name of the feature group
  - `--enable-feature-store`: Enable/disable Feature Store
  - `--region`: AWS region

### 3. Notebook Updates (`seedcode/sagemaker-pipelines-project.ipynb`)

#### New Cells Added
1. **Experiment Setup**: Creates or loads the experiment
2. **Feature Store Check**: Verifies Feature Store feature group status
3. **Experiment Trials View**: Lists all trials in the experiment
4. **Trial Components**: Shows components (training jobs, processing jobs) in each trial

## Usage

### Running the Pipeline with Experiment Tracking

```python
from pipelines.abalone.pipeline import get_pipeline
from sagemaker.workflow.experiment_config import ExperimentConfig

# Define experiment and feature group names
experiment_name = "AbalonePipeline-Example-Experiment"
feature_group_name = "Abalone-feature-group"

# Create pipeline with experiment and Feature Store enabled
pipeline = get_pipeline(
    region=region,
    role=role,
    default_bucket=default_bucket,
    model_package_group_name="AbaloneModelPackageGroup-Example",
    pipeline_name="AbalonePipeline-Example",
    experiment_name=experiment_name,
    feature_group_name=feature_group_name,
    enable_feature_store=True,
)

# Upsert pipeline
pipeline.upsert(role_arn=role)

# Create experiment (if it doesn't exist)
from sagemaker.experiments import Experiment
try:
    experiment = Experiment.load(
        experiment_name=experiment_name,
        sagemaker_boto_client=boto3.client("sagemaker")
    )
except:
    experiment = Experiment.create(
        experiment_name=experiment_name,
        description="Abalone pipeline experiment",
        sagemaker_boto_client=boto3.client("sagemaker")
    )

# Start pipeline execution (experiment tracking is automatic)
execution = pipeline.start()
```

### Viewing Experiment Results

```python
# List all trials in the experiment
trials = list(experiment.list_trials())
for trial in trials:
    print(f"Trial: {trial.trial_name}")
    print(f"Created: {trial.creation_time}")
    
    # List trial components
    components = list(trial.list_trial_components())
    for component in components:
        print(f"  Component: {component.trial_component_name}")
```

### Checking Feature Store

```python
from sagemaker.feature_store.feature_group import FeatureGroup

feature_group = FeatureGroup(
    name=feature_group_name,
    sagemaker_session=sagemaker.session.Session()
)

# Get feature group description
fg_desc = feature_group.describe()
print(f"Feature Group ARN: {fg_desc['FeatureGroupArn']}")
print(f"Online Store Status: {fg_desc['OnlineStoreConfig']['Status']}")

# Get record count (if available)
# Note: This requires the feature group to be created and data ingested
```

## Benefits

### Experiment Tracking
1. **Reproducibility**: Track all hyperparameters and metrics for each run
2. **Comparison**: Compare different pipeline executions side-by-side
3. **Lineage**: Track artifact lineage from data to model
4. **Collaboration**: Share experiment results with team members

### Feature Store
1. **Feature Reuse**: Use the same features across multiple models
2. **Point-in-Time Retrieval**: Retrieve features as they existed at a specific time
3. **Online Serving**: Serve features in real-time for inference
4. **Feature Discovery**: Discover and reuse features across teams

## IAM Permissions Required

### For Experiment Tracking
- `sagemaker:CreateExperiment`
- `sagemaker:DescribeExperiment`
- `sagemaker:ListTrials`
- `sagemaker:ListTrialComponents`
- `sagemaker:AssociateTrialComponent`

### For Feature Store
- `sagemaker:CreateFeatureGroup`
- `sagemaker:DescribeFeatureGroup`
- `sagemaker:PutRecord` (for ingestion)
- `sagemaker:GetRecord` (for retrieval)
- `s3:PutObject` (for offline store)
- `s3:GetObject` (for offline store)

## Notes

1. **Feature Store Creation**: The feature group is created automatically during the first pipeline execution if it doesn't exist. This may take a few minutes.

2. **Experiment Auto-Creation**: When you start a pipeline execution, SageMaker automatically creates a trial in the experiment. The experiment itself should be created beforehand (as shown in the notebook).

3. **Feature Store Offline Store**: Features are stored in S3 in Parquet format for efficient querying. The offline store location is automatically configured.

4. **Online Store**: By default, an online store is created for real-time feature serving. This can be disabled if not needed.

5. **Cost Considerations**: 
   - Feature Store online store incurs additional costs
   - Experiment tracking has minimal cost impact
   - Consider disabling online store if not needed for real-time inference

## Troubleshooting

### Feature Store Creation Fails
- Ensure IAM role has necessary permissions
- Check that the S3 bucket exists and is accessible
- Verify the feature group name follows naming conventions (alphanumeric and hyphens only)

### Experiment Not Found
- Create the experiment before running the pipeline
- Ensure experiment name matches between creation and pipeline execution

### Features Not Ingested
- Check preprocessing logs for Feature Store errors
- Verify `EnableFeatureStore` parameter is set to "True"
- Ensure IAM role has `sagemaker:PutRecord` permission

