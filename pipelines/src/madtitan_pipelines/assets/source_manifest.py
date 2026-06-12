from dagster import AssetExecutionContext, asset
from madtitan_contracts.extraction import SourceBook

from madtitan_pipelines.page_inventory import create_pdf_page_inventory
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
def pdf_pages(
    context: AssetExecutionContext,
    source_books: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Page inventory and text/scanned triage."""
    records = []
    for source_book_payload in source_books:
        source_book = SourceBook.model_validate(source_book_payload)
        records.extend(create_pdf_page_inventory(source_book))

    pages_needing_ocr = sum(1 for record in records if record.likely_needs_ocr)
    context.add_output_metadata(
        {
            "pages": len(records),
            "pages_needing_ocr": pages_needing_ocr,
        }
    )
    return [record.model_dump(mode="json") for record in records]
