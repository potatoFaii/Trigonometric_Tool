![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Autodesk Maya](https://img.shields.io/badge/Autodesk%20Maya-37A5CC?style=for-the-badge&logo=autodesk&logoColor=white)

# Trigonometric Expression Tool for Autodesk Maya

---

## Overview

<img width="244" height="400" alt="image" src="https://github.com/user-attachments/assets/abe0c3db-574a-49ac-8175-6f9f4e15fe4f" />

The **Trigonometric Expression Tool** is a Maya helper tool designed to speed up the creation of procedural wave, sine, cosine, and tangent animation expressions.

The tool allows riggers and technical artists to generate expression code from a simple UI instead of manually writing repeated trigonometric formulas for each controller or object.

It is especially useful for creating procedural motion such as:

- Wave motion  
- Spline / chain offset animation  
- Secondary controller motion  
- Repeated FK controller delay effects  
- Side-to-side or up-and-down cyclic animation  
- Tail, rope, cloth-strip, tentacle, or path-controller style motion  

By selecting a main driver controller, choosing a trigonometric function, selecting a target attribute, and selecting multiple target objects, the tool generates a clean expression script with automatic index offset per selected object.

⚠️ This tool is intended for internal studio pipeline usage.

---

## Features

- Generate `sin`, `cos`, or `tan` expression code from a UI  
- Supports selected target attributes such as `.translateX`, `.rotateY`, etc.  
- Manual Channel Box attribute insertion  
- Numeric attribute validation to avoid invalid boolean / enum attributes  
- Multi-selection expression generation based on selected object order  
- Automatic index-based wave offset per selected target  
- ON / OFF radio controls for optional formula components  
- Expression preview window with syntax-highlighted code display  
- Auto-generated expression node name  
- Create or update Maya expression nodes from the preview window  
- Optional attribute creation on the main SDK controller  

---

## Workflow Concept

### 1. Main Controller Input

The **MainController** field stores the driver controller used by the generated expression.

This controller is usually the object that contains the main wave-control attributes, for example:

- `Offset`
- `WaveLength`
- `WaveLength_Offset`
- `Amplitude`
- `Speed`
- `Time_Scale`

Use the **Grab** button after selecting the intended controller in Maya.

Example:

```text
pCube1
Wave_Handle_ctrl_NEW
CPath_Wave_ctrl
```

---

### 2. Trigonometric Function Selection

The **Trigonometric** option menu controls which math function will be used in the generated expression.

Available options:

- `SIN`
- `COS`
- `TAN`

Example output:

```mel
sin(time * controller.Speed)
cos(time * controller.Speed)
tan(time * controller.Speed)
```

The selected option also updates the preview icon inside the UI.

---

### 3. Target Attribute Selection

The **Target_Attribute** field defines which attribute will be driven by the expression.

Preset attributes are available from the right-click popup menu:

- `.translateX`
- `.translateY`
- `.translateZ`
- `.rotateX`
- `.rotateY`
- `.rotateZ`

The tool also supports manual Channel Box insertion.

When using **Insert_Selection**, select exactly one numeric attribute in Maya's Channel Box. The tool converts short names such as:

```text
tx
ry
```

into long attribute names:

```text
.translateX
.rotateY
```

Boolean, enum, and string attributes are rejected to prevent invalid expression output.

---

### 4. Attribute Settings

The **Attribute Settings** section controls which formula components are included in the generated expression.

Each row has an ON / OFF radio button.

| Setting | Description |
|---|---|
| `Target` | Controls whether target assignment lines are generated |
| `Offset` | Adds controller offset into the trig function |
| `WaveLength` | Adds per-target wave spacing into the trig function |
| `WaveLength_Offset` | Multiplies the wavelength by an extra offset amount |
| `Amplitude` | Multiplies the final trig result |
| `Speed` | Multiplies the time value for faster / slower animation |
| `Time_Scale` | Adds an extra time scale multiplier |

When a setting is OFF, that part is removed from the formula instead of being multiplied by zero.

This avoids unwanted results such as the whole expression becoming zero.

---

### 5. Target Object Selection

After the main controller, function, and target attribute are set, select the target objects in Maya.

Each selected object will generate one expression line.

The index starts from `1` and increases for every selected object.

Example selected objects:

```text
CPath_SplineIK_main_00_C_OG
CPath_SplineIK_main_01_C_OG
CPath_SplineIK_main_02_C_OG
```

Generated expression concept:

```mel
CPath_SplineIK_main_00_C_OG.rotateY = cos(time * Wave_Handle_ctrl.Speed + Wave_Handle_ctrl.Offset + Wave_Handle_ctrl.WaveLength * Wave_Handle_ctrl.WaveLength_Offset * 1) * Wave_Handle_ctrl.Amplitude;
CPath_SplineIK_main_01_C_OG.rotateY = cos(time * Wave_Handle_ctrl.Speed + Wave_Handle_ctrl.Offset + Wave_Handle_ctrl.WaveLength * Wave_Handle_ctrl.WaveLength_Offset * 2) * Wave_Handle_ctrl.Amplitude;
CPath_SplineIK_main_02_C_OG.rotateY = cos(time * Wave_Handle_ctrl.Speed + Wave_Handle_ctrl.Offset + Wave_Handle_ctrl.WaveLength * Wave_Handle_ctrl.WaveLength_Offset * 3) * Wave_Handle_ctrl.Amplitude;
```

If selection order is important, enable Maya selection order tracking before selecting targets:

```python
cmds.selectPref(trackSelectionOrder=True)
```

---

### 6. Expression Preview Window

Clicking **Generate** opens the **Trigonometric_Expression** preview window.

This window displays:

- Generated script node / expression node name
- Generated expression code
- Syntax-highlighted preview
- Create button for creating the expression in Maya

The expression name is generated from:

```text
<mainController>_<targetAttribute>_<trigonometric>_EXP
```

Example:

```text
pCube1_translateX_sin_EXP
```

---

### 7. Create Expression Node

Clicking **Create** in the expression preview window should:

1. Add required driver attributes onto the main controller if missing  
2. Create a Maya expression node using the expression node name  
3. Insert the generated expression code into the expression node  
4. Update the existing expression node if the same name already exists  
5. Optionally open Maya's Expression Editor with expression filter enabled  

Example Maya command concept:

```python
cmds.expression(
    name="pCube1_translateX_sin_EXP",
    s=expression_text,
    ae=True,
    uc="all"
)
```

---

## Formula Logic

The generated formula is built from enabled UI settings.

Base structure:

```mel
target.attribute = trig(time + optionalParts);
```

With all common settings enabled:

```mel
target.attribute = trig(time * sdk.Time_Scale * sdk.Speed + sdk.Offset + sdk.WaveLength * sdk.WaveLength_Offset * index) * sdk.Amplitude;
```

Example:

```mel
pCube2.translateX = sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.Offset + pCube1.WaveLength * pCube1.WaveLength_Offset * 1) * pCube1.Amplitude;
```

If `Amplitude` is OFF:

```mel
pCube2.translateX = sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.Offset + pCube1.WaveLength * pCube1.WaveLength_Offset * 1);
```

If `Offset` is OFF:

```mel
pCube2.translateX = sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.WaveLength * pCube1.WaveLength_Offset * 1) * pCube1.Amplitude;
```

If `WaveLength` is OFF:

```mel
pCube2.translateX = sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.Offset) * pCube1.Amplitude;
```

---

## Installation

1. Open Autodesk Maya  
2. Place the tool files inside the studio Maya script path  
3. Make sure the following Python files are available:

```text
Trigonometric_UI.py
Trigonometric_UI_Expression.py
Trigonometric_Expression_Create.py
```

4. Run the launcher command from Script Editor or a shelf button:

```python
import Trigonometric_UI
reload(Trigonometric_UI)
Trigonometric_UI.Trigonometric_UI()
```

For Maya Python 3:

```python
from importlib import reload
import Trigonometric_UI
reload(Trigonometric_UI)
Trigonometric_UI.Trigonometric_UI()
```

---

## Usage

1. Select the main driver controller  
2. Click **Grab** in the MainController section  
3. Choose `SIN`, `COS`, or `TAN`  
4. Choose a target attribute from the popup menu or Channel Box  
5. Turn formula settings ON / OFF as needed  
6. Select all target objects that should receive expression lines  
7. Click **Generate**  
8. Review the generated expression in the preview window  
9. Click **Create** to create or update the Maya expression node  

---

## Required / Generated Attributes

The main controller may receive these attributes depending on enabled settings:

| Attribute | Default | Purpose |
|---|---:|---|
| `Offset` | `0.0` | Shifts the wave phase |
| `WaveLength` | `1.0` | Controls spacing between selected targets |
| `WaveLength_Offset` | `0.01` | Additional multiplier for wavelength spacing |
| `Amplitude` | `1.0` | Controls output strength |
| `Speed` | `1.0` | Controls animation speed |
| `Time_Scale` | `0.1` | Global time multiplier |

Optional target attribute:

| Attribute | Default | Purpose |
|---|---:|---|
| `BlendExpression` | `1.0` | Allows per-target blending of expression output |

---

## Notes for Riggers

- The target attribute must exist on every selected target object.  
- Channel Box manual insertion only accepts numeric attributes.  
- Selection order affects generated wave index.  
- `WaveLength_Offset` is ignored if `WaveLength` is OFF.  
- `Target` OFF means no target assignment lines should be generated.  
- Existing expression nodes with the same name can be updated instead of duplicated.  
- Short node names are used in expression code for cleaner output.  

---

## Example Output

```mel
// Generated Trigonometric Expression
// Main Controller : pCube1
// Target Count    : 6

pCube2.translateX = (sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.Offset + pCube1.WaveLength * pCube1.WaveLength_Offset * 1) * pCube1.Amplitude);
pCube3.translateX = (sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.Offset + pCube1.WaveLength * pCube1.WaveLength_Offset * 2) * pCube1.Amplitude);
pCube4.translateX = (sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.Offset + pCube1.WaveLength * pCube1.WaveLength_Offset * 3) * pCube1.Amplitude);
pCube5.translateX = (sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.Offset + pCube1.WaveLength * pCube1.WaveLength_Offset * 4) * pCube1.Amplitude);
pCube6.translateX = (sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.Offset + pCube1.WaveLength * pCube1.WaveLength_Offset * 5) * pCube1.Amplitude);
pCube7.translateX = (sin(time * pCube1.Time_Scale * pCube1.Speed + pCube1.Offset + pCube1.WaveLength * pCube1.WaveLength_Offset * 6) * pCube1.Amplitude);
```

---

## Troubleshooting

### Generate button does not create expression lines

Check that target objects are selected before pressing **Generate**.

---

### Target attribute does not exist warning

Make sure the selected target objects have the target attribute you selected, such as `.translateX` or `.rotateY`.

---

### Boolean / visibility attributes are rejected

This is expected. Expression output should drive numeric attributes only.

---

### Expression result is too strong

Lower the `Amplitude` attribute on the main controller.

---

### Wave offset is not visible

Make sure `WaveLength` is ON. `WaveLength_Offset` is only useful when `WaveLength` is enabled.

---

## Recommended File Structure

```text
TrigonometricTool/
│
├─ Trigonometric_UI.py
├─ Trigonometric_UI_Expression.py
├─ Trigonometric_Expression_Create.py
│
├─ Icon_Trigonometric/
│  ├─ sin.png
│  ├─ cos.png
│  └─ tan.png
│
└─ README.md
```

---

## Status

Current tool status:

- UI generation: complete  
- Attribute query: complete  
- Radio-button formula filtering: complete  
- Multi-target expression generation: complete  
- Expression preview window: complete  
- Expression node creation: in progress / final integration stage  

---

## License / Usage

Internal production tool.  
Use and modify according to studio pipeline requirements.
