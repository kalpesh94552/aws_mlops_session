"""Feature engineers the abalone dataset and optionally writes to Feature Store."""
import argparse
import logging
import os
import pathlib
import requests
import tempfile
import time
from datetime import datetime

import boto3
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


# Since we get a headerless CSV file we specify the column names here.
feature_columns_names = [
    "sex",
    "length",
    "diameter",
    "height",
    "whole_weight",
    "shucked_weight",
    "viscera_weight",
    "shell_weight",
]
label_column = "rings"

feature_columns_dtype = {
    "sex": str,
    "length": np.float64,
    "diameter": np.float64,
    "height": np.float64,
    "whole_weight": np.float64,
    "shucked_weight": np.float64,
    "viscera_weight": np.float64,
    "shell_weight": np.float64,
}
label_column_dtype = {"rings": np.float64}


def merge_two_dicts(x, y):
    """Merges two dicts, returning a new copy."""
    z = x.copy()
    z.update(y)
    return z


def write_to_feature_store(df, feature_group_name, region, role):
    """Write processed features to SageMaker Feature Store."""
    try:
        import sagemaker
        from sagemaker.feature_store.feature_group import FeatureGroup
        from sagemaker.feature_store.feature_definition import (
            FeatureDefinition,
            FeatureTypeEnum,
        )
        
        logger.info(f"Writing features to Feature Store: {feature_group_name}")
        
        # Create boto3 session
        boto_session = boto3.Session(region_name=region)
        sagemaker_session = sagemaker.Session(boto_session=boto_session)
        
        # Define feature definitions
        feature_definitions = [
            FeatureDefinition(feature_name="event_time", feature_type=FeatureTypeEnum.STRING),
            FeatureDefinition(feature_name="record_id", feature_type=FeatureTypeEnum.STRING),
            FeatureDefinition(feature_name="sex", feature_type=FeatureTypeEnum.STRING),
            FeatureDefinition(feature_name="length", feature_type=FeatureTypeEnum.FRACTIONAL),
            FeatureDefinition(feature_name="diameter", feature_type=FeatureTypeEnum.FRACTIONAL),
            FeatureDefinition(feature_name="height", feature_type=FeatureTypeEnum.FRACTIONAL),
            FeatureDefinition(feature_name="whole_weight", feature_type=FeatureTypeEnum.FRACTIONAL),
            FeatureDefinition(feature_name="shucked_weight", feature_type=FeatureTypeEnum.FRACTIONAL),
            FeatureDefinition(feature_name="viscera_weight", feature_type=FeatureTypeEnum.FRACTIONAL),
            FeatureDefinition(feature_name="shell_weight", feature_type=FeatureTypeEnum.FRACTIONAL),
            FeatureDefinition(feature_name="rings", feature_type=FeatureTypeEnum.INTEGRAL),
        ]
        
        # Create or get feature group
        feature_group = FeatureGroup(
            name=feature_group_name,
            sagemaker_session=sagemaker_session,
            feature_definitions=feature_definitions,
        )
        
        # Prepare data for Feature Store
        # Add event_time and record_id columns
        current_time_sec = int(round(time.time()))
        df_fs = df.copy()
        df_fs["event_time"] = pd.Series([current_time_sec] * len(df_fs), dtype=str)
        df_fs["record_id"] = df_fs.index.astype(str)
        
        # Ensure all columns are present
        required_cols = ["event_time", "record_id", "sex", "length", "diameter", "height",
                        "whole_weight", "shucked_weight", "viscera_weight", "shell_weight", "rings"]
        for col in required_cols:
            if col not in df_fs.columns:
                if col == "rings":
                    # If rings is not in df_fs, we need to add it from the original data
                    logger.warning(f"Column {col} not found, skipping Feature Store write")
                    return
                else:
                    df_fs[col] = 0.0
        
        # Select only required columns in correct order
        df_fs = df_fs[required_cols]
        
        # Try to create feature group (will fail if it already exists, which is fine)
        try:
            feature_group.create(
                s3_uri=f"s3://{sagemaker_session.default_bucket()}/feature-store/{feature_group_name}",
                record_identifier_name="record_id",
                event_time_feature_name="event_time",
                role_arn=role,
                enable_online_store=True,
            )
            logger.info(f"Created new feature group: {feature_group_name}")
            # Wait for feature group to be ready
            time.sleep(10)
        except Exception as e:
            if "ResourceInUse" in str(e) or "already exists" in str(e).lower():
                logger.info(f"Feature group {feature_group_name} already exists, using existing one")
            else:
                logger.warning(f"Could not create feature group: {e}")
                return
        
        # Ingest data to Feature Store
        feature_group.ingest(data_frame=df_fs, max_workers=3, wait=True)
        logger.info(f"Successfully ingested {len(df_fs)} records to Feature Store")
        
    except ImportError:
        logger.warning("SageMaker Feature Store SDK not available, skipping Feature Store write")
    except Exception as e:
        logger.warning(f"Failed to write to Feature Store: {e}")
        logger.warning("Continuing without Feature Store...")


