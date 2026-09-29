using MingJian.Desktop.Services;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace MingJian.Desktop;

public partial class SettingsWindow : Window
{
    private sealed record Provider(string Id, string Name, string Url, string Model, string Hint);
    private readonly Provider[] _providers =
    [
        new("embedded", "内置 Qwen2.5（离线）", "", "Qwen2.5-0.5B-Instruct Q4_K_M", "无需网络和 API 密钥，适合默认审查。"),
        new("openai", "OpenAI", "https://api.openai.com/v1", "gpt-4.1-mini", "使用 OpenAI Chat Completions 接口。"),
        new("anthropic", "Anthropic Claude", "https://api.anthropic.com/v1", "claude-sonnet-4-5", "使用 Anthropic Messages API。"),
        new("gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta", "gemini-2.5-flash", "使用 Gemini generateContent API。"),
        new("deepseek", "DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat", "兼容 OpenAI 请求格式。"),
        new("dashscope", "阿里云百炼 / 通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus", "兼容 OpenAI 请求格式。"),
        new("zhipu", "智谱 GLM", "https://open.bigmodel.cn/api/paas/v4", "glm-4-flash", "兼容 OpenAI 请求格式。"),
        new("moonshot", "Moonshot / Kimi", "https://api.moonshot.cn/v1", "moonshot-v1-8k", "兼容 OpenAI 请求格式。"),
        new("siliconflow", "硅基流动", "https://api.siliconflow.cn/v1", "Qwen/Qwen3-8B", "兼容 OpenAI 请求格式。"),
        new("volcengine", "火山方舟 / 豆包", "https://ark.cn-beijing.volces.com/api/v3", "", "模型名称填写方舟推理接入点 ID。"),
        new("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "qwen/qwen3-8b", "兼容 OpenAI 请求格式。"),
        new("ollama", "Ollama 本地服务", "http://127.0.0.1:11434", "qwen3:4b", "连接电脑上已运行的 Ollama。"),
        new("custom", "其他 OpenAI 兼容服务", "", "", "填写服务地址、模型名称和密钥。")
    ];
    public ModelSettings Settings { get; private set; }

    public SettingsWindow(ModelSettings settings)
    {
        InitializeComponent();
        Settings = new() { Enabled = settings.Enabled, Provider = settings.Provider, BaseUrl = settings.BaseUrl, Model = settings.Model, ApiKey = settings.ApiKey, TimeoutSeconds = settings.TimeoutSeconds };
        ProviderCombo.ItemsSource = _providers;
        EnabledCheck.IsChecked = settings.Enabled;
        ProviderCombo.SelectedValue = settings.Provider;
        BaseUrlText.Text = settings.BaseUrl;
        ModelText.Text = settings.Model;
        ApiKeyText.Password = settings.ApiKey;
        UpdateEnabledState();
    }

    private void Title_MouseLeftButtonDown(object sender, MouseButtonEventArgs e) { if (e.LeftButton == MouseButtonState.Pressed) DragMove(); }
    private void Cancel_Click(object sender, RoutedEventArgs e) { DialogResult = false; Close(); }
    private void EnabledChanged(object sender, RoutedEventArgs e) => UpdateEnabledState();
    private void UpdateEnabledState() { if (FieldsPanel is not null) FieldsPanel.IsEnabled = EnabledCheck.IsChecked == true; }
    private void ProviderChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ProviderCombo.SelectedItem is not Provider provider || BaseUrlText is null) return;
        var changing = !string.Equals(provider.Id, Settings.Provider, StringComparison.Ordinal);
        if (changing || string.IsNullOrWhiteSpace(BaseUrlText.Text)) BaseUrlText.Text = provider.Url;
        if (changing || string.IsNullOrWhiteSpace(ModelText.Text)) ModelText.Text = provider.Model;
        ProviderHint.Text = provider.Hint;
        var embedded = provider.Id == "embedded";
        BaseUrlText.IsEnabled = !embedded; ApiKeyText.IsEnabled = !embedded; ModelText.IsEnabled = !embedded;
        ModelsList.ItemsSource = null;
    }
    private ModelSettings ReadSettings() => new() { Enabled = EnabledCheck.IsChecked == true, Provider = (ProviderCombo.SelectedItem as Provider)?.Id ?? "embedded", BaseUrl = BaseUrlText.Text.Trim(), Model = ModelText.Text.Trim(), ApiKey = ApiKeyText.Password.Trim(), TimeoutSeconds = 180 };
    private async void FetchModels_Click(object sender, RoutedEventArgs e)
    {
        try { TestStatus.Text = "正在获取模型列表…"; ModelsList.ItemsSource = await ModelService.ListModelsAsync(ReadSettings()); TestStatus.Text = $"已获取 {ModelsList.Items.Count} 个模型"; }
        catch (Exception error) { TestStatus.Text = error.Message; }
    }
    private void ModelsList_SelectionChanged(object sender, SelectionChangedEventArgs e) { if (ModelsList.SelectedItem is string model) ModelText.Text = model; }
    private void Save_Click(object sender, RoutedEventArgs e)
    {
        var settings = ReadSettings();
        if (settings.Enabled && settings.Provider != "embedded" && (string.IsNullOrWhiteSpace(settings.BaseUrl) || string.IsNullOrWhiteSpace(settings.Model))) { TestStatus.Text = "请填写接口地址和模型名称"; return; }
        Settings = settings; DialogResult = true; Close();
    }
}
