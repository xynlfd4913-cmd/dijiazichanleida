from crawler.adapters._planned import PlannedSourceAdapter


class JdAssetAdapter(PlannedSourceAdapter):
    source_platform = "jd_asset"


__all__ = ["JdAssetAdapter"]
