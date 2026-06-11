from dagster import AssetExecutionContext, asset


@asset
def postgres_load(
    context: AssetExecutionContext,
    validation_results: dict[str, list[dict[str, object]]],
) -> dict[str, int]:
    """Idempotent loading boundary for Postgres raw/core schemas."""
    accepted_count = len(validation_results["accepted"])
    quarantine_count = len(validation_results["quarantined"]) + len(validation_results["failed"])
    context.add_output_metadata(
        {
            "accepted_records": accepted_count,
            "quarantine_records": quarantine_count,
        }
    )
    return {"accepted_records": accepted_count, "quarantine_records": quarantine_count}


@asset
def mart_build(postgres_load: dict[str, int]) -> str:
    """Boundary for dbt mart refreshes."""
    return "pending"


@asset
def search_refresh(mart_build: str) -> str:
    """Boundary for app read-model and search index refreshes."""
    return "pending"


@asset
def report_build(mart_build: str) -> str:
    """Boundary for generated derived-metric reports."""
    return "pending"
