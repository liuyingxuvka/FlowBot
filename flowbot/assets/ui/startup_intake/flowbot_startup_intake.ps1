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

function Write-CancelledIntake([string]$Language = "en") {
    $cancelledDir = Join-Path $RepoRoot ".flowbot\cancelled_intake"
    New-Item -ItemType Directory -Force -Path $cancelledDir | Out-Null
    $resultPath = Join-Path $cancelledDir ("cancelled-" + [DateTime]::UtcNow.ToString("yyyyMMdd-HHmmss") + ".json")
    $result = @{
        schema_version = "flowbot.intake_result.v1"
        status = "cancelled"
        language = $Language
        controller_visibility = "cancel_status_only"
        body_text_included = $false
        recorded_at = Get-UtcNow
    }
    Write-JsonFile $resultPath $result
    return $resultPath
}

function Write-ConfirmedIntake([string]$BodyText, [bool]$BackgroundAgents, [string]$Language = "en") {
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
        language = $Language
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
        language = $Language
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
        language = $Language
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
    $resultPath = Write-ConfirmedIntake $HeadlessConfirmText $true "en"
    $runtimeOutput = Invoke-FlowBotRuntime $resultPath
    $resultPath | Write-Output
    if (-not [string]::IsNullOrWhiteSpace($runtimeOutput)) {
        $runtimeOutput | Write-Output
    }
    exit 0
}

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class FlowBotDpi {
    [DllImport("shcore.dll")]
    public static extern int SetProcessDpiAwareness(int awareness);

    [DllImport("user32.dll")]
    public static extern bool SetProcessDPIAware();
}
"@

try {
    [FlowBotDpi]::SetProcessDpiAwareness(2) | Out-Null
} catch {
    try { [FlowBotDpi]::SetProcessDPIAware() | Out-Null } catch {}
}

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName System.Xaml

$IconUri = ([System.Uri]::new($IconPath)).AbsoluteUri
$script:StartupIntakeCompleted = $false
$script:ExitCode = 0

$Xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="FlowBot"
    Width="860"
    Height="680"
    MinWidth="780"
    MinHeight="650"
    WindowStartupLocation="CenterScreen"
    Background="#FFFDF7"
    FontFamily="Segoe UI Variable Text, Segoe UI"
    TextOptions.TextFormattingMode="Display"
    TextOptions.TextRenderingMode="ClearType"
    UseLayoutRounding="True"
    SnapsToDevicePixels="True"
    ResizeMode="CanResizeWithGrip">
  <Window.Resources>
    <SolidColorBrush x:Key="InkBrush" Color="#141414" />
    <SolidColorBrush x:Key="MutedBrush" Color="#706A62" />
    <SolidColorBrush x:Key="LineBrush" Color="#E2DCD2" />
    <SolidColorBrush x:Key="PanelBrush" Color="#FFFFFF" />
    <SolidColorBrush x:Key="FieldBrush" Color="#FBFAF7" />
    <SolidColorBrush x:Key="AccentBrush" Color="#B9821D" />
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
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="Button">
            <Border
                x:Name="ButtonBorder"
                Background="{TemplateBinding Background}"
                BorderBrush="{TemplateBinding BorderBrush}"
                BorderThickness="{TemplateBinding BorderThickness}"
                CornerRadius="8">
              <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center" />
            </Border>
            <ControlTemplate.Triggers>
              <Trigger Property="IsMouseOver" Value="True">
                <Setter TargetName="ButtonBorder" Property="Background" Value="#2A2723" />
                <Setter TargetName="ButtonBorder" Property="BorderBrush" Value="#2A2723" />
              </Trigger>
              <Trigger Property="IsPressed" Value="True">
                <Setter TargetName="ButtonBorder" Property="Background" Value="#000000" />
              </Trigger>
            </ControlTemplate.Triggers>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
    <Style x:Key="LanguageChoice" TargetType="RadioButton">
      <Setter Property="Height" Value="30" />
      <Setter Property="MinWidth" Value="68" />
      <Setter Property="Foreground" Value="#625C55" />
      <Setter Property="FontSize" Value="12.5" />
      <Setter Property="FontWeight" Value="SemiBold" />
      <Setter Property="Cursor" Value="Hand" />
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="RadioButton">
            <Border
                x:Name="ChoiceBorder"
                Background="Transparent"
                BorderBrush="Transparent"
                BorderThickness="1"
                CornerRadius="15"
                Padding="10,0">
              <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center" />
            </Border>
            <ControlTemplate.Triggers>
              <Trigger Property="IsChecked" Value="True">
                <Setter TargetName="ChoiceBorder" Property="Background" Value="#141414" />
                <Setter TargetName="ChoiceBorder" Property="BorderBrush" Value="#141414" />
                <Setter Property="Foreground" Value="#FFFDF7" />
              </Trigger>
              <Trigger Property="IsMouseOver" Value="True">
                <Setter TargetName="ChoiceBorder" Property="BorderBrush" Value="#CFC7BA" />
              </Trigger>
            </ControlTemplate.Triggers>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
    <Style x:Key="ScrollBarPageButton" TargetType="RepeatButton">
      <Setter Property="Focusable" Value="False" />
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="RepeatButton">
            <Border Background="Transparent" />
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
    <Style x:Key="ScrollBarThumb" TargetType="Thumb">
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="Thumb">
            <Border Background="#CBC3B8" CornerRadius="4" />
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
    <Style TargetType="ScrollBar">
      <Setter Property="Width" Value="10" />
      <Setter Property="Background" Value="Transparent" />
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="ScrollBar">
            <Grid Background="Transparent" Width="10">
              <Track x:Name="PART_Track" IsDirectionReversed="True">
                <Track.DecreaseRepeatButton>
                  <RepeatButton Command="ScrollBar.PageUpCommand" Style="{StaticResource ScrollBarPageButton}" />
                </Track.DecreaseRepeatButton>
                <Track.Thumb>
                  <Thumb Style="{StaticResource ScrollBarThumb}" />
                </Track.Thumb>
                <Track.IncreaseRepeatButton>
                  <RepeatButton Command="ScrollBar.PageDownCommand" Style="{StaticResource ScrollBarPageButton}" />
                </Track.IncreaseRepeatButton>
              </Track>
            </Grid>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
    <Style x:Key="SwitchToggle" TargetType="ToggleButton">
      <Setter Property="Width" Value="88" />
      <Setter Property="Height" Value="40" />
      <Setter Property="Cursor" Value="Hand" />
      <Setter Property="Focusable" Value="True" />
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="ToggleButton">
            <Grid Width="88" Height="40" SnapsToDevicePixels="True">
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
              <Trigger Property="IsKeyboardFocused" Value="True">
                <Setter TargetName="Track" Property="BorderBrush" Value="#B9821D" />
              </Trigger>
            </ControlTemplate.Triggers>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
  </Window.Resources>

  <Grid Background="{StaticResource PanelBrush}" ClipToBounds="True">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto" />
      <RowDefinition Height="*" />
      <RowDefinition Height="Auto" />
    </Grid.RowDefinitions>

    <Grid Grid.Row="0" Margin="38,44,38,24">
      <Grid.ColumnDefinitions>
        <ColumnDefinition Width="Auto" />
        <ColumnDefinition Width="*" />
        <ColumnDefinition Width="Auto" />
      </Grid.ColumnDefinitions>
      <Image Grid.Column="0" Source="$IconUri" Width="56" Height="56" Margin="0,0,16,0" RenderOptions.BitmapScalingMode="HighQuality" VerticalAlignment="Center" />
      <StackPanel Grid.Column="1" VerticalAlignment="Center">
        <TextBlock x:Name="TitleText" Text="FlowBot" Foreground="{StaticResource InkBrush}" FontFamily="Segoe UI Variable Display, Segoe UI" FontSize="28" FontWeight="SemiBold" />
      </StackPanel>
      <Border
          Grid.Column="2"
          BorderBrush="Transparent"
          BorderThickness="0"
          Padding="0"
          Height="36"
          VerticalAlignment="Top"
          Background="Transparent">
        <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
          <Viewbox Width="18" Height="18" Margin="0,0,7,0">
            <Canvas Width="24" Height="24">
              <Ellipse Width="18" Height="18" Canvas.Left="3" Canvas.Top="3" Stroke="#141414" StrokeThickness="1.5" />
              <Line X1="4" Y1="9" X2="20" Y2="9" Stroke="#141414" StrokeThickness="1.5" />
              <Line X1="4" Y1="15" X2="20" Y2="15" Stroke="#141414" StrokeThickness="1.5" />
              <Path Data="M12 3 C15 6 15 18 12 21" Stroke="#141414" StrokeThickness="1.5" Fill="{x:Null}" />
              <Path Data="M12 3 C9 6 9 18 12 21" Stroke="#141414" StrokeThickness="1.5" Fill="{x:Null}" />
            </Canvas>
          </Viewbox>
          <Border Background="Transparent" CornerRadius="17" Padding="2">
            <StackPanel Orientation="Horizontal">
              <RadioButton x:Name="EnglishLanguage" GroupName="Language" IsChecked="True" Content="English" Style="{StaticResource LanguageChoice}" />
              <RadioButton x:Name="ChineseLanguage" GroupName="Language" Content="中文" Style="{StaticResource LanguageChoice}" />
            </StackPanel>
          </Border>
        </StackPanel>
      </Border>
    </Grid>

    <ScrollViewer
        Grid.Row="1"
        VerticalScrollBarVisibility="Auto"
        HorizontalScrollBarVisibility="Disabled"
        Padding="38,0,30,0">
      <Grid MinHeight="350">
        <Grid.ColumnDefinitions>
          <ColumnDefinition Width="*" MinWidth="330" />
          <ColumnDefinition Width="*" MinWidth="330" />
        </Grid.ColumnDefinitions>
        <Grid Grid.Column="0" Margin="0,0,18,0">
          <StackPanel>
            <DockPanel Margin="0,0,0,10">
              <TextBlock x:Name="RequestLabel" Text="Work request" Foreground="{StaticResource InkBrush}" FontSize="14" FontWeight="SemiBold" DockPanel.Dock="Left" />
            </DockPanel>
            <Grid>
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
              <TextBlock
                  x:Name="PlaceholderText"
                  Text="Write the instructions you want FlowBot to follow."
                  Foreground="#8D857A"
                  FontSize="14"
                  Margin="18,15,18,0"
                  TextWrapping="Wrap"
                  IsHitTestVisible="False" />
            </Grid>
          </StackPanel>
        </Grid>

        <StackPanel Grid.Column="1" VerticalAlignment="Top" Margin="6,30,0,0">
          <Grid MinHeight="82" Margin="0,0,0,26">
            <Grid.ColumnDefinitions>
              <ColumnDefinition Width="*" />
              <ColumnDefinition Width="Auto" />
            </Grid.ColumnDefinitions>
            <StackPanel Grid.Column="0" VerticalAlignment="Center">
              <TextBlock x:Name="AgentsTitle" Text="Background agents" Foreground="{StaticResource InkBrush}" FontSize="14" FontWeight="SemiBold" />
              <TextBlock x:Name="AgentsBody" Text="Allow PM and Worker agents." Foreground="{StaticResource MutedBrush}" FontSize="12.5" TextWrapping="Wrap" Margin="0,5,16,0" />
            </StackPanel>
            <ToggleButton x:Name="AgentsToggle" Grid.Column="1" IsChecked="True" Style="{StaticResource SwitchToggle}" VerticalAlignment="Center" />
          </Grid>
        </StackPanel>
      </Grid>
    </ScrollViewer>

    <Grid Grid.Row="2" Margin="38,34,38,26">
      <Grid.RowDefinitions>
        <RowDefinition Height="Auto" />
        <RowDefinition Height="Auto" />
      </Grid.RowDefinitions>
      <Button x:Name="ConfirmButton" Grid.Row="0" HorizontalAlignment="Center" Style="{StaticResource PrimaryButton}" Content="Confirm" />
      <TextBlock x:Name="StatusText" Grid.Row="1" HorizontalAlignment="Center" Foreground="{StaticResource MutedBrush}" FontSize="12.5" Margin="0,10,0,0" />
    </Grid>
  </Grid>
