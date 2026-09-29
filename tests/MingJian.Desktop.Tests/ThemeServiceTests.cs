using MingJian.Desktop.Services;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace MingJian.Desktop.Tests;

public sealed class ThemeServiceTests
{
    private sealed record TestProvider(string Name);

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

    [Fact]
    public void ApplyAnimated_UsesWritableBrushesWithTargetBaseColors()
    {
        var resources = new ResourceDictionary
        {
            ["AppBrush"] = new SolidColorBrush(Color.FromRgb(9, 16, 21))
        };

        ThemeService.ApplyAnimated(resources, dark: false, TimeSpan.FromMilliseconds(200));

        var brush = Assert.IsType<SolidColorBrush>(resources["AppBrush"]);
        Assert.False(brush.IsFrozen);
        Assert.Equal(Color.FromRgb(244, 247, 246), brush.GetAnimationBaseValue(SolidColorBrush.ColorProperty));
    }

    [Fact]
    public void ComboBoxStyle_FollowsDynamicThemeResources()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                var app = new App();
                app.InitializeComponent();
                var style = Assert.IsType<Style>(app.Resources[typeof(ComboBox)]);
                var comboBox = new ComboBox { Style = style, DisplayMemberPath = nameof(TestProvider.Name) };
                comboBox.Items.Add(new TestProvider("测试提供方"));
                comboBox.SelectedIndex = 0;
                var window = new Window { Content = comboBox, Width = 320, Height = 120, ShowInTaskbar = false };
                window.Show();

                ThemeService.Apply(app.Resources, dark: true);
                window.Dispatcher.Invoke(() => { });
                Assert.Equal(Color.FromRgb(22, 35, 43), Assert.IsType<SolidColorBrush>(comboBox.Background).Color);
                Assert.Equal(Color.FromRgb(242, 247, 245), Assert.IsType<SolidColorBrush>(comboBox.Foreground).Color);
                Assert.NotNull(comboBox.Template);
                comboBox.ApplyTemplate();
                window.UpdateLayout();
                Assert.Contains(VisualChildren<TextBlock>(comboBox), text => text.Text == "测试提供方");

                ThemeService.Apply(app.Resources, dark: false);
                window.Dispatcher.Invoke(() => { });
                Assert.Equal(Color.FromRgb(232, 239, 236), Assert.IsType<SolidColorBrush>(comboBox.Background).Color);
                Assert.Equal(Color.FromRgb(19, 32, 28), Assert.IsType<SolidColorBrush>(comboBox.Foreground).Color);
                window.Close();
            }
            catch (Exception exception)
            {
                failure = exception;
            }
        });

        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();

        Assert.Null(failure);
    }

    private static IEnumerable<T> VisualChildren<T>(DependencyObject parent) where T : DependencyObject
    {
        for (var index = 0; index < VisualTreeHelper.GetChildrenCount(parent); index++)
        {
            var child = VisualTreeHelper.GetChild(parent, index);
            if (child is T match) yield return match;
            foreach (var descendant in VisualChildren<T>(child)) yield return descendant;
        }
    }
}
