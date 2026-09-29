using MingJian.Desktop.Services;
using System.Windows;
using System.Windows.Media;

namespace MingJian.Desktop.Tests;

public sealed class ThemeServiceTests
{
    [Fact]
    public void Apply_ReplacesFrozenBrushes_AndSupportsRepeatedSwitching()
    {
        var original = new SolidColorBrush(Color.FromRgb(9, 16, 21));
        original.Freeze();
        var resources = new ResourceDictionary { ["AppBrush"] = original };

        ThemeService.Apply(resources, dark: false);
        var light = Assert.IsType<SolidColorBrush>(resources["AppBrush"]);
        Assert.NotSame(original, light);
        Assert.Equal(Color.FromRgb(244, 247, 246), light.Color);

        ThemeService.Apply(resources, dark: true);
        var dark = Assert.IsType<SolidColorBrush>(resources["AppBrush"]);
        Assert.Equal(Color.FromRgb(9, 16, 21), dark.Color);
    }
}
