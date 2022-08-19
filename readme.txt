Omgifol -- a Python library for Doom WAD files

Originally by Fredrik Johansson (http://fredrikj.net).
Maintained since 0.3.0 by Devin Acker (http://revenant1.net).

Use `pip install omgifol` to install. See manual.html (and module/class 
docstrings) for usage notes. Requires Python 3.x.

Some planned things:

 - Basic Doom 0.4 / 0.5 wad support in master
 - Basic Doom 64 wad support
 - support for non-vanilla/Boom maps in lineinfo
 - some stuff from AlexMax's fork

The "doomalphas" branch contains extremely rudimentary loading of maps from the
Doom 0.4 / 0.5 alphas. It was used to generate linedef animations for the
"dmvis" project and is pretty much completely useless for anything else (it
only loads linedefs and things, not sectors or texture/flat info). The struct
info was gleaned from the Yadex source code (thanks!)
