$ErrorActionPreference = "Stop"

$headers = @{
  Authorization = "Bearer $env:OPENAI_API_KEY"
  "Content-Type" = "application/json"
}

$instr = Get-Content .\instructions2.txt -Raw
$body  = @{ model = "gpt-5.2"; input = $instr } | ConvertTo-Json -Depth 10

try {
  $res = Invoke-RestMethod -Method Post -Uri "https://api.openai.com/v1/responses" -Headers $headers -Body $body
  "OK status=$($res.status) model=$($res.model) id=$($res.id)"
} catch {
  $r = $_.Exception.Response
  if ($r -and $r.GetResponseStream()) {
    $sr = New-Object IO.StreamReader($r.GetResponseStream())
    $txt = $sr.ReadToEnd()
    "NG http=$([int]$r.StatusCode) $($r.StatusDescription) ct=$($r.ContentType) body_len=$($txt.Length)"
    if ($txt) { $txt }
  } else {
    "NG " + $_.Exception.Message
  }
}
