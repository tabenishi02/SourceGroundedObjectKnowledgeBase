def test_legacy_ingestion_import_paths_reexport_canonical_symbols():
    from sgokb.context import analyze as legacy_analyze
    from sgokb.extraction import GenericExtractor as LegacyGenericExtractor
    from sgokb.importer import WebCaptureImporter as LegacyWebCaptureImporter
    from sgokb.ingestion.context import analyze
    from sgokb.ingestion.extraction import GenericExtractor
    from sgokb.ingestion.importer import WebCaptureImporter

    assert legacy_analyze is analyze
    assert LegacyGenericExtractor is GenericExtractor
    assert LegacyWebCaptureImporter is WebCaptureImporter
