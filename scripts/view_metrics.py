#!/usr/bin/env python3
"""View CloudWatch metrics for Lambda functions."""

import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from typing import List, Dict, Any


def get_lambda_functions() -> List[Any]:
    """Get list of all Lambda functions with 'cvideo-api' prefix."""
    lambda_client = boto3.client("lambda")

    try:
        response = lambda_client.list_functions()
        functions = response.get("Functions", [])

        # Filter for our API functions
        api_functions = [
            f for f in functions if f["FunctionName"].startswith("cvideo-api-")
        ]

        return api_functions
    except ClientError as e:
        print(f"❌ Error listing Lambda functions: {e}")
        return []


def get_function_metrics(function_name: str) -> Dict[str, Any]:
    """Get CloudWatch metrics for a specific Lambda function."""
    cloudwatch = boto3.client("cloudwatch")

    # Get metrics for the last 24 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)

    metrics = {}

    # Define metrics to retrieve
    metric_queries = [
        ("Invocations", "Sum", "Total invocations"),
        ("Duration", "Average", "Average duration (ms)"),
        ("Errors", "Sum", "Total errors"),
        ("Throttles", "Sum", "Total throttles"),
    ]

    for metric_name, statistic, description in metric_queries:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/Lambda",
                MetricName=metric_name,
                Dimensions=[{"Name": "FunctionName", "Value": function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour periods
                Statistics=[statistic],
            )

            datapoints = response.get("Datapoints", [])
            if datapoints:
                # Get the most recent value
                latest = max(datapoints, key=lambda x: x["Timestamp"])
                metrics[metric_name] = {
                    "value": latest[statistic],
                    "description": description,
                    "timestamp": latest["Timestamp"],
                }
            else:
                metrics[metric_name] = {
                    "value": 0,
                    "description": description,
                    "timestamp": None,
                }

        except ClientError as e:
            print(f"❌ Error getting {metric_name} metrics: {e}")
            metrics[metric_name] = {
                "value": "Error",
                "description": description,
                "timestamp": None,
            }

    return metrics


def display_metrics() -> None:
    """Display metrics for all API functions."""
    print("📊 CloudWatch Metrics for CVIDEO-CLICK-API")
    print("=" * 60)

    functions = get_lambda_functions()

    if not functions:
        print("ℹ️  No Lambda functions found with 'cvideo-api-' prefix.")
        return

    for function in functions:
        function_name = function["FunctionName"]
        print(f"\n🔧 Function: {function_name}")
        print(f"   Runtime: {function['Runtime']}")
        print(f"   Last Modified: {function['LastModified']}")
        print(f"   Memory: {function['MemorySize']} MB")
        print(f"   Timeout: {function['Timeout']} seconds")

        metrics = get_function_metrics(function_name)

        print("   📈 Metrics (Last 24 hours):")
        for metric_name, data in metrics.items():
            value = data["value"]
            description = data["description"]

            if isinstance(value, float):
                if metric_name == "Duration":
                    print(f"      {description}: {value:.2f}")
                else:
                    print(f"      {description}: {int(value)}")
            else:
                print(f"      {description}: {value}")


def main() -> None:
    """Main function to display all metrics."""
    try:
        display_metrics()
    except Exception as e:
        print(f"❌ Error displaying metrics: {e}")


if __name__ == "__main__":
    main()
