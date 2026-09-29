using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Animation;

namespace MingJian.Desktop.Services;

public static class ThemeService
{
    private static readonly IReadOnlyDictionary<string, string> DarkPalette = new Dictionary<string, string>
    {
        ["AppBrush"] = "#091015",
        ["SidebarBrush"] = "#0D151B",
        ["SurfaceBrush"] = "#111C23",
        ["SurfaceAltBrush"] = "#16232B",
        ["SurfaceHoverBrush"] = "#1B2B34",
        ["BorderBrush"] = "#263841",
        ["TextBrush"] = "#F2F7F5",
        ["MutedBrush"] = "#90A29F",
        ["FaintBrush"] = "#61736F",
        ["AccentDarkBrush"] = "#102D25",
        ["AccentTextBrush"] = "#07130F"
    };

    private static readonly IReadOnlyDictionary<string, string> LightPalette = new Dictionary<string, string>
    {
        ["AppBrush"] = "#F4F7F6",
        ["SidebarBrush"] = "#ECF1EF",
        ["SurfaceBrush"] = "#FFFFFF",
        ["SurfaceAltBrush"] = "#E8EFEC",
        ["SurfaceHoverBrush"] = "#DFE9E5",
        ["BorderBrush"] = "#CFDBD6",
        ["TextBrush"] = "#13201C",
        ["MutedBrush"] = "#5E706A",
        ["FaintBrush"] = "#81918C",
        ["AccentDarkBrush"] = "#D8F5E8",
        ["AccentTextBrush"] = "#07130F"
    };

    public static void Apply(ResourceDictionary resources, bool dark)
    {
        var palette = dark ? DarkPalette : LightPalette;
        foreach (var (key, value) in palette)
        {
            var color = (Color)ColorConverter.ConvertFromString(value);
            resources[key] = new SolidColorBrush(color);
        }
    }

    public static void ApplyAnimated(ResourceDictionary resources, bool dark, TimeSpan duration)
    {
        if (!SystemParameters.ClientAreaAnimation || duration <= TimeSpan.Zero)
        {
            Apply(resources, dark);
            return;
        }

        var palette = dark ? DarkPalette : LightPalette;
        var easing = new CubicEase { EasingMode = EasingMode.EaseOut };
        foreach (var (key, value) in palette)
        {
            var targetColor = (Color)ColorConverter.ConvertFromString(value);
            var currentColor = resources[key] is SolidColorBrush current ? current.Color : targetColor;
            var brush = new SolidColorBrush(targetColor);
            brush.BeginAnimation(SolidColorBrush.ColorProperty, new ColorAnimation(currentColor, targetColor, duration)
            {
                EasingFunction = easing,
                FillBehavior = FillBehavior.Stop
            }, HandoffBehavior.SnapshotAndReplace);
            resources[key] = brush;
        }
    }
}
