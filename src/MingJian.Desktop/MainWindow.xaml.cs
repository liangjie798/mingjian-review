using DiffPlex.DiffBuilder;
using DiffPlex.DiffBuilder.Model;
using Microsoft.Win32;
using MingJian.Desktop.Services;
using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;

namespace MingJian.Desktop;

public partial class MainWindow : Window
{
    private readonly ObservableCollection<ReviewFile> _files = [];
    private readonly ObservableCollection<Finding> _findings = [];
    private readonly ReviewEngine _engine = new();
    private ModelSettings _settings = ModelService.LoadSettings();
    private ReviewScenario _scenario = ReviewScenario.Competition;
    private bool _dark = true;
    private string? _leftContract;
    private string? _rightContract;
    private Button? _selectedNav;

    public MainWindow()
    {
        InitializeComponent();
        FilesList.ItemsSource = _files;
        FindingsList.ItemsSource = _findings;
        UpdateScenario();
        UpdateModelStatus();
        Loaded += (_, _) => ShowPage(ReviewPage, "材料审查", ReviewNav);
    }

    private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ClickCount == 2) ToggleMaximize(); else if (e.LeftButton == MouseButtonState.Pressed) DragMove();
    }
    private void Minimize_Click(object sender, RoutedEventArgs e) => WindowState = WindowState.Minimized;
    private void Maximize_Click(object sender, RoutedEventArgs e) => ToggleMaximize();
    private void ToggleMaximize() => WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;
    private void Close_Click(object sender, RoutedEventArgs e) => Close();

    private void ReviewNav_Click(object sender, RoutedEventArgs e) => ShowPage(ReviewPage, "材料审查", ReviewNav);
    private void CompareNav_Click(object sender, RoutedEventArgs e) => ShowPage(ComparePage, "合同对比", CompareNav);
    private void GuideNav_Click(object sender, RoutedEventArgs e) => ShowPage(GuidePage, "使用指南", GuideNav);

    private void ShowPage(UIElement page, string label, Button nav)
    {
        foreach (var element in new[] { ReviewPage, ComparePage, GuidePage }) element.Visibility = element == page ? Visibility.Visible : Visibility.Collapsed;
        _selectedNav = nav;
        ApplyNavigationStyles();
        WindowSection.Text = label;
        AnimatePage(page);
    }

    private void ApplyNavigationStyles()
    {
        foreach (var button in new[] { ReviewNav, CompareNav, GuideNav })
        {
            button.Background = button == _selectedNav ? (Brush)FindResource("AccentDarkBrush") : Brushes.Transparent;
            button.Foreground = button == _selectedNav ? (Brush)FindResource("AccentBrush") : (Brush)FindResource("MutedBrush");
        }
    }

    private static void AnimatePage(UIElement page)
    {
        var transform = new TranslateTransform(18, 0);
        page.RenderTransform = transform;
        page.Opacity = 0;
        var easing = new CubicEase { EasingMode = EasingMode.EaseOut };
        page.BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(240)) { EasingFunction = easing });
        transform.BeginAnimation(TranslateTransform.XProperty, new DoubleAnimation(18, 0, TimeSpan.FromMilliseconds(300)) { EasingFunction = easing });
    }

    private void Competition_Click(object sender, RoutedEventArgs e) { _scenario = ReviewScenario.Competition; UpdateScenario(); }
    private void Contract_Click(object sender, RoutedEventArgs e) { _scenario = ReviewScenario.Contract; UpdateScenario(); }
    private void UpdateScenario()
    {
        var competition = _scenario == ReviewScenario.Competition;
        PageTitle.Text = competition ? "大学生竞赛材料审查" : "合同条款审查";
        PageSubtitle.Text = competition ? "核对材料完整性、团队信息与跨文件一致性" : "检查主体、付款、验收、违约责任与关键条款风险";
        ApplyScenarioStyles();
        _findings.Clear();
        ExportButton.IsEnabled = false;
        UpdateMetrics();
        ClearDetail();
    }

    private void ApplyScenarioStyles()
    {
        var competition = _scenario == ReviewScenario.Competition;
        CompetitionButton.Background = competition ? (Brush)FindResource("AccentDarkBrush") : Brushes.Transparent;
        CompetitionButton.Foreground = competition ? (Brush)FindResource("AccentBrush") : (Brush)FindResource("MutedBrush");
        ContractButton.Background = !competition ? (Brush)FindResource("AccentDarkBrush") : Brushes.Transparent;
        ContractButton.Foreground = !competition ? (Brush)FindResource("AccentBrush") : (Brush)FindResource("MutedBrush");
    }

    private void AddFiles_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog { Multiselect = true, Filter = "支持的材料|*.pdf;*.docx;*.xlsx;*.txt;*.md;*.csv;*.json|所有文件|*.*" };
        if (dialog.ShowDialog(this) == true) AddFiles(dialog.FileNames);
    }
    private void DropZone_DragEnter(object sender, DragEventArgs e) => e.Effects = e.Data.GetDataPresent(DataFormats.FileDrop) ? DragDropEffects.Copy : DragDropEffects.None;
    private void DropZone_Drop(object sender, DragEventArgs e)
    {
        if (e.Data.GetData(DataFormats.FileDrop) is string[] paths) AddFiles(paths);
    }
    private void AddFiles(IEnumerable<string> paths)
    {
        foreach (var path in paths.Where(File.Exists).Where(x => DocumentParser.Supported.Contains(Path.GetExtension(x))))
            if (_files.All(x => !string.Equals(x.Path, path, StringComparison.OrdinalIgnoreCase))) _files.Add(new() { Path = path });
        FileMetric.Text = _files.Count.ToString();
        StatusText.Text = _files.Count == 0 ? "添加材料后开始审查" : $"已添加 {_files.Count} 份材料，可以开始审查";
    }
    private void RemoveFile_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button { Tag: ReviewFile file }) _files.Remove(file);
        FileMetric.Text = _files.Count.ToString();
    }

    private async void StartReview_Click(object sender, RoutedEventArgs e)
    {
        if (_files.Count == 0) { MessageBox.Show(this, "请先添加需要审查的材料。", "尚未添加文件", MessageBoxButton.OK, MessageBoxImage.Information); return; }
        StartButton.IsEnabled = false;
        ReviewProgress.Visibility = Visibility.Visible;
        var progress = new Progress<string>(message => StatusText.Text = message);
        try
        {
            var result = await _engine.ReviewAsync(_scenario, _files.Select(x => x.Path), _settings, progress);
            _findings.Clear();
            foreach (var finding in result.Findings.OrderBy(x => x.Severity)) _findings.Add(finding);
            StatusText.Text = result.ModelStatus;
            FindingCountLabel.Text = _findings.Count == 0 ? "未发现明显问题" : $"{_findings.Count} 项待核对";
            UpdateMetrics();
            ExportButton.IsEnabled = true;
            if (_findings.Count > 0) FindingsList.SelectedIndex = 0;
        }
        catch (Exception error) { MessageBox.Show(this, error.Message, "审查未完成", MessageBoxButton.OK, MessageBoxImage.Warning); StatusText.Text = "审查未完成"; }
        finally { StartButton.IsEnabled = true; ReviewProgress.Visibility = Visibility.Collapsed; }
    }

    private void UpdateMetrics()
    {
        BlockingMetric.Text = _findings.Count(x => x.Severity == RiskLevel.Blocking).ToString();
        HighMetric.Text = _findings.Count(x => x.Severity == RiskLevel.High).ToString();
        TotalMetric.Text = _findings.Count.ToString();
    }
    private void ExportReport_Click(object sender, RoutedEventArgs e)
    {
        if (_findings.Count == 0) return;
        var dialog = new SaveFileDialog { Filter = "Markdown 报告|*.md", FileName = $"明鉴审查报告-{DateTime.Now:yyyyMMdd-HHmm}.md" };
        if (dialog.ShowDialog(this) != true) return;
        var lines = new List<string>
        {
            "# 明鉴材料审查报告", "", $"- 审查场景：{(_scenario == ReviewScenario.Contract ? "合同审查" : "大学生竞赛材料审查")}",
            $"- 生成时间：{DateTime.Now:yyyy-MM-dd HH:mm}", $"- 材料数量：{_files.Count}", $"- 待核对项：{_findings.Count}", "", "## 审查发现", ""
        };
        foreach (var item in _findings)
        {
            lines.Add($"### [{item.SeverityLabel}] {item.Title}"); lines.Add("");
            lines.Add($"- 编号：{item.Id}"); lines.Add($"- 来源：{item.SourceLabel}"); lines.Add($"- 文件：{item.Evidence.File}（第 {item.Evidence.Page} 页）");
            lines.Add($"- 说明：{item.Detail}"); lines.Add($"- 原文：{item.Evidence.Excerpt}"); lines.Add($"- 建议：{item.Suggestion}"); lines.Add("");
        }
        lines.Add("> 本报告用于辅助核对，重要合同和正式申报材料请由专业人员最终确认。");
        try
        {
            File.WriteAllLines(dialog.FileName, lines);
            StatusText.Text = $"报告已导出：{Path.GetFileName(dialog.FileName)}";
        }
        catch (Exception error)
        {
            MessageBox.Show(this, $"无法保存报告：{error.Message}", "导出失败", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }
    private void FindingsList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (FindingsList.SelectedItem is not Finding finding) { ClearDetail(); return; }
        EmptyDetail.Visibility = Visibility.Collapsed; DetailContent.Visibility = Visibility.Visible;
        DetailBadge.Background = finding.SeverityBackground; DetailSeverity.Text = finding.SeverityLabel; DetailSeverity.Foreground = finding.SeverityBrush;
        DetailTitle.Text = finding.Title; DetailDescription.Text = finding.Detail; DetailSource.Text = $"{finding.Evidence.File} · 第 {finding.Evidence.Page} 页"; DetailExcerpt.Text = finding.Evidence.Excerpt; DetailSuggestion.Text = finding.Suggestion;
    }
    private void ClearDetail() { EmptyDetail.Visibility = Visibility.Visible; DetailContent.Visibility = Visibility.Collapsed; }

    private void Settings_Click(object sender, RoutedEventArgs e)
    {
        var window = new SettingsWindow(_settings) { Owner = this };
        if (window.ShowDialog() != true) return;
        try
        {
            ModelService.SaveSettings(window.Settings);
            _settings = window.Settings;
            UpdateModelStatus();
        }
        catch (Exception error)
        {
            MessageBox.Show(this, $"无法保存模型设置：{error.Message}", "保存失败", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }
    private void UpdateModelStatus() => ModelStatusSide.Text = !_settings.Enabled ? "仅使用确定性规则" : _settings.Provider == "embedded" ? "Qwen2.5 · 离线可用" : _settings.Model;

    private void ThemeButton_Click(object sender, RoutedEventArgs e)
    {
        var nextDark = !_dark;
        ThemeService.Apply(Application.Current.Resources, nextDark);
        _dark = nextDark;
        ApplyNavigationStyles();
        ApplyScenarioStyles();
        ThemeButton.Content = _dark ? "\uE706" : "\uE708";
    }

    private void ChooseLeftContract_Click(object sender, RoutedEventArgs e) { if (ChooseContract() is string path) { _leftContract = path; LeftContractButton.Content = Path.GetFileName(path); LeftDiffStatus.Text = "已选择"; } }
    private void ChooseRightContract_Click(object sender, RoutedEventArgs e) { if (ChooseContract() is string path) { _rightContract = path; RightContractButton.Content = Path.GetFileName(path); RightDiffStatus.Text = "已选择"; } }
    private string? ChooseContract()
    {
        var dialog = new OpenFileDialog { Filter = "支持的合同|*.pdf;*.docx;*.xlsx;*.txt;*.md;*.csv;*.json" };
        return dialog.ShowDialog(this) == true ? dialog.FileName : null;
    }
    private async void RunCompare_Click(object sender, RoutedEventArgs e)
    {
        if (_leftContract is null || _rightContract is null) { MessageBox.Show(this, "请先选择甲方和乙方合同。", "合同对比", MessageBoxButton.OK, MessageBoxImage.Information); return; }
        try
        {
            LeftDiffStatus.Text = RightDiffStatus.Text = "正在比对…";
            var left = await DocumentParser.ParseAsync(_leftContract); var right = await DocumentParser.ParseAsync(_rightContract);
            var leftText = string.Join('\n', left.Pages); var rightText = string.Join('\n', right.Pages);
            if (leftText.Length > 200_000 || rightText.Length > 200_000) throw new InvalidOperationException("单份合同超过 20 万字，请拆分后对比。");
            var model = new SideBySideDiffBuilder(new DiffPlex.Differ()).BuildDiffModel(leftText, rightText);
            LeftDiffBox.Document = BuildDiffDocument(model.OldText.Lines, false);
            RightDiffBox.Document = BuildDiffDocument(model.NewText.Lines, true);
            var changed = model.OldText.Lines.Count(x => x.Type != ChangeType.Unchanged) + model.NewText.Lines.Count(x => x.Type != ChangeType.Unchanged);
            var total = Math.Max(1, model.OldText.Lines.Count + model.NewText.Lines.Count);
            var similarity = Math.Max(0, Math.Round((1d - changed / (double)total) * 100));
            LeftDiffStatus.Text = $"相似度 {similarity:0}% · {changed} 处差异"; RightDiffStatus.Text = "绿色为新增 · 红色为删除";
        }
        catch (Exception error) { MessageBox.Show(this, error.Message, "无法完成对比", MessageBoxButton.OK, MessageBoxImage.Warning); LeftDiffStatus.Text = RightDiffStatus.Text = "对比失败"; }
    }
    private FlowDocument BuildDiffDocument(IEnumerable<DiffPiece> lines, bool newSide)
    {
        var document = new FlowDocument { PagePadding = new Thickness(0), FontFamily = new FontFamily("Microsoft YaHei UI"), FontSize = 13, LineHeight = 23 };
        foreach (var line in lines)
        {
            var paragraph = new Paragraph { Margin = new Thickness(0, 0, 0, 2), Padding = new Thickness(8, 3, 8, 3) };
            var text = line.Text ?? "";
            paragraph.Inlines.Add(new Run(string.IsNullOrEmpty(text) ? " " : text));
            if (line.Type == ChangeType.Deleted) { paragraph.Background = Brush("#4A2027"); paragraph.Foreground = Brush("#FFD3D7"); }
            else if (line.Type == ChangeType.Inserted) { paragraph.Background = Brush("#164434"); paragraph.Foreground = Brush("#B7F2D4"); }
            else if (line.Type == ChangeType.Modified) { paragraph.Background = Brush("#514123"); paragraph.Foreground = Brush("#FFE0A2"); }
            document.Blocks.Add(paragraph);
        }
        return document;
    }
    private static SolidColorBrush Brush(string value) => new((Color)ColorConverter.ConvertFromString(value));
}
