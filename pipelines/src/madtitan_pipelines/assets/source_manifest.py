from dagster import AssetExecutionContext, asset


@asset
def source_books(context: AssetExecutionContext) -> list[dict[str, str]]:
    """Manifest rows for private source books.

    This placeholder intentionally does not scan the local mirror yet. The real asset
    will read configured private paths, compute checksums, and emit source metadata.
    """
    settings = context.resources.settings
    context.add_output_metadata({"local_pdf_mirror": settings.local_pdf_mirror or "unset"})
    return []


@asset
def pdf_pages(source_books: list[dict[str, str]]) -> list[dict[str, str]]:
    """Page inventory and text/scanned triage."""
    return []
