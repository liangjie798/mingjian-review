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
            documents.AddRange(await DocumentParser.ParseManyAsync(path));
        }
        progress?.Report("正在执行一致性与风险规则");
        var findings = ReviewArchives(documents);
        findings.AddRange(scenario == ReviewScenario.Contract ? ReviewContract(documents) : ReviewCompetition(documents, scenario));
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

    private static List<Finding> ReviewCompetition(IReadOnlyList<ParsedDocument> docs, ReviewScenario scenario)
    {
        var result = new List<Finding>();
        var names = string.Join('\n', docs.Select(x => x.Name).Concat(docs.Where(x => x.Parser == "ZIP 清单").SelectMany(x => x.Pages)));
        var expected = scenario switch
        {
            ReviewScenario.MathModeling => new[] { ("竞赛论文或答卷", "论文|答卷", RiskLevel.Blocking), ("支撑材料", "支撑|附件|代码|数据", RiskLevel.High) },
            ReviewScenario.InternetPlus => new[] { ("项目申报书", "报名|申报", RiskLevel.Blocking), ("商业计划书", "商业计划|项目计划|项目书", RiskLevel.Blocking), ("路演材料", "路演|PPT|演示", RiskLevel.High) },
            ReviewScenario.ChallengeCup => new[] { ("项目申报书", "报名|申报", RiskLevel.Blocking), ("项目或调研报告", "项目报告|调研报告|作品报告", RiskLevel.Blocking), ("证明材料", "证明|附件|佐证", RiskLevel.High) },
            ReviewScenario.InnovationTraining => new[] { ("申报书或任务书", "申报书|任务书", RiskLevel.Blocking), ("中期或结题材料", "中期|结题", RiskLevel.Blocking), ("成果附件", "成果|附件|佐证", RiskLevel.High) },
            ReviewScenario.ElectronicDesign => new[] { ("设计报告", "设计报告|论文", RiskLevel.Blocking), ("源程序", "源程序|源代码|代码", RiskLevel.Blocking), ("测试记录", "测试记录|测试数据|测试报告", RiskLevel.High) },
            ReviewScenario.ComputerDesign => new[] { ("作品申报书", "申报书|报名表", RiskLevel.Blocking), ("作品说明书", "作品说明|设计说明|项目说明", RiskLevel.Blocking), ("演示材料", "演示|视频|答辩|PPT", RiskLevel.High) },
            ReviewScenario.LanQiaoCup => new[] { ("参赛信息", "报名|参赛信息|队伍信息", RiskLevel.Blocking), ("源代码", "源代码|源码|代码", RiskLevel.Blocking), ("说明文档", "说明文档|使用说明|README", RiskLevel.High) },
            _ => new[] { ("报名表", "报名|申报", RiskLevel.Blocking), ("项目书", "项目书|计划书|商业计划", RiskLevel.Blocking), ("承诺书", "承诺", RiskLevel.High) }
        };
        foreach (var (label, pattern, risk) in expected.Where(x => !Regex.IsMatch(names, x.Item2, RegexOptions.IgnoreCase)))
            result.Add(New($"C-MISSING-{result.Count + 1:00}", risk, $"未识别到{label}", $"当前文件名中没有识别到{label}，请确认它是否属于必交材料。", "材料清单", "待核对材料：" + label, $"上传{label}，或根据正式通知确认该材料并非必交。"));

        var text = AllText(docs);
        if (!Regex.IsMatch(text, @"1[3-9]\d{9}|(?:电话|手机|联系方式)\s*[:：]"))
            result.Add(New("C-CONTACT-01", RiskLevel.Medium, "未识别到有效联系方式", "材料正文中没有识别到手机号或明确的联系方式字段。", "材料正文", "未检出手机号或联系方式字段", "在报名表中补充负责人联系方式，并确认号码完整、可用。"));

        var projects = Matches(docs, @"(?:项目|作品|论文|题目)名称\s*[:：]\s*([^\n|]{2,60})");
        if (projects.Select(x => x.Value).Distinct().Count() > 1)
            result.Add(New("C-CONSIST-01", RiskLevel.High, "项目名称可能不一致", "不同材料中识别到多个项目名称，可能导致资格审查退回。", projects[0].Doc.Name, projects[0].Value, "统一报名表、项目书、承诺书和附件中的项目名称。"));

        if (scenario == ReviewScenario.MathModeling)
        {
            MissingContent(result, text, "M-STRUCT-01", @"摘要", RiskLevel.High, "未识别到论文摘要", "补充摘要，概括问题、方法、模型与主要结论。");
            MissingContent(result, text, "M-STRUCT-02", @"关键词", RiskLevel.Medium, "未识别到关键词", "在摘要后补充能够代表模型和问题的关键词。");
            MissingContent(result, text, "M-STRUCT-03", @"模型假设|问题假设", RiskLevel.Medium, "未识别到模型假设", "单列模型假设并说明假设依据与适用范围。");
            MissingContent(result, text, "M-STRUCT-04", @"参考文献", RiskLevel.High, "未识别到参考文献", "补充参考文献并统一正文引用格式。");
        }
        else if (scenario == ReviewScenario.InternetPlus)
        {
            MissingContent(result, text, "I-MARKET-01", @"市场分析|市场规模|目标市场", RiskLevel.High, "缺少市场分析", "补充目标市场、规模依据、用户画像和竞争分析。");
            MissingContent(result, text, "I-BUSINESS-01", @"商业模式|盈利模式", RiskLevel.High, "缺少商业模式说明", "说明客户、核心价值、收入来源和关键成本。");
            MissingContent(result, text, "I-FINANCE-01", @"财务预测|营收预测|成本预测|融资", RiskLevel.Medium, "缺少财务或融资数据", "补充测算口径、关键假设和资金使用计划。");
            MissingContent(result, text, "I-IP-01", @"知识产权|专利|软件著作权|商标", RiskLevel.Medium, "未识别到知识产权说明", "说明知识产权归属、申请状态及与项目的关联。");
        }
        else if (scenario == ReviewScenario.ChallengeCup)
        {
            MissingContent(result, text, "T-VALUE-01", @"社会价值|社会效益|现实意义", RiskLevel.High, "缺少社会价值说明", "结合服务对象和实际问题说明项目的社会价值。");
            MissingContent(result, text, "T-INNOVATION-01", @"创新点|创新性|创新之处", RiskLevel.High, "缺少创新点说明", "用可验证的对比说明核心创新及其依据。");
            MissingContent(result, text, "T-PRACTICE-01", @"实践|调研|走访|问卷|访谈", RiskLevel.Medium, "缺少实践或调研过程", "补充实践过程、样本来源、时间地点和证据材料。");
            MissingContent(result, text, "T-ADVISOR-01", @"指导教师|指导老师", RiskLevel.Medium, "未识别到指导教师信息", "核对申报书中的指导教师姓名、单位和联系方式。");
        }
        else if (scenario == ReviewScenario.InnovationTraining)
        {
            MissingContent(result, text, "D-INNOVATION-01", @"创新点|创新性|创新之处", RiskLevel.High, "缺少创新点说明", "说明项目解决的问题、核心创新及可验证依据。");
            MissingContent(result, text, "D-PLAN-01", @"研究计划|实施计划|进度安排", RiskLevel.High, "缺少实施计划", "补充阶段目标、时间节点、负责人和预期成果。");
            MissingContent(result, text, "D-BUDGET-01", @"经费|预算|支出", RiskLevel.Medium, "缺少经费说明", "核对预算、支出科目和学校财务要求。");
            MissingContent(result, text, "D-ADVISOR-01", @"指导教师|指导老师", RiskLevel.Medium, "未识别到指导教师信息", "补充指导教师姓名、单位和职责。");
        }
        else if (scenario == ReviewScenario.ElectronicDesign)
        {
            MissingContent(result, text, "E-SYSTEM-01", @"系统方案|总体方案|方案论证", RiskLevel.High, "缺少系统方案", "补充总体框图、方案比较和选型依据。");
            MissingContent(result, text, "E-CIRCUIT-01", @"电路|原理图|硬件设计", RiskLevel.High, "缺少电路设计说明", "补充关键电路、参数计算和器件选型。");
            MissingContent(result, text, "E-TEST-01", @"测试方法|测试数据|测试结果", RiskLevel.High, "缺少测试过程", "补充测试条件、仪器、原始数据和指标对照。");
        }
        else if (scenario == ReviewScenario.ComputerDesign)
        {
            MissingContent(result, text, "CD-RUN-01", @"运行说明|使用说明|部署|安装", RiskLevel.High, "缺少运行说明", "补充运行环境、安装步骤、测试账号和操作流程。");
            MissingContent(result, text, "CD-ARCH-01", @"系统架构|技术架构|总体设计", RiskLevel.Medium, "缺少技术架构说明", "补充主要模块、数据流和关键技术选择。");
            MissingContent(result, text, "CD-IP-01", @"原创|知识产权|版权|著作权", RiskLevel.High, "缺少原创或版权说明", "列明原创内容、第三方素材来源和知识产权归属。");
        }
        else if (scenario == ReviewScenario.LanQiaoCup)
        {
            MissingContent(result, text, "L-ENV-01", @"开发环境|运行环境|编译环境|版本", RiskLevel.High, "缺少运行环境说明", "写明语言、框架、依赖版本和运行平台。");
            MissingContent(result, text, "L-RUN-01", @"运行步骤|使用说明|启动|README", RiskLevel.High, "缺少运行步骤", "提供从解压、安装依赖到启动程序的完整步骤。");
            MissingContent(result, text, "L-ORIGINAL-01", @"原创|独立完成|知识产权", RiskLevel.Medium, "缺少原创性说明", "补充原创声明和第三方依赖清单。");
        }
        if (!Regex.IsMatch(text, @"签字|签名|盖章|公章") && Regex.IsMatch(names, "承诺|声明"))
            result.Add(New("C-SIGN-01", RiskLevel.High, "承诺材料可能缺少签署信息", "承诺材料的可提取文本中没有出现签字或盖章信息。", "承诺材料", "未检出签署字段", "查看原件并确认签名、日期和盖章是否完整。"));
        return result;
    }

    private static List<Finding> ReviewArchives(IReadOnlyList<ParsedDocument> docs)
    {
        var result = new List<Finding>();
        var summaries = docs.Where(x => x.Parser == "ZIP 清单").ToArray();
        for (var index = 0; index < summaries.Length; index++)
        {
            var summary = summaries[index];
            var text = string.Join('\n', summary.Pages);
            var entryCount = Marker(text, "ZIP_ENTRY_COUNT");
            var supportedCount = Marker(text, "ZIP_SUPPORTED_COUNT");
            var unsafeCount = Marker(text, "ZIP_UNSAFE_COUNT");
            if (entryCount == 0)
                result.Add(New($"Z-EMPTY-{index + 1:00}", RiskLevel.Blocking, "ZIP 压缩包为空", "压缩包中没有可审查的文件。", summary.Name, "文件数量：0", "重新打包全部参赛材料后再上传。"));
            if (unsafeCount > 0)
                result.Add(New($"Z-PATH-{index + 1:00}", RiskLevel.Blocking, "ZIP 包含危险文件路径", $"检测到 {unsafeCount} 个可能越过解压目录的文件路径，系统已跳过这些条目。", summary.Name, $"危险路径：{unsafeCount} 个", "删除异常路径文件，并使用普通相对目录重新生成 ZIP。"));
            if (entryCount > 0 && supportedCount == 0)
                result.Add(New($"Z-FORMAT-{index + 1:00}", RiskLevel.High, "ZIP 中没有可解析的正文材料", "压缩包中未发现 PDF、DOCX、XLSX 或常见文本文件，当前只能依据文件名检查清单。", summary.Name, "可解析文件：0", "至少加入一份可解析的申报书、报告或说明文档。"));
        }
        return result;
    }

    private static int Marker(string text, string name)
    {
        var match = Regex.Match(text, $@"(?m)^{Regex.Escape(name)}=(\d+)$");
        return match.Success ? int.Parse(match.Groups[1].Value) : 0;
    }

    private static void MissingContent(List<Finding> result, string text, string id, string pattern, RiskLevel level, string title, string suggestion)
    {
        if (!Regex.IsMatch(text, pattern, RegexOptions.IgnoreCase))
            result.Add(New(id, level, title, "材料正文中没有识别到该项内容。", "材料正文", "未检出对应内容", suggestion));
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
