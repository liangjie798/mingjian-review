using MingJian.Desktop.Services;

namespace MingJian.Desktop.Tests;

public sealed class ReviewEngineTests : IDisposable
{
    private readonly string _folder = Path.Combine(Path.GetTempPath(), "mingjian-tests-" + Guid.NewGuid().ToString("N"));
    public ReviewEngineTests() => Directory.CreateDirectory(_folder);

    [Fact]
    public async Task ContractReview_FindsMissingCriticalClauses()
    {
        var path = Write("采购合同.txt", "甲方：海川公司\n乙方：远景公司\n人民币 10000 元\n双方签字盖章");
        var result = await new ReviewEngine().ReviewAsync(ReviewScenario.Contract, [path], new() { Enabled = false });

        Assert.Contains(result.Findings, x => x.Id == "K-ACCEPT-01");
        Assert.Contains(result.Findings, x => x.Id == "K-BREACH-01");
        Assert.DoesNotContain(result.Findings, x => x.Id == "K-PARTY-01");
    }

    [Fact]
    public async Task CompetitionReview_FindsProjectNameMismatch()
    {
        var common = "团队成员：张三、李四、王五\n联系方式：13800138000\n签字盖章";
        var files = new[]
        {
            Write("报名表.txt", "项目名称：星火平台\n" + common),
            Write("项目书.txt", "项目名称：星光平台\n" + common),
            Write("承诺书.txt", "项目名称：星火平台\n" + common)
        };
        var result = await new ReviewEngine().ReviewAsync(ReviewScenario.Competition, files, new() { Enabled = false });

        Assert.Contains(result.Findings, x => x.Id == "C-CONSIST-01");
        Assert.DoesNotContain(result.Findings, x => x.Id.StartsWith("C-MISSING"));
    }

    [Fact]
    public async Task TextParser_PreservesChineseContent()
    {
        var path = Write("材料.md", "# 项目说明\n这是审查材料。\n");
        var parsed = await DocumentParser.ParseAsync(path);
        Assert.Contains("这是审查材料", parsed.Pages[0]);
        Assert.Equal("文本解析", parsed.Parser);
    }

    private string Write(string name, string content)
    {
        var path = Path.Combine(_folder, name);
        File.WriteAllText(path, content);
        return path;
    }
    public void Dispose() => Directory.Delete(_folder, true);
}