</Window>
"@

$Reader = [System.Xml.XmlReader]::Create([System.IO.StringReader]::new($Xaml))
$Window = [Windows.Markup.XamlReader]::Load($Reader)
$Window.Icon = [System.Windows.Media.Imaging.BitmapImage]::new([System.Uri]::new($IconPath))

$Names = @(
    "EnglishLanguage", "ChineseLanguage", "TitleText", "RequestLabel",
    "WorkRequest", "PlaceholderText", "AgentsTitle", "AgentsBody",
    "AgentsToggle", "ConfirmButton", "StatusText"
)

$Ui = @{}
foreach ($Name in $Names) {
    $Ui[$Name] = $Window.FindName($Name)
}

$Copy = @{
    en = @{
        Window = "FlowBot"
        Title = "FlowBot"
        RequestLabel = "Work request"
        Placeholder = "Write the instructions you want FlowBot to follow."
        AgentsTitle = "Background agents"
        AgentsBody = "Allow PM and Worker agents."
        Confirm = "Confirm"
        Creating = "Creating FlowBot run..."
        Confirmed = "FlowBot run completed."
        EmptyRequest = "Work request cannot be empty."
    }
    zh = @{
        Window = "FlowBot"
        Title = "FlowBot"
        RequestLabel = "工作要求"
        Placeholder = "写下你希望 FlowBot 完成的工作。"
        AgentsTitle = "后台智能体"
        AgentsBody = "启用 PM 和 Worker。"
        Confirm = "确认启动"
        Creating = "正在创建 FlowBot run..."
        Confirmed = "FlowBot run 已完成。"
        EmptyRequest = "工作要求不能为空。"
    }
}

