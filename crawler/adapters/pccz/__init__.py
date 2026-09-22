from crawler.adapters._planned import PlannedSourceAdapter


class PcczAdapter(PlannedSourceAdapter):
    source_platform = "pccz"


__all__ = ["PcczAdapter"]
