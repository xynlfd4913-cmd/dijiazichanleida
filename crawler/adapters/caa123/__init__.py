from crawler.adapters._planned import PlannedSourceAdapter


class Caa123Adapter(PlannedSourceAdapter):
    source_platform = "caa123"


__all__ = ["Caa123Adapter"]
