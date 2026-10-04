using System.Diagnostics;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace MingJian.Desktop.Services;

public static class ModelService
{
    private static readonly HttpClient Http = new();
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true, WriteIndented = true };
    private static string SettingsPath => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "MingJian", "settings.json");

    public static ModelSettings LoadSettings()
    {
        try { return JsonSerializer.Deserialize<ModelSettings>(File.ReadAllText(SettingsPath), JsonOptions) ?? new(); }
        catch { return new(); }
    }

    public static void SaveSettings(ModelSettings settings)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(SettingsPath)!);
        File.WriteAllText(SettingsPath, JsonSerializer.Serialize(settings, JsonOptions));
    }

    public static async Task<List<Finding>> AnalyzeAsync(ModelSettings config, ReviewScenario scenario, IReadOnlyList<ParsedDocument> documents)
    {
        var remaining = 6000;
        var material = new StringBuilder();
        foreach (var doc in documents)
        {
            material.AppendLine($"\n### 文件：{doc.Name}");
            for (var i = 0; i < doc.Pages.Length && remaining > 0; i++)
            {
                var cleaned = Regex.Replace(doc.Pages[i], @"\s+", " ").Trim();
                var snippet = cleaned[..Math.Min(cleaned.Length, Math.Min(remaining, 3000))];
                remaining -= snippet.Length;
                material.AppendLine($"[第{i + 1}页] {snippet}");
            }
        }
        var names = string.Join("、", documents.Select(x => x.Name));
        var system = "你是严谨的中文材料审查员。只根据原文指出可验证的问题，不得虚构条款、数字或页码。只输出 JSON。";
        var user = $"审查场景：{ReviewScenarios.Get(scenario).AiInstruction}。找出最多8个高价值问题，没有可靠问题时返回空数组。返回 findings 数组；每项包含 severity、title、detail、file、page、excerpt、suggestion。page必须是JSON整数，不能加引号；severity只能是blocking、high、medium或info。可用文件名：{names}\n材料：\n{material}";
        var content = config.Provider == "embedded"
            ? await EmbeddedChat(config, system, user)
            : await CloudChat(config, system, user);
        return ParseFindings(content, documents);
    }

    public static async Task<IReadOnlyList<string>> ListModelsAsync(ModelSettings config)
    {
        if (config.Provider == "embedded") return ["Qwen2.5-0.5B-Instruct Q4_K_M"];
        using var request = new HttpRequestMessage(HttpMethod.Get, config.Provider switch
        {
            "ollama" => config.BaseUrl.TrimEnd('/') + "/api/tags",
            _ => config.BaseUrl.TrimEnd('/') + "/models"
        });
        AddHeaders(request, config);
        using var response = await Send(request, Math.Min(15, config.TimeoutSeconds));
        var root = JsonNode.Parse(await response.Content.ReadAsStringAsync());
        if (config.Provider == "ollama") return root?["models"]?.AsArray().Select(x => x?["name"]?.GetValue<string>() ?? "").Where(x => x.Length > 0).ToArray() ?? [];
        return root?["data"]?.AsArray().Select(x => x?["id"]?.GetValue<string>() ?? "").Where(x => x.Length > 0).ToArray()
            ?? root?["models"]?.AsArray().Select(x => (x?["name"]?.GetValue<string>() ?? "").Replace("models/", "")).Where(x => x.Length > 0).ToArray() ?? [];
    }

    private static async Task<string> CloudChat(ModelSettings config, string system, string user)
    {
        var baseUrl = config.BaseUrl.TrimEnd('/');
        string url;
        object payload;
        if (config.Provider == "anthropic")
        {
            url = baseUrl + "/messages";
            payload = new { model = config.Model, max_tokens = 1200, temperature = .1, system, messages = new[] { new { role = "user", content = user } } };
        }
        else if (config.Provider == "gemini")
        {
            url = $"{baseUrl}/models/{config.Model}:generateContent";
            payload = new { systemInstruction = new { parts = new[] { new { text = system } } }, contents = new[] { new { role = "user", parts = new[] { new { text = user } } } }, generationConfig = new { temperature = .1, responseMimeType = "application/json" } };
        }
        else if (config.Provider == "ollama")
        {
            url = baseUrl + "/api/chat";
            payload = new { model = config.Model, stream = false, format = "json", messages = Messages(system, user), options = new { temperature = .1, num_ctx = 8192 } };
        }
        else
        {
            url = baseUrl + "/chat/completions";
            payload = new { model = config.Model, temperature = .1, messages = Messages(system, user) };
        }
        using var request = new HttpRequestMessage(HttpMethod.Post, url) { Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json") };
        AddHeaders(request, config);
        using var response = await Send(request, config.TimeoutSeconds);
        var root = JsonNode.Parse(await response.Content.ReadAsStringAsync());
        return config.Provider switch
        {
            "anthropic" => string.Concat(root?["content"]?.AsArray().Select(x => x?["text"]?.GetValue<string>() ?? "") ?? []),
            "gemini" => root?["candidates"]?[0]?["content"]?["parts"]?[0]?["text"]?.GetValue<string>() ?? "",
            "ollama" => root?["message"]?["content"]?.GetValue<string>() ?? "",
            _ => root?["choices"]?[0]?["message"]?["content"]?.GetValue<string>() ?? ""
        };
    }

    private static object[] Messages(string system, string user) => [new { role = "system", content = system }, new { role = "user", content = user }];

    private static async Task<HttpResponseMessage> Send(HttpRequestMessage request, int timeout)
    {
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(timeout));
        var response = await Http.SendAsync(request, cts.Token);
        if (!response.IsSuccessStatusCode)
        {
            var detail = await response.Content.ReadAsStringAsync(cts.Token);
            throw new InvalidOperationException($"接口返回 {(int)response.StatusCode}：{detail[..Math.Min(120, detail.Length)]}");
        }
        return response;
    }

    private static void AddHeaders(HttpRequestMessage request, ModelSettings config)
    {
        if (config.Provider == "anthropic")
        {
            request.Headers.Add("x-api-key", config.ApiKey);
            request.Headers.Add("anthropic-version", "2023-06-01");
        }
        else if (config.Provider == "gemini") request.Headers.Add("x-goog-api-key", config.ApiKey);
        else if (!string.IsNullOrWhiteSpace(config.ApiKey)) request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", config.ApiKey);
    }

    private static async Task<string> EmbeddedChat(ModelSettings config, string system, string user)
    {
        var root = AppContext.BaseDirectory;
        var runtime = Path.Combine(root, "runtime", "llama", "llama-cli.exe");
        var model = Path.Combine(root, "models", "qwen2.5-0.5b-instruct-q4_k_m.gguf");
        if (!File.Exists(runtime) || !File.Exists(model)) throw new FileNotFoundException("内置模型文件不完整，请重新下载安装包。");
        var start = new ProcessStartInfo(runtime)
        {
            UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true,
            CreateNoWindow = true, StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8
        };
        foreach (var arg in new[] { "-m", model, "-sys", system, "-p", user, "-st", "-n", "900", "-c", "8192", "-t", Math.Clamp(Environment.ProcessorCount - 1, 2, 8).ToString(), "--temp", "0.1", "--no-display-prompt", "--no-show-timings", "--simple-io", "--log-disable" }) start.ArgumentList.Add(arg);
        using var process = Process.Start(start) ?? throw new InvalidOperationException("无法启动内置模型");
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(Math.Max(180, config.TimeoutSeconds)));
        var output = process.StandardOutput.ReadToEndAsync(cts.Token);
        var error = process.StandardError.ReadToEndAsync(cts.Token);
        await process.WaitForExitAsync(cts.Token);
        if (process.ExitCode != 0) throw new InvalidOperationException((await error)[..Math.Min(180, (await error).Length)]);
        return await output;
    }

    internal static List<Finding> ParseFindings(string content, IReadOnlyList<ParsedDocument> docs)
    {
        content = Regex.Replace(content, @"<think>[\s\S]*?</think>", "").Trim();
        content = Regex.Replace(content, @"^```(?:json)?\s*|\s*```$", "", RegexOptions.IgnoreCase).Trim();
        var root = ParseJsonPayload(content);
        var items = root as JsonArray ?? (root as JsonObject)?["findings"] as JsonArray;
        var result = new List<Finding>();
        if (items is null) return result;
        foreach (var item in items.Take(8))
        {
            if (item is not JsonObject finding) continue;
            var file = TextValue(finding["file"]);
            var doc = docs.FirstOrDefault(x => x.Name == file);
            if (doc is null || doc.Pages.Length == 0) continue;
            var page = Math.Clamp(PageValue(finding["page"]), 1, Math.Max(1, doc.Pages.Length));
            var excerpt = TextValue(finding["excerpt"]).Trim();
            if (excerpt.Length < 4 || !doc.Pages[page - 1].Contains(excerpt, StringComparison.Ordinal)) continue;
            var severity = TextValue(finding["severity"]).ToLowerInvariant() switch { "blocking" => RiskLevel.Blocking, "high" => RiskLevel.High, "info" => RiskLevel.Info, _ => RiskLevel.Medium };
            var title = TextValue(finding["title"]).Trim();
            var detail = TextValue(finding["detail"]).Trim();
            var suggestion = TextValue(finding["suggestion"]).Trim();
            if (string.IsNullOrWhiteSpace(title) || string.IsNullOrWhiteSpace(detail) || string.IsNullOrWhiteSpace(suggestion)) continue;
            result.Add(new() { Id = $"AI-{result.Count + 1:000}", Severity = severity, Title = title, Detail = detail, Evidence = new(file, page, excerpt), Suggestion = suggestion, IsModel = true });
        }
        return result;
    }

    private static JsonNode? ParseJsonPayload(string content)
    {
        try { return JsonNode.Parse(content); }
        catch (JsonException)
        {
            var objectStart = content.IndexOf('{');
            var arrayStart = content.IndexOf('[');
            var start = objectStart < 0 ? arrayStart : arrayStart < 0 ? objectStart : Math.Min(objectStart, arrayStart);
            var end = Math.Max(content.LastIndexOf('}'), content.LastIndexOf(']'));
            if (start < 0 || end <= start) throw;
            return JsonNode.Parse(content[start..(end + 1)]);
        }
    }

    private static int PageValue(JsonNode? node)
    {
        if (node is not JsonValue value) return 1;
        if (value.TryGetValue<int>(out var number)) return number;
        if (value.TryGetValue<long>(out var longNumber) && longNumber is >= int.MinValue and <= int.MaxValue) return (int)longNumber;
        if (value.TryGetValue<double>(out var decimalNumber) && double.IsFinite(decimalNumber)) return (int)Math.Round(decimalNumber);
        if (value.TryGetValue<string>(out var text) && int.TryParse(text, out number)) return number;
        return 1;
    }

    private static string TextValue(JsonNode? node)
    {
        if (node is not JsonValue value) return "";
        return value.TryGetValue<string>(out var text) ? text ?? "" : value.ToJsonString().Trim('"');
    }
}
