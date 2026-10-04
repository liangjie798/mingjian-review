using MingJian.Desktop.Services;

namespace MingJian.Desktop.Tests;

public sealed class ModelServiceTests
{
    [Fact]
    public void ParseFindings_AcceptsStringPageNumberFromModel()
    {
        var documents = new[] { new ParsedDocument("申报书.txt", ["项目预算缺少测算依据。"], "测试") };
        const string response = """
            ```json
            {"findings":[{"severity":"high","title":"预算依据不足","detail":"预算缺少测算过程","file":"申报书.txt","page":"1","excerpt":"项目预算缺少测算依据。","suggestion":"补充单价和数量依据"}]}
            ```
            """;

        var findings = ModelService.ParseFindings(response, documents);

        var finding = Assert.Single(findings);
        Assert.Equal(1, finding.Evidence.Page);
        Assert.Equal(RiskLevel.High, finding.Severity);
    }

    [Fact]
    public void ParseFindings_AcceptsTopLevelArrayAndDecimalPage()
    {
        var documents = new[] { new ParsedDocument("报告.txt", ["第一页", "缺少测试数据和指标对照。"], "测试") };
        const string response = """[{"severity":"medium","title":"测试不完整","detail":"缺少指标对照","file":"报告.txt","page":2.0,"excerpt":"缺少测试数据和指标对照。","suggestion":"补充测试表格"}]""";

        var findings = ModelService.ParseFindings(response, documents);

        Assert.Equal(2, Assert.Single(findings).Evidence.Page);
    }
}
