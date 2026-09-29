using System.Text.RegularExpressions;

namespace MingJian.Desktop.Services;

public sealed partial class ReviewEngine
{
    public async Task<ReviewResult> ReviewAsync(ReviewScenario scenario, IEnumerable<string> paths, ModelSettings settings, IProgress<string>? progress = null)
    {
        var documents = new List<ParsedDocument>();
        foreach (var path in paths)
        {
            progress?.Report($"正在解析 {Path.GetFileName(path)}");
            documents.Add(await DocumentParser.ParseAsync(path));
        }
        progress?.Report("正在执行一致性与风险规则");
        var findings = scenario == ReviewScenario.Contract ? ReviewContract(documents) : ReviewCompetition(documents);
        var modelStatus = "内置规则审查";
        if (settings.Enabled)
        {
            progress?.Report($"正在调用 {settings.Model}");
            try
            {
                var ai = await ModelService.AnalyzeAsync(settings, scenario, documents);
                findings.AddRange(ai);
                modelStatus = settings.Provider == "embedded" ? $"规则 + 内置 Qwen · 新增 {ai.Count} 项" : $"规则 + {settings.Model} · 新增 {ai.Count} 项";
            }
            catch (Exception error)
            {
                modelStatus = $"规则审查完成；AI 跳过：{error.Message}";
            }
        }
        return new(documents, findings, modelStatus);
    }

    private static List<Finding> ReviewCompetition(IReadOnlyList<ParsedDocument> docs)
    {
        var result = new List<Finding>();
        var names = string.Join(' ', docs.Select(x => x.Name));
        var expected = new[] { ("报名表", "报名|申报", RiskLevel.Blocking), ("项目书", "项目书|计划书|商业计划", RiskLevel.Blocking), ("承诺书", "承诺", RiskLevel.High) };
        foreach (var (label, pattern, risk) in expected.Where(x => !Regex.IsMatch(names, x.Item2, RegexOptions.IgnoreCase)))
            result.Add(New($"C-MISSING-{result.Count + 1:00}", risk, $"未识别到{label}", $"当前文件名中没有识别到{label}，请确认它是否属于必交材料。", "材料清单", "待核对材料：" + label, $"上传{label}，或根据正式通知确认该材料并非必交。"));

        var text = AllText(docs);
        if (!Regex.IsMatch(text, @"1[3-9]\d{9}|(?:电话|手机|联系方式)\s*[:：]"))
            result.Add(New("C-CONTACT-01", RiskLevel.Medium, "未识别到有效联系方式", "材料正文中没有识别到手机号或明确的联系方式字段。", "材料正文", "未检出手机号或联系方式字段", "在报名表中补充负责人联系方式，并确认号码完整、可用。"));

        var projects = Matches(docs, @"(?:项目|作品)名称\s*[:：]\s*([^\n|]{2,60})");
        if (projects.Select(x => x.Value).Distinct().Count() > 1)
            result.Add(New("C-CONSIST-01", RiskLevel.High, "项目名称可能不一致", "不同材料中识别到多个项目名称，可能导致资格审查退回。", projects[0].Doc.Name, projects[0].Value, "统一报名表、项目书、承诺书和附件中的项目名称。"));

        var team = Regex.Match(text, @"团队成员\s*[:：]\s*([^\n]+)");
        if (team.Success)
        {
            var count = Regex.Split(team.Groups[1].Value, "[、,，;；]").Count(x => !string.IsNullOrWhiteSpace(x));
            if (count is > 0 and < 3)
                result.Add(New("C-TEAM-01", RiskLevel.Blocking, "团队人数可能不足", $"成员字段中识别到约 {count} 名成员，演示规则要求 3 至 5 人。", "材料正文", team.Value, "根据正式比赛通知确认人数要求，并同步更新全部材料。"));
        }
        if (!Regex.IsMatch(text, @"签字|签名|盖章|公章") && Regex.IsMatch(names, "承诺|声明"))
            result.Add(New("C-SIGN-01", RiskLevel.High, "承诺材料可能缺少签署信息", "承诺材料的可提取文本中没有出现签字或盖章信息。", "承诺材料", "未检出签署字段", "查看原件并确认签名、日期和盖章是否完整。"));
        return result;
    }

    private static List<Finding> ReviewContract(IReadOnlyList<ParsedDocument> docs)
    {
        var result = new List<Finding>();
        var text = AllText(docs);
        void Missing(string id, string pattern, RiskLevel level, string title, string suggestion)
        {
            if (!Regex.IsMatch(text, pattern, RegexOptions.IgnoreCase))
                result.Add(New(id, level, title, "合同正文中没有识别到该项关键约定。", "合同正文", "未检出对应条款", suggestion));
        }
        Missing("K-PARTY-01", @"甲方|委托方", RiskLevel.Blocking, "未识别到甲方主体", "补充甲方全称、统一社会信用代码与联系地址。");
        Missing("K-PARTY-02", @"乙方|受托方|承包方", RiskLevel.Blocking, "未识别到乙方主体", "补充乙方全称、统一社会信用代码与联系地址。");
        Missing("K-AMOUNT-01", @"(?:人民币|¥|￥)\s*[\d,，.]+|合同(?:总价|金额)", RiskLevel.High, "未识别到明确合同金额", "明确含税总价、税率、付款节点和收款账户。");
        Missing("K-ACCEPT-01", @"验收", RiskLevel.High, "缺少明确验收条款", "补充验收标准、期限、异议方式和逾期处理。");
        Missing("K-BREACH-01", @"违约|违约金", RiskLevel.High, "缺少违约责任", "明确双方违约情形、责任上限和解除条件。");
        Missing("K-DISPUTE-01", @"争议|仲裁|人民法院", RiskLevel.Medium, "缺少争议解决方式", "约定适用法律、管辖法院或仲裁机构。");
        Missing("K-CONF-01", @"保密", RiskLevel.Medium, "缺少保密约定", "明确保密范围、例外、期限与泄密责任。");
        var percents = Regex.Matches(text, @"(\d{1,3})\s*%").Select(x => int.Parse(x.Groups[1].Value)).ToArray();
        if (percents.Any(x => x > 100))
            result.Add(New("K-PAY-01", RiskLevel.Blocking, "检测到超过 100% 的比例", "付款或责任比例可能填写错误。", "合同正文", string.Join("、", percents.Where(x => x > 100).Select(x => x + "%")), "核对比例数值和对应付款节点。"));
        if (!Regex.IsMatch(text, @"签字|签章|盖章"))
            result.Add(New("K-SIGN-01", RiskLevel.Medium, "未识别到签署信息", "可提取文本中没有出现签字或盖章字段。", "合同正文", "未检出签署字段", "检查签署页、签署日期和公章。"));
        return result;
    }

    private static Finding New(string id, RiskLevel severity, string title, string detail, string file, string excerpt, string suggestion) => new()
        { Id = id, Severity = severity, Title = title, Detail = detail, Evidence = new(file, 1, excerpt), Suggestion = suggestion };
    private static string AllText(IEnumerable<ParsedDocument> docs) => string.Join('\n', docs.SelectMany(x => x.Pages));
    private static List<(ParsedDocument Doc, string Value)> Matches(IEnumerable<ParsedDocument> docs, string pattern) => docs.SelectMany(d => Regex.Matches(string.Join('\n', d.Pages), pattern, RegexOptions.IgnoreCase).Select(m => (d, m.Groups[1].Value.Trim()))).ToList();
}
