from dagster import AssetExecutionContext, asset

from madtitan_pipelines.source_manifest import load_source_manifests


@asset
def source_books(context: AssetExecutionContext) -> list[dict[str, object]]:
    """Manifest rows for private source books.

    Manifests are user-created before extraction and contain book title, ruleset,
    private PDF reference, checksum, and extraction settings.
    """
    settings = context.resources.settings
    manifests = load_source_manifests(settings.source_manifest_path)
    context.add_output_metadata(
        {
            "local_pdf_mirror": settings.local_pdf_mirror or "unset",
            "source_manifest_path": settings.source_manifest_path,
            "source_books": len(manifests),
        }
    )
    return [manifest.model_dump(mode="json") for manifest in manifests]


@asset
def pdf_pages(source_books: list[dict[str, str]]) -> list[dict[str, str]]:
    """Page inventory and text/scanned triage."""
    return []
