# Changelog

## [1.0.0] - 2025-12-29

### 🎉 First Stable Release

This release marks semantic-sentinel as production-ready with enterprise features.

### Added
- **Audit Logging**: Pluggable logging system for compliance
  - `FileAuditLogger` - JSONL format for Splunk/Datadog ingestion
  - `ConsoleAuditLogger` - Human-readable console output
  - Logs: profile, action, reason, latency, shadow_mode status
- **Shadow Mode**: Dry-run mode for safe policy rollout
  - Set `shadow_mode: true` in profile config
  - Detects and logs violations but does NOT block (`valid=True`)
  - Actions marked as `shadow_block` for easy filtering
- **CLI Tool**: Command-line interface for quick testing
  - `sentinel scan --text "..." --profile finance`
  - `sentinel list` - Show available profiles
  - `sentinel setup` - Download required models
- **HuggingFace Integration**: `SentinelHFStreamer` for local models
  - Real-time sanitization during `model.generate()`
  - Works with any HuggingFace Transformers model
- **OpenAI Integration**: Native wrappers with streaming support
  - `SentinelOpenAI` (sync) and `SentinelAsyncOpenAI` (async)
  - Automatic input validation and output sanitization
- **LangChain Integration**: `SentinelRunnable` for chain pipelines
- **LlamaIndex Integration**: `SentinelNodePostprocessor` for RAG
- **Async Support**: `validate_async()` for non-blocking operations
- **Streaming**: `StreamSanitizer` for real-time content filtering

### Changed
- Made core dependencies lightweight (moved langkit, detoxify to `[plugins]`)
- Added optional dependency groups: `[openai]`, `[langchain]`, `[llamaindex]`, `[plugins]`, `[all]`
- Fixed image URLs for proper PyPI display

## [0.0.1] - 2025-12-28
### Added
- Initial release of Semantic Sentinel Framework.
- Core Engine with Regex, Semantic Blocking, and PII Redaction.
- Plugin Support (LangKit).
- Configuration-driven architecture (YAML profiles).