if __name__ == "__main__":
    logger.debug("Starting preprocessing.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-data", type=str, required=True)
    parser.add_argument("--feature-group-name", type=str, default=None)
    parser.add_argument("--enable-feature-store", type=str, default="False")
    parser.add_argument("--region", type=str, default=None)
    args = parser.parse_args()

    base_dir = "/opt/ml/processing"
    pathlib.Path(f"{base_dir}/data").mkdir(parents=True, exist_ok=True)
    input_data = args.input_data
    bucket = input_data.split("/")[2]
    key = "/".join(input_data.split("/")[3:])

    logger.info("Downloading data from bucket: %s, key: %s", bucket, key)
    fn = f"{base_dir}/data/abalone-dataset.csv"
    s3 = boto3.resource("s3")
    s3.Bucket(bucket).download_file(key, fn)

    logger.debug("Reading downloaded data.")
    df = pd.read_csv(
        fn,
        header=None,
        names=feature_columns_names + [label_column],
        dtype=merge_two_dicts(feature_columns_dtype, label_column_dtype),
    )
    os.unlink(fn)

    logger.debug("Defining transformers.")
    numeric_features = list(feature_columns_names)
    numeric_features.remove("sex")
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_features = ["sex"]
    categorical_transformer = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="constant", fill_value="missing"),
            ),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocess = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    logger.info("Applying transforms.")
    y = df.pop("rings")
    X_pre = preprocess.fit_transform(df)
    y_pre = y.to_numpy().reshape(len(y), 1)

    X = np.concatenate((y_pre, X_pre), axis=1)

    logger.info(
        "Splitting %d rows of data into train, validation, test datasets.",
        len(X),
    )
    np.random.shuffle(X)
    train, validation, test = np.split(
        X, [int(0.7 * len(X)), int(0.85 * len(X))]
    )

    logger.info("Writing out datasets to %s.", base_dir)
    pd.DataFrame(train).to_csv(
        f"{base_dir}/train/train.csv", header=False, index=False
    )
    pd.DataFrame(validation).to_csv(
        f"{base_dir}/validation/validation.csv", header=False, index=False
    )
    pd.DataFrame(test).to_csv(
        f"{base_dir}/test/test.csv", header=False, index=False
    )
    
    # Write features for Feature Store (original data before preprocessing)
    # Save original dataframe for Feature Store ingestion
    features_dir = f"{base_dir}/features"
    pathlib.Path(features_dir).mkdir(parents=True, exist_ok=True)
    
    # Reconstruct original dataframe with features and label
    original_df = df.copy()
    original_df["rings"] = y
    original_df.to_csv(
        f"{features_dir}/features.csv", header=True, index=False
    )
    logger.info("Saved features for Feature Store ingestion.")
    
    # Write to Feature Store if enabled
    if args.enable_feature_store.lower() == "true" and args.feature_group_name:
        try:
            # Get IAM role from environment (set by SageMaker)
            role = os.environ.get("SAGEMAKER_ROLE_ARN") or os.environ.get("TRAINING_JOB_ROLE_ARN")
            if not role:
                logger.warning("IAM role not found in environment, skipping Feature Store write")
            else:
                write_to_feature_store(
                    original_df,
                    args.feature_group_name,
                    args.region or os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                    role
                )
        except Exception as e:
            logger.warning(f"Feature Store ingestion failed: {e}, continuing...")
