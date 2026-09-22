from crawler.adapters._planned import PlannedSourceAdapter


class GpaiAdapter(PlannedSourceAdapter):
    source_platform = "gpai"


__all__ = ["GpaiAdapter"]
