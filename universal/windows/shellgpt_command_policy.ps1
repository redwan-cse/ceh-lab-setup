param([Parameter(Mandatory=$true)][string]$CommandBase64)
$ErrorActionPreference = 'Stop'
function Deny([string]$reason) {
    @{ automatic = $false; reason = $reason; command = '' } | ConvertTo-Json -Compress
    exit 0
}
try {
    $command = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($CommandBase64))
    if ([string]::IsNullOrWhiteSpace($command)) { Deny 'Empty command' }
    # Reject syntax that can invoke hidden code or add additional statements.
    # Literal strings containing these characters also require approval.
    if ($command -match '[\r\n;`$&><{}()@#=]') { Deny 'Script, compound command, redirection, or dynamic expression' }
    $parseErrors = $null
    $tokens = $null
    $ast = [Management.Automation.Language.Parser]::ParseInput($command, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count) { Deny 'PowerShell parse error' }
    if ($ast.ParamBlock -or $ast.BeginBlock -or $ast.ProcessBlock -or
        $ast.EndBlock.Statements.Count -ne 1 -or
        $ast.EndBlock.Statements[0] -isnot [Management.Automation.Language.PipelineAst]) {
        Deny 'Only one literal inspection pipeline is automatic'
    }
    $allowedNodes = @('ScriptBlockAst','NamedBlockAst','PipelineAst','CommandAst',
        'CommandParameterAst','StringConstantExpressionAst','ConstantExpressionAst','ArrayLiteralAst')
    foreach ($node in $ast.FindAll({param($node) $true}, $true)) {
        if ($node.GetType().Name -notin $allowedNodes) { Deny 'Expression requires approval' }
    }
    # Exact command names and parameter names only. Aliases and executable files
    # are deliberately not auto-approved. Module-qualified names prevent function
    # shadowing; the runner restricts PSModulePath to the system modules folder.
    $management = 'Microsoft.PowerShell.Management'
    $utility = 'Microsoft.PowerShell.Utility'
    $commands = @{
        'Get-Location' = @($management, @('PSDrive','PSProvider'))
        'Get-ChildItem' = @($management, @('Path','LiteralPath','Filter','Include','Exclude','Recurse','Depth','Force','Name','Directory','File','Hidden','ReadOnly','System','Attributes'))
        'Get-Content' = @($management, @('Path','LiteralPath','Filter','Include','Exclude','Force','ReadCount','TotalCount','Tail','Raw','Encoding','Delimiter','Wait','Stream'))
        'Get-Item' = @($management, @('Path','LiteralPath','Filter','Include','Exclude','Force','Stream'))
        'Get-ItemProperty' = @($management, @('Path','LiteralPath','Name','Filter','Include','Exclude','Force'))
        'Get-PSDrive' = @($management, @('Name','PSProvider','Scope'))
        'Test-Path' = @($management, @('Path','LiteralPath','PathType','IsValid','OlderThan','NewerThan','Filter','Include','Exclude'))
        'Resolve-Path' = @($management, @('Path','LiteralPath','Relative'))
        'Get-Process' = @($management, @('Name','Id','Module','FileVersionInfo','IncludeUserName'))
        'Get-Service' = @($management, @('Name','DisplayName','DependentServices','RequiredServices','Include','Exclude'))
        'Get-Date' = @($utility, @('Date','Year','Month','Day','Hour','Minute','Second','Millisecond','DisplayHint','Format','UFormat'))
        'Get-Host' = @($utility, @())
        'Select-Object' = @($utility, @('Property','ExcludeProperty','ExpandProperty','First','Last','Skip','SkipLast','Unique','Wait'))
        'Sort-Object' = @($utility, @('Property','Descending','Unique','CaseSensitive','Culture'))
        'Measure-Object' = @($utility, @('Property','Sum','Average','Maximum','Minimum','Line','Word','Character','IgnoreWhiteSpace'))
        'Format-Table' = @($utility, @('Property','AutoSize','HideTableHeaders','Wrap','GroupBy'))
        'Format-List' = @($utility, @('Property','GroupBy','Force'))
    }
    $replacements = @()
    foreach ($element in $ast.EndBlock.Statements[0].PipelineElements) {
        if ($element -isnot [Management.Automation.Language.CommandAst] -or
            $element.InvocationOperator.ToString() -ne 'Unknown' -or $element.Redirections.Count) {
            Deny 'Invocation or redirection requires approval'
        }
        $name = $element.GetCommandName()
        if (-not $name) { Deny 'Dynamic command name' }
        $parts = $name -split '\\'
        $short = $parts[-1]
        if (-not $commands.ContainsKey($short)) { Deny 'Command is outside the automatic inspection list' }
        $definition = $commands[$short]
        $qualified = $definition[0] + '\' + $short
        if ($parts.Count -gt 1 -and $name -ine $qualified) { Deny 'Untrusted module qualification' }
        foreach ($argument in $element.CommandElements) {
            if ($argument -is [Management.Automation.Language.CommandParameterAst] -and
                $argument.ParameterName -notin $definition[1]) { Deny 'Parameter requires approval' }
        }
        $extent = $element.CommandElements[0].Extent
        $replacements += @{start=$extent.StartOffset; length=($extent.EndOffset-$extent.StartOffset); value=$qualified}
    }
    $rewritten = $command
    foreach ($replacement in ($replacements | Sort-Object { $_.start } -Descending)) {
        $rewritten = $rewritten.Remove($replacement.start, $replacement.length).Insert($replacement.start, $replacement.value)
    }
    @{automatic=$true; reason='Recognized literal inspection pipeline'; command=$rewritten} | ConvertTo-Json -Compress
} catch {
    Deny 'Policy evaluation failed'
}
