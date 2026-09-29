using System.Collections.ObjectModel;
using System.Windows.Media;

namespace MingJian.Desktop;

public enum ReviewScenario { Competition, Contract }
public enum RiskLevel { Blocking, High, Medium, Info }

public sealed record Evidence(string File, int Page, string Excerpt);

public sealed class Finding
{
    public required string Id { get; init; }
    public required RiskLevel Severity { get; init; }
    public required string Title { get; init; }
    public required string Detail { get; init; }
    public required Evidence Evidence { get; init; }
    public required string Suggestion { get; init; }
    public bool IsModel { get; init; }
    public string SeverityLabel => Severity switch
    {
        RiskLevel.Blocking => "阻断",
        RiskLevel.High => "高风险",
        RiskLevel.Medium => "需关注",
        _ => "提示"
    };
    public Brush SeverityBrush => new SolidColorBrush((Color)ColorConverter.ConvertFromString(Severity switch
    {
        RiskLevel.Blocking => "#FF6872",
        RiskLevel.High => "#FFAC5F",
        RiskLevel.Medium => "#DFC86A",
        _ => "#66B8FF"
    }));
    public Brush SeverityBackground => new SolidColorBrush((Color)ColorConverter.ConvertFromString(Severity switch
    {
        RiskLevel.Blocking => "#2C161C",
        RiskLevel.High => "#2B2118",
        RiskLevel.Medium => "#29271A",
        _ => "#172434"
    }));
    public string SourceLabel => IsModel ? "AI 模型" : "审查规则";
}

public sealed class ReviewFile
{
    public required string Path { get; init; }
    public string Name => System.IO.Path.GetFileName(Path);
    public string Extension => System.IO.Path.GetExtension(Path).TrimStart('.').ToUpperInvariant();
    public long Size => new FileInfo(Path).Length;
    public string SizeLabel => Size < 1024 * 1024 ? $"{Size / 1024d:0.0} KB" : $"{Size / 1024d / 1024d:0.0} MB";
}

public sealed record ParsedDocument(string Name, string[] Pages, string Parser)
{
    public int Characters => Pages.Sum(x => x.Length);
}

public sealed record ReviewResult(IReadOnlyList<ParsedDocument> Documents, IReadOnlyList<Finding> Findings, string ModelStatus);

public sealed class ModelSettings
{
    public bool Enabled { get; set; } = true;
    public string Provider { get; set; } = "embedded";
    public string BaseUrl { get; set; } = "";
    public string Model { get; set; } = "Qwen2.5-0.5B-Instruct Q4_K_M";
    public string ApiKey { get; set; } = "";
    public int TimeoutSeconds { get; set; } = 180;
}
