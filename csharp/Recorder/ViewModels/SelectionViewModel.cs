using CommunityToolkit.Mvvm.ComponentModel;
using System.Drawing;

namespace Recorder.ViewModels
{
    public partial class SelectionViewModel : ObservableObject
    {
        [ObservableProperty]
        private Rectangle selectedArea;

        [ObservableProperty]
        private string selectionDetails;
    }
}