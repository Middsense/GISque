Each plugin is defined as a `class`. The class name should be the same as the
module name to insure the plugin is properly loaded.

There are three main plugin classes: `Input`, `Analysis` and `Output`.

The class of a plugin is defined by the attribute `pluginClass`.

Within each class, plugins can be defined to belong to a `group`. All the
plugins belonging to the same group will be listed within that group.
The group of a plugin is defined by the attribute `pluginGroup`.

Each plugin should also define the following attributes:

* `pluginLabel`: will beused to identify the plugin on the main screen

* `pluginCommand`: a callback function, implemented as a class method, taking
the following parameters:
    * `image` an istance of the image displayed on the main screen
    * `stack`: an istance of the image stack displayes on the main screen
    * `status`: a callback function to the update function for the status bar
on the main screen.

If the plugins needs to open a new windows it should make use of the TkInter
method `Toplevel()` and take care of dstroying the window on exit.

This is an example for a very simple plugin performing log strech of the image
on the main screen:

```python
import numpy as np

class StretchImage(object):
    def __init__(self):
        self.pluginClass = 'Analysis'
        self.pluginGroup = 'Image'
        self.pluginLabel = 'Log10 Stretch'
        self.pluginCommand = self.callback

    def callback(self, image, stack, status):
        status('Evaluating Log10...')
        image = np.log10(1.0 + image)
        status()
```
