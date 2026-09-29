using MingJian.Desktop.Services;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace MingJian.Desktop.Tests;

public sealed class MotionServiceTests
{
    [Fact]
    public void PageMotion_SetsStableFinalValuesAfterAnimations()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                var element = new Border();
                MotionService.PrepareEnter(element, 18);
                MotionService.Animate(element, 1, 0, 240);

                Assert.Equal(1d, element.GetAnimationBaseValue(UIElement.OpacityProperty));
                var transform = Assert.IsType<TranslateTransform>(element.RenderTransform);
                Assert.Equal(0d, transform.GetAnimationBaseValue(TranslateTransform.XProperty));

                MotionService.Reset(element);
                Assert.Equal(1d, element.Opacity);
                Assert.Equal(0d, transform.X);
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
}
