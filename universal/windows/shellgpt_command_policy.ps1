param([Parameter(Mandatory=$true)][string]$CommandBase64)
$ErrorActionPreference = 'Stop'
function Deny([string]$reason) {
    @{ automatic = $false; reason = $reason; command = '' } | ConvertTo-Json -Compress
    exit 0
}
function LiteralValue($node) {
    if($node -is [Management.Automation.Language.StringConstantExpressionAst]){return [string]$node.Value}
    if($node -is [Management.Automation.Language.VariableExpressionAst] -and $node.VariablePath.UserPath -ieq 'env:CEH_EXAM_DIR'){return $env:CEH_EXAM_DIR}
    if($node -is [Management.Automation.Language.ExpandableStringExpressionAst]){
        return ([string]$node.Value).Replace('${env:CEH_EXAM_DIR}',$env:CEH_EXAM_DIR).Replace('$env:CEH_EXAM_DIR',$env:CEH_EXAM_DIR)
    }
    Deny 'A literal argument is required'
}
function Argument($element,[string]$name) {
    $items=$element.CommandElements
    for($i=1;$i -lt $items.Count;$i++){
        if($items[$i] -is [Management.Automation.Language.CommandParameterAst] -and $items[$i].ParameterName -ieq $name){
            if($items[$i].Argument){return LiteralValue $items[$i].Argument}
            if($i+1 -lt $items.Count -and $items[$i+1] -isnot [Management.Automation.Language.CommandParameterAst]){return LiteralValue $items[$i+1]}
            Deny 'Missing parameter value'
        }
    }
    return $null
}
function ScopedOutput([string]$value,[bool]$append) {
    if(-not $value -or -not $env:CEH_EXAM_DIR){Deny 'Use an explicit output inside the exam folder'}
    $root=[IO.Path]::GetFullPath($env:CEH_EXAM_DIR).TrimEnd('\','/')
    $path=[IO.Path]::GetFullPath($value)
    if(-not $path.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){Deny 'Output outside exam folder'}
    $relative=$path.Substring($root.Length+1)
    if($relative -match '(^|\\)\.|[:*?\[\]]' -or [IO.Path]::GetFileName($path) -in @('terminal.md','terminal.txt','findings.txt')){Deny 'Reserved or nonliteral evidence file'}
    $parent=Split-Path -Parent $path
    if(-not (Test-Path -LiteralPath $parent -PathType Container)){Deny 'Output parent missing'}
    $cursor=$path
    while($cursor){
        $info=Get-Item -LiteralPath $cursor -Force -ErrorAction SilentlyContinue
        if($null -ne $info -and $info.Attributes -band [IO.FileAttributes]::ReparsePoint){Deny 'Redirected output path'}
        $next=Split-Path -Parent $cursor
        if($next -eq $cursor){break};$cursor=$next
    }
    if((Test-Path -LiteralPath $path) -and (-not $append -or -not (Test-Path -LiteralPath $path -PathType Leaf))){Deny 'Existing evidence would be overwritten'}
    if($script:AutomaticOutputs.ContainsKey($path) -and -not $append){Deny 'Repeated output would overwrite evidence'}
    $script:AutomaticOutputs[$path]=$true
}
try {
    $script:AutomaticOutputs=@{}
    $command = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($CommandBase64))
    if ([string]::IsNullOrWhiteSpace($command)) { Deny 'Empty command' }
    # Reject syntax that can invoke hidden code or add additional statements.
    # Literal strings containing these characters also require approval.
    if ($command -match '[\r\n]') { Deny 'Multiline script requires approval' }
    $parseErrors = $null
    $tokens = $null
    $ast = [Management.Automation.Language.Parser]::ParseInput($command, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count) { Deny 'PowerShell parse error' }
    if(@($tokens | Where-Object {$_.Kind.ToString() -eq 'Comment'}).Count){Deny 'Comments require approval'}
    if ($ast.ParamBlock -or $ast.BeginBlock -or $ast.ProcessBlock -or
        $ast.EndBlock.Statements.Count -lt 1) {
        Deny 'Only literal routine pipelines are automatic'
    }
    foreach($statement in $ast.EndBlock.Statements){if($statement -isnot [Management.Automation.Language.PipelineAst]){Deny 'Script requires approval'}}
    $allowedNodes = @('ScriptBlockAst','NamedBlockAst','PipelineAst','CommandAst',
        'CommandParameterAst','StringConstantExpressionAst','ConstantExpressionAst','ArrayLiteralAst','VariableExpressionAst','ExpandableStringExpressionAst')
    foreach ($node in $ast.FindAll({param($node) $true}, $true)) {
        if ($node.GetType().Name -notin $allowedNodes) { Deny 'Expression requires approval' }
        if($node -is [Management.Automation.Language.VariableExpressionAst] -and $node.VariablePath.UserPath -ine 'env:CEH_EXAM_DIR'){Deny 'Dynamic variable requires approval'}
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
        'Select-String' = @($utility, @('Path','LiteralPath','Pattern','SimpleMatch','CaseSensitive','AllMatches','List','Quiet','NotMatch','Include','Exclude','Context','Encoding'))
        'Get-FileHash' = @($utility, @('Path','LiteralPath','Algorithm'))
        'Write-Output' = @($utility, @('InputObject','NoEnumerate'))
        'Resolve-DnsName' = @('DnsClient', @('Name','Type','Server','DnsOnly','NoHostsFile','QuickTimeout','TcpOnly'))
        'Get-CimInstance' = @('CimCmdlets', @('ClassName','Namespace','Filter','Property','Query','ComputerName','OperationTimeoutSec'))
        'Invoke-WebRequest' = @($utility, @('Uri','UseBasicParsing','Method','UserAgent','TimeoutSec','MaximumRedirection','OutFile'))
        'Out-File' = @($utility, @('FilePath','Encoding','Append','NoClobber','Width','NoNewline'))
    }
    $replacements = @()
    foreach($statement in $ast.EndBlock.Statements){
    foreach ($element in $statement.PipelineElements) {
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
            if($argument -is [Management.Automation.Language.CommandParameterAst] -and $argument.ParameterName -in @('Append','NoClobber','UseBasicParsing') -and $argument.Argument){Deny 'Use plain safety switches, not explicit switch values'}
        }
        $parameters=@($element.CommandElements | Where-Object {$_ -is [Management.Automation.Language.CommandParameterAst]} | ForEach-Object {$_.ParameterName})
        if($short -ieq 'Invoke-WebRequest'){
            $uriValue=Argument $element 'Uri';$uri=$null
            if(-not [uri]::TryCreate($uriValue,[UriKind]::Absolute,[ref]$uri) -or $uri.Scheme -notin @('http','https') -or -not $uri.Host){Deny 'Use an explicit HTTP(S) URI'}
            $method=Argument $element 'Method';if($method -and $method -notin @('GET','HEAD')){Deny 'Non-read-only HTTP method'}
            $out=Argument $element 'OutFile';if($out){ScopedOutput $out $false}
            if($parameters -notcontains 'UseBasicParsing'){$qualified+=' -UseBasicParsing'}
        }
        if($short -ieq 'Out-File'){
            ScopedOutput (Argument $element 'FilePath') ($parameters -contains 'Append')
            if($parameters -notcontains 'Append' -and $parameters -notcontains 'NoClobber'){$qualified+=' -NoClobber'}
        }
        $extent = $element.CommandElements[0].Extent
        $replacements += @{start=$extent.StartOffset; length=($extent.EndOffset-$extent.StartOffset); value=$qualified}
    }
    }
    $rewritten = $command
    foreach ($replacement in ($replacements | Sort-Object { $_.start } -Descending)) {
        $rewritten = $rewritten.Remove($replacement.start, $replacement.length).Insert($replacement.start, $replacement.value)
    }
    @{automatic=$true; reason='Recognized literal inspection pipeline'; command=$rewritten} | ConvertTo-Json -Compress
} catch {
    Deny 'Policy evaluation failed'
}
