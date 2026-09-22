from crawler.adapters._planned import PlannedSourceAdapter


class OvupreAdapter(PlannedSourceAdapter):
    source_platform = "ovupre"


__all__ = ["OvupreAdapter"]