function Get-Language {
    if ($Ui.ChineseLanguage.IsChecked) { return "zh" }
    return "en"
}

function Update-Placeholder {
    if ([string]::IsNullOrWhiteSpace($Ui.WorkRequest.Text)) {
        $Ui.PlaceholderText.Visibility = [System.Windows.Visibility]::Visible
    } else {
        $Ui.PlaceholderText.Visibility = [System.Windows.Visibility]::Collapsed
    }
}

function Apply-Language {
    $Lang = Get-Language
    $T = $Copy[$Lang]
    $Window.Title = $T.Window
    $Ui.TitleText.Text = $T.Title
    $Ui.RequestLabel.Text = $T.RequestLabel
    $Ui.PlaceholderText.Text = $T.Placeholder
    $Ui.AgentsTitle.Text = $T.AgentsTitle
    $Ui.AgentsBody.Text = $T.AgentsBody
    $Ui.ConfirmButton.Content = $T.Confirm
    $Ui.StatusText.Text = ""
}

$Ui.EnglishLanguage.Add_Checked({ Apply-Language })
$Ui.ChineseLanguage.Add_Checked({ Apply-Language })
$Ui.WorkRequest.Add_TextChanged({ Update-Placeholder })
Apply-Language
Update-Placeholder

$Ui.ConfirmButton.Add_Click({
    $Lang = Get-Language
    $T = $Copy[$Lang]
    try {
        if ([string]::IsNullOrWhiteSpace($Ui.WorkRequest.Text)) {
            throw $T.EmptyRequest
        }
        $Ui.StatusText.Text = $T.Creating
        $resultPath = Write-ConfirmedIntake $Ui.WorkRequest.Text ([bool]$Ui.AgentsToggle.IsChecked) $Lang
        $runtimeOutput = Invoke-FlowBotRuntime $resultPath
        $script:StartupIntakeCompleted = $true
        $script:ExitCode = 0
        $Ui.StatusText.Text = $T.Confirmed
        $Window.Tag = $runtimeOutput
        $Window.Close()
    } catch {
        $Ui.StatusText.Text = $_.Exception.Message
    }
})

if ($SmokeTest) {
    "UI_SMOKE_OK"
    exit 0
}

$Window.Add_Closing({
    if (-not $script:StartupIntakeCompleted) {
        try {
            Write-CancelledIntake (Get-Language) | Out-Null
            $script:ExitCode = 0
        } catch {
            $script:ExitCode = 1
        }
    }
})

$Window.ShowDialog() | Out-Null
exit $script:ExitCode
