from dagster import Definitions, load_assets_from_modules

from madtitan_pipelines.assets import extraction, loading, source_manifest
from madtitan_pipelines.resources.settings import PipelineSettings

assets = load_assets_from_modules([source_manifest, extraction, loading])

defs = Definitions(
    assets=assets,
    resources={
        "settings": PipelineSettings(),
    },
)
