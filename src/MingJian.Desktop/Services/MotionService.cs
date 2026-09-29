using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Animation;

namespace MingJian.Desktop.Services;

public static class MotionService
{
    public static bool IsEnabled => SystemParameters.ClientAreaAnimation;

    public static int Duration(int milliseconds) => IsEnabled ? milliseconds : 0;

    public static void PrepareEnter(UIElement element, double offsetX = 18, double opacity = 0)
    {
        var transform = EnsureTranslateTransform(element);
        element.BeginAnimation(UIElement.OpacityProperty, null);
        transform.BeginAnimation(TranslateTransform.XProperty, null);
        element.Opacity = IsEnabled ? opacity : 1;
        transform.X = IsEnabled ? offsetX : 0;
    }

    public static void Animate(UIElement element, double opacity, double offsetX, int milliseconds)
    {
        var transform = EnsureTranslateTransform(element);
        if (!IsEnabled || milliseconds <= 0)
        {
            element.BeginAnimation(UIElement.OpacityProperty, null);
            transform.BeginAnimation(TranslateTransform.XProperty, null);
            element.Opacity = opacity;
            transform.X = offsetX;
            return;
        }

        var easing = new CubicEase { EasingMode = EasingMode.EaseOut };
        AnimateDouble(element, UIElement.OpacityProperty, opacity, milliseconds, easing);
        AnimateDouble(transform, TranslateTransform.XProperty, offsetX, milliseconds, easing);
    }

    public static void AnimateThemeIcon(FrameworkElement element, double from, double to, int milliseconds)
    {
        var rotation = element.RenderTransform as RotateTransform ?? new RotateTransform();
        element.RenderTransform = rotation;
        element.RenderTransformOrigin = new Point(0.5, 0.5);
        if (!IsEnabled)
        {
            rotation.Angle = to;
            return;
        }

        rotation.Angle = to;
        rotation.BeginAnimation(RotateTransform.AngleProperty, new DoubleAnimation(from, to, TimeSpan.FromMilliseconds(milliseconds))
        {
            EasingFunction = new CubicEase { EasingMode = EasingMode.EaseOut },
            FillBehavior = FillBehavior.Stop
        });
    }

    public static void Reset(UIElement element)
    {
        element.BeginAnimation(UIElement.OpacityProperty, null);
        element.Opacity = 1;
        if (element.RenderTransform is TranslateTransform transform)
        {
            transform.BeginAnimation(TranslateTransform.XProperty, null);
            transform.X = 0;
        }
    }

    private static TranslateTransform EnsureTranslateTransform(UIElement element)
    {
        if (element.RenderTransform is TranslateTransform transform) return transform;
        transform = new TranslateTransform();
        element.RenderTransform = transform;
        return transform;
    }

    private static void AnimateDouble(UIElement target, DependencyProperty property, double to, int milliseconds, IEasingFunction easing)
    {
        var from = (double)target.GetValue(property);
        target.SetValue(property, to);
        target.BeginAnimation(property, new DoubleAnimation(from, to, TimeSpan.FromMilliseconds(milliseconds))
        {
            EasingFunction = easing,
            FillBehavior = FillBehavior.Stop
        }, HandoffBehavior.SnapshotAndReplace);
    }

    private static void AnimateDouble(Animatable target, DependencyProperty property, double to, int milliseconds, IEasingFunction easing)
    {
        var from = (double)target.GetValue(property);
        target.SetValue(property, to);
        target.BeginAnimation(property, new DoubleAnimation(from, to, TimeSpan.FromMilliseconds(milliseconds))
        {
            EasingFunction = easing,
            FillBehavior = FillBehavior.Stop
        }, HandoffBehavior.SnapshotAndReplace);
    }
}
