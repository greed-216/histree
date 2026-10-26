# Ancient scroll and viewport tiles

The prefix covers mythic narratives, Xia, Shang and early Western Zhou as undated chapters. Chapter widths are reading-layout positions, not inferred calendar dates. Annual coordinates start at 841 BCE; the extension joins the unchanged v6 artwork at 403 BCE.

The three prompt files preserve generation inputs for the prefix, annual extension and revised join. Delivered WebP dimensions and SHA-256 hashes are recorded in apps/web/src/data/history-scroll.json. Original generated images remain in the original project design directory and are not runtime dependencies.

apps/web/src/data/history-scroll-tiles.json records source hashes, crops, 1560-pixel cores with edge bleed, low/high variants, exact byte sizes and content hashes. Run python3 scripts/build-scroll-tiles.py to regenerate with Pillow; production serves the checked-in outputs.

Visible low-resolution tiles load first, followed by high-resolution tiles when display density warrants them and low-priority adjacent prefetch. Hash-named tiles receive immutable caching.

Era reading currently uses an empty state, without scene-topic placeholders or fixed book links. This release changes no database records or ingestion progress.
