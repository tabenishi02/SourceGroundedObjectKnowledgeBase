# Dot-source in a dedicated CPC PowerShell session: . ./scripts/Use-Strata.ps1
$strataStatus = Invoke-RestMethod 'http://127.0.0.1:8080/v1/status' -TimeoutSec 10
if (-not $strataStatus.loaded -or $strataStatus.model -ne 'qwen3.8-flash-next-iq3_s') {
    throw 'Start Strata with qwen3.8-flash-next-iq3_s before selecting this environment.'
}
$strataMetrics = Invoke-RestMethod 'http://127.0.0.1:8080/metrics' -TimeoutSec 10
$env:CPC_LLM_PROVIDER = 'strata'
$env:CPC_LLM_BASE_URL = 'http://127.0.0.1:8080/v1'
$env:CPC_LLM_MODEL = 'qwen3.8-flash-next-iq3_s'
$env:CPC_LLM_REVISION = 'upstream-unknown;IQ3_S'
$env:CPC_LLM_MAX_TOKENS = '8192'
$env:CPC_API_TIMEOUT = '180'
$env:CPC_LLM_EXTRA_JSON = '{"chat_template_kwargs":{"enable_thinking":false}}'
Remove-Item Env:CPC_LLM_FRAGMENT_EXTRA_JSON -ErrorAction SilentlyContinue
Remove-Item Env:CPC_LLM_FINAL_EXTRA_JSON -ErrorAction SilentlyContinue
$env:CPC_RUNTIME_METADATA_JSON = @{
    runtime = 'Strata'
    runtime_version = $strataStatus.engine
    model_revision = 'unknown'
    quantization = 'IQ3_S'
    context_length = $strataStatus.context.native
    control_vector = $strataMetrics.engine.cvec
    gpu = $strataStatus.machine.gpu.name
} | ConvertTo-Json -Compress
# Embedding settings remain separate: Strata does not expose a text embedding API.
