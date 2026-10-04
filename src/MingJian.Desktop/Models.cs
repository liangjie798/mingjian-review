using System.Collections.ObjectModel;
using System.Windows.Media;

namespace MingJian.Desktop;

public enum ReviewScenario { Competition, MathModeling, InternetPlus, ChallengeCup, Contract }
public enum RiskLevel { Blocking, High, Medium, Info }

public sealed record ReviewScenarioProfile(string Title, string Subtitle, string SectionLabel, string ReportLabel, string AiInstruction);

public static class ReviewScenarios
{
    public static bool IsCompetition(ReviewScenario scenario) => scenario != ReviewScenario.Contract;

    public static ReviewScenarioProfile Get(ReviewScenario scenario) => scenario switch
    {
        ReviewScenario.MathModeling => new(
            "数学建模竞赛材料审查",
            "检查论文结构、队伍信息、支撑材料与格式完整性",
            "竞赛材料审查 / 数学建模",
            "数学建模竞赛材料审查",
            "数学建模竞赛材料，重点核对论文或答卷、摘要与关键词、模型假设、结果验证、参考文献、队伍信息和支撑材料。"),
        ReviewScenario.InternetPlus => new(
            "互联网+ / 创新大赛材料审查",
            "检查申报书、商业计划、路演材料与数据一致性",
            "竞赛材料审查 / 互联网+",
            "互联网+ / 创新大赛材料审查",
            "中国国际大学生创新大赛（互联网+）材料，重点核对申报书、商业计划书、路演材料、市场分析、商业模式、财务数据、知识产权和团队信息。"),
        ReviewScenario.ChallengeCup => new(
            "挑战杯竞赛材料审查",
            "检查申报材料、项目报告、实践证明与创新价值",
            "竞赛材料审查 / 挑战杯",
            "挑战杯竞赛材料审查",
            "挑战杯竞赛材料，重点核对申报书、项目或调研报告、实践证明、社会价值、创新点、成果依据、指导教师和学校信息。"),
        ReviewScenario.Contract => new(
            "合同条款审查",
            "检查主体、付款、验收、违约责任与关键条款风险",
            "合同审查",
            "合同审查",
            "合同材料，重点核对双方主体、金额与付款、交付验收、违约责任、保密、知识产权、解除条件和争议解决。"),
        _ => new(
            "大学生竞赛材料审查",
            "核对材料完整性、团队信息与跨文件一致性",
            "竞赛材料审查",
            "大学生竞赛材料审查",
            "通用大学生竞赛材料，重点核对必交文件、项目名称、团队信息、签署信息、日期和跨文件一致性。")
    };
}

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
