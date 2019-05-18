# Open GL real time renderer
A real time renderer that loads an OBJ file with python bindings for Open GL, that also provides camera controls and some shader manipulations.

## Requirements
You'll need the following libraries

- glm
- numpy
- pygame
- pyassimp (need to install assimp first)
- pyopengl

## Running
```python glViewer.py```

## In-renderer controls
Camera controls:

- LEFT & RIGHT keys: move circularily along 'x' axis.
- UP & DOWN keys: move along 'y' axis.
- W & S keys: zoom-in and out (move along 'z' axis).

Shader controls:
(The following are not NUMPAD keys)

- 1: Normal Shader (some illumination, sun coming from left side, shadow in right side)
- 2: Sunny Shader (more sun illumination, sun coming from left side, almost no shadow)
- 3: Night Shader (no sun, just some moon light coming from left side)
- 4: Inverted Sun Shader (some illumination, sun coming from right side, shadow in left side)