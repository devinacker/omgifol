Omgifol -- a Python library for Doom WAD files

By Fredrik Johansson
http://fredrikj.net

See manual.html for installation and usage notes.
Requires Python 2.7.

This is Revenant's personal fork. What's new:

 - support for Hexen / ZDoom maps
 - better handling of missing map data (including nodes)
 - better map loading (supports names other than ExMx and MAPxx,
   doesn't mistake MAPINFO for an actual map)
 - better support for "limit removing" maps
 
Some planned things:

 - UDMF map support
 - Basic Doom 0.4 / 0.5 wad support in master
 - Basic Doom 64 wad support
 - support for non-vanilla/Boom maps in lineinfo
 - some stuff from AlexMax's fork

The "doomalphas" branch contains extremely rudimentary loading of maps from the
Doom 0.4 / 0.5 alphas. It was used to generate linedef animations for the
"dmvis" project and is pretty much completely useless for anything else (it
only loads linedefs and things, not sectors or texture/flat info). The struct
info was gleaned from the Yadex source code (thanks!)
