param(
    [string]$ProjectRoot = "",
    [string]$HeadlessConfirmText = "",
    [switch]$HeadlessCancel,
    [switch]$NoRun,
    [switch]$SmokeTest
)

$ErrorActionPreference = "Stop"

function Find-FlowBotRepoRoot {
    if (-not [string]::IsNullOrWhiteSpace($ProjectRoot)) {
        return [System.IO.Path]::GetFullPath($ProjectRoot)
    }
    $cursor = [System.IO.DirectoryInfo]::new($PSScriptRoot)
    while ($null -ne $cursor) {
        $runtime = Join-Path $cursor.FullName "flowbot\runtime.py"
        $openspec = Join-Path $cursor.FullName "openspec\config.yaml"
        if ((Test-Path -LiteralPath $runtime) -and (Test-Path -LiteralPath $openspec)) {
            return $cursor.FullName
        }
        $cursor = $cursor.Parent
    }
    throw "Unable to locate FlowBot repository from $PSScriptRoot"
}

$RepoRoot = Find-FlowBotRepoRoot
$IconPath = Join-Path $RepoRoot "assets\brand\flowbot-icon.png"
if (-not (Test-Path -LiteralPath $IconPath)) {
    throw "Missing FlowBot icon: $IconPath"
}

function Get-UtcNow {
    return [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function New-FlowBotRunId {
    return "run-" + [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss")
}

function Write-Utf8NoBomText([string]$Path, [string]$Value) {
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $Value, $encoding)
}

function Write-JsonFile([string]$Path, [hashtable]$Payload) {
    $json = $Payload | ConvertTo-Json -Depth 20
    Write-Utf8NoBomText -Path $Path -Value ($json + [Environment]::NewLine)
}

function Get-ProjectRelativePath([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd('\') + '\'
    if ($full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $full.Substring($root.Length).Replace('\', '/')
    }
    return $full
}

function Get-FileSha256([string]$Path) {
    $stream = [System.IO.File]::OpenRead($Path)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $sha.ComputeHash($stream)
        return ([System.BitConverter]::ToString($hash)).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
        $stream.Dispose()
    }
}

function Write-CancelledIntake {
    $cancelledDir = Join-Path $RepoRoot ".flowbot\cancelled_intake"
    New-Item -ItemType Directory -Force -Path $cancelledDir | Out-Null
    $resultPath = Join-Path $cancelledDir ("cancelled-" + [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss") + ".json")
    $result = @{
        schema_version = "flowbot.intake_result.v1"
        status = "cancelled"
        controller_visibility = "cancel_status_only"
        body_text_included = $false
        recorded_at = Get-UtcNow
    }
    Write-JsonFile $resultPath $result
    return $resultPath
}

function Write-ConfirmedIntake([string]$BodyText, [bool]$BackgroundAgents) {
    if ([string]::IsNullOrWhiteSpace($BodyText)) {
        throw "Work request cannot be empty."
    }

    $runId = New-FlowBotRunId
    $intakeDir = Join-Path $RepoRoot ".flowbot\runs\$runId\intake"
    New-Item -ItemType Directory -Force -Path $intakeDir | Out-Null

    $recordedAt = Get-UtcNow
    $answers = @{
        background_agents = $(if ($BackgroundAgents) { "allow" } else { "single-agent" })
        provenance = "explicit_user_reply"
    }
    $bodyPath = Join-Path $intakeDir "flowbot_intake_body.md"
    $receiptPath = Join-Path $intakeDir "flowbot_intake_receipt.json"
    $envelopePath = Join-Path $intakeDir "flowbot_intake_envelope.json"
    $resultPath = Join-Path $intakeDir "flowbot_intake_result.json"

    Write-Utf8NoBomText -Path $bodyPath -Value ($BodyText.Trim() + [Environment]::NewLine)
    $bodyHash = Get-FileSha256 $bodyPath

    $receipt = @{
        schema_version = "flowbot.intake_receipt.v1"
        status = "confirmed"
        ui_surface = "native_wpf_startup_intake"
        startup_answers = $answers
        confirmed_by_user = $true
        cancelled_by_user = $false
        body_path = Get-ProjectRelativePath $bodyPath
        body_hash = $bodyHash
        envelope_path = Get-ProjectRelativePath $envelopePath
        body_text_included = $false
        recorded_at = $recordedAt
    }
    Write-JsonFile $receiptPath $receipt

    $envelope = @{
        schema_version = "flowbot.intake_envelope.v1"
        status = "confirmed"
        source = "native_wpf_startup_intake"
        startup_answers = $answers
        body_path = Get-ProjectRelativePath $bodyPath
        body_hash = $bodyHash
        receipt_path = Get-ProjectRelativePath $receiptPath
        body_visibility = "sealed_pm_only"
        controller_visibility = "envelope_only"
        controller_may_read_body = $false
        body_text_included = $false
        recorded_at = $recordedAt
    }
    Write-JsonFile $envelopePath $envelope

    $result = @{
        schema_version = "flowbot.intake_result.v1"
        status = "confirmed"
        run_id = $runId
        startup_answers = $answers
        receipt_path = Get-ProjectRelativePath $receiptPath
        envelope_path = Get-ProjectRelativePath $envelopePath
        body_path = Get-ProjectRelativePath $bodyPath
        body_hash = $bodyHash
        controller_visibility = "envelope_only"
        controller_may_read_body = $false
        body_text_included = $false
        recorded_at = $recordedAt
    }
    Write-JsonFile $resultPath $result
    return $resultPath
}

function Invoke-FlowBotRuntime([string]$ResultPath) {
    if ($NoRun) {
        return ""
    }
    $runner = Join-Path $RepoRoot "scripts\run_flowbot_from_intake.py"
    if (-not (Test-Path -LiteralPath $runner)) {
        throw "Missing FlowBot runner: $runner"
    }
    $output = & python $runner --project-root $RepoRoot --intake-result $ResultPath
    if ($LASTEXITCODE -ne 0) {
        throw "FlowBot runtime failed for intake: $ResultPath"
    }
    return ($output -join [Environment]::NewLine)
}

if ($HeadlessCancel) {
    Write-CancelledIntake | Write-Output
    exit 0
}

if (-not [string]::IsNullOrWhiteSpace($HeadlessConfirmText)) {
    $resultPath = Write-ConfirmedIntake $HeadlessConfirmText $true
    $runtimeOutput = Invoke-FlowBotRuntime $resultPath
    $resultPath | Write-Output
    if (-not [string]::IsNullOrWhiteSpace($runtimeOutput)) {
        $runtimeOutput | Write-Output
    }
    exit 0
}

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName System.Xaml

if ($SmokeTest) {
    "UI_SMOKE_OK"
    exit 0
}

$IconUri = ([System.Uri]::new($IconPath)).AbsoluteUri
$script:StartupIntakeCompleted = $false
$script:ExitCode = 0

$Xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="FlowBot"
    Width="860"
    Height="620"
    MinWidth="760"
    MinHeight="560"
    WindowStartupLocation="CenterScreen"
    Background="#FFFDF7"
    FontFamily="Segoe UI Variable Text, Segoe UI"
    ResizeMode="CanResizeWithGrip">
  <Window.Resources>
    <SolidColorBrush x:Key="InkBrush" Color="#141414" />
    <SolidColorBrush x:Key="MutedBrush" Color="#706A62" />
    <SolidColorBrush x:Key="LineBrush" Color="#E2DCD2" />
    <SolidColorBrush x:Key="FieldBrush" Color="#FBFAF7" />
    <Style x:Key="PrimaryButton" TargetType="Button">
      <Setter Property="MinWidth" Value="132" />
      <Setter Property="Height" Value="44" />
      <Setter Property="Padding" Value="20,0" />
      <Setter Property="Foreground" Value="#FFFDF7" />
      <Setter Property="Background" Value="#141414" />
      <Setter Property="BorderBrush" Value="#141414" />
      <Setter Property="BorderThickness" Value="1" />
      <Setter Property="FontWeight" Value="SemiBold" />
      <Setter Property="Cursor" Value="Hand" />
    </Style>
    <Style x:Key="SwitchToggle" TargetType="ToggleButton">
      <Setter Property="Width" Value="88" />
      <Setter Property="Height" Value="40" />
      <Setter Property="Cursor" Value="Hand" />
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="ToggleButton">
            <Grid Width="88" Height="40">
              <Border x:Name="Track" Background="#141414" BorderBrush="#141414" BorderThickness="1" CornerRadius="20" />
              <TextBlock x:Name="StateLabel" Text="ON" Foreground="#FFFDF7" FontSize="10" FontWeight="Bold" HorizontalAlignment="Left" VerticalAlignment="Center" Margin="15,0,0,0" />
              <Ellipse x:Name="Knob" Width="30" Height="30" Fill="#FFFDF7" Stroke="#D8CFC1" StrokeThickness="1" HorizontalAlignment="Right" VerticalAlignment="Center" Margin="4" />
            </Grid>
            <ControlTemplate.Triggers>
              <Trigger Property="IsChecked" Value="False">
                <Setter TargetName="Track" Property="Background" Value="#D6D0C7" />
                <Setter TargetName="Track" Property="BorderBrush" Value="#A69E94" />
                <Setter TargetName="StateLabel" Property="Text" Value="OFF" />
                <Setter TargetName="StateLabel" Property="Foreground" Value="#514B44" />
                <Setter TargetName="StateLabel" Property="HorizontalAlignment" Value="Right" />
                <Setter TargetName="StateLabel" Property="Margin" Value="0,0,12,0" />
                <Setter TargetName="Knob" Property="HorizontalAlignment" Value="Left" />
              </Trigger>
            </ControlTemplate.Triggers>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
  </Window.Resources>

  <Grid Margin="38">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto" />
      <RowDefinition Height="*" />
      <RowDefinition Height="Auto" />
    </Grid.RowDefinitions>

    <Grid Grid.Row="0" Margin="0,0,0,26">
      <Grid.ColumnDefinitions>
        <ColumnDefinition Width="Auto" />
        <ColumnDefinition Width="*" />
      </Grid.ColumnDefinitions>
      <Image Grid.Column="0" Source="$IconUri" Width="56" Height="56" Margin="0,0,16,0" RenderOptions.BitmapScalingMode="HighQuality" />
      <StackPanel Grid.Column="1" VerticalAlignment="Center">
        <TextBlock Text="FlowBot" Foreground="{StaticResource InkBrush}" FontFamily="Segoe UI Variable Display, Segoe UI" FontSize="28" FontWeight="SemiBold" />
        <TextBlock Text="Model-first startup intake" Foreground="{StaticResource MutedBrush}" FontSize="13" Margin="0,5,0,0" />
      </StackPanel>
    </Grid>

    <Grid Grid.Row="1">
      <Grid.ColumnDefinitions>
        <ColumnDefinition Width="*" MinWidth="360" />
        <ColumnDefinition Width="260" />
      </Grid.ColumnDefinitions>
      <StackPanel Grid.Column="0" Margin="0,0,24,0">
        <TextBlock Text="工作要求" Foreground="{StaticResource InkBrush}" FontSize="14" FontWeight="SemiBold" Margin="0,0,0,10" />
        <TextBox
            x:Name="WorkRequest"
            MinHeight="318"
            AcceptsReturn="True"
            TextWrapping="Wrap"
            VerticalScrollBarVisibility="Auto"
            BorderBrush="#C9BFAF"
            BorderThickness="1"
            Background="{StaticResource FieldBrush}"
            Foreground="{StaticResource InkBrush}"
            FontSize="14"
            Padding="14"
            SpellCheck.IsEnabled="True" />
      </StackPanel>
      <StackPanel Grid.Column="1" VerticalAlignment="Top" Margin="0,32,0,0">
        <Grid MinHeight="82">
          <Grid.ColumnDefinitions>
            <ColumnDefinition Width="*" />
            <ColumnDefinition Width="Auto" />
          </Grid.ColumnDefinitions>
          <StackPanel Grid.Column="0" VerticalAlignment="Center">
            <TextBlock Text="后台智能体" Foreground="{StaticResource InkBrush}" FontSize="14" FontWeight="SemiBold" />
            <TextBlock Text="启用 PM 和 Worker。" Foreground="{StaticResource MutedBrush}" FontSize="12.5" TextWrapping="Wrap" Margin="0,5,16,0" />
          </StackPanel>
          <ToggleButton x:Name="AgentsToggle" Grid.Column="1" IsChecked="True" Style="{StaticResource SwitchToggle}" VerticalAlignment="Center" />
        </Grid>
      </StackPanel>
    </Grid>

    <Grid Grid.Row="2" Margin="0,30,0,0">
      <Grid.RowDefinitions>
        <RowDefinition Height="Auto" />
        <RowDefinition Height="Auto" />
      </Grid.RowDefinitions>
      <Button x:Name="ConfirmButton" Grid.Row="0" HorizontalAlignment="Center" Style="{StaticResource PrimaryButton}" Content="确认启动" />
      <TextBlock x:Name="StatusText" Grid.Row="1" HorizontalAlignment="Center" Foreground="{StaticResource MutedBrush}" FontSize="12.5" Margin="0,10,0,0" />
    </Grid>
  </Grid>
</Window>
"@

$Reader = [System.Xml.XmlReader]::Create([System.IO.StringReader]::new($Xaml))
$Window = [Windows.Markup.XamlReader]::Load($Reader)
$Window.Icon = [System.Windows.Media.Imaging.BitmapImage]::new([System.Uri]::new($IconPath))
$WorkRequest = $Window.FindName("WorkRequest")
$AgentsToggle = $Window.FindName("AgentsToggle")
$ConfirmButton = $Window.FindName("ConfirmButton")
$StatusText = $Window.FindName("StatusText")

$ConfirmButton.Add_Click({
    try {
        $StatusText.Text = "正在创建 FlowBot run..."
        $resultPath = Write-ConfirmedIntake $WorkRequest.Text ([bool]$AgentsToggle.IsChecked)
        $runtimeOutput = Invoke-FlowBotRuntime $resultPath
        $script:StartupIntakeCompleted = $true
        $script:ExitCode = 0
        $StatusText.Text = "FlowBot run 已完成。"
        $Window.Tag = $runtimeOutput
        $Window.Close()
    } catch {
        $StatusText.Text = $_.Exception.Message
    }
})

$Window.Add_Closing({
    if (-not $script:StartupIntakeCompleted) {
        try {
            Write-CancelledIntake | Out-Null
            $script:ExitCode = 0
        } catch {
            $script:ExitCode = 1
        }
    }
})

$Window.ShowDialog() | Out-Null
exit $script:ExitCode
