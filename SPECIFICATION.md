# Kinematic Syntax Code (KSC) — Technical Specification

**Version**: 1.0  
**Date**: May 6, 2026  
**Author**: Ryutara Kiedcharoensiri  
**Status**: Formal Specification

---

## 1. Introduction

Kinematic Syntax Code (KSC) is a **deterministic, human-readable protocol** for encoding human skeletal articulation into alphanumeric strings. It provides:

- **Precision**: Exact degree values with biomechanical constraints
- **Readability**: Text-based, version-controllable, searchable
- **Interoperability**: Language-agnostic JSON interchange format
- **Extensibility**: Support for motion sequences, easing, and metadata

This specification defines the formal grammar, joint inventory, coordinate system, validation rules, and interchange formats.

---

## 2. Formal Grammar (BNF)

```bnf
<ksc_command>       ::= <ksc_atom> | <ksc_sequence>
<ksc_sequence>      ::= <ksc_atom> ( " " <ksc_atom> )*
<ksc_atom>          ::= [<modifier>] <joint_command> | <system_command>

<modifier>          ::= "@" <duration> | "~" <easing> | "!" | "?" | "#" <comment>

<joint_command>     ::= <side> "-" <joint> "-" <axis> "-" <value>
<side>              ::= "L" | "R" | "" (for bilateral joints like "head", "spine")
<joint>             ::= "head" | "spine" | "shld" | "elb" | "wrist" | "hip" | "knee" | "ankle"
<axis>              ::= "x" | "y" | "z"
<value>             ::= <digit>+ (0-360)

<system_command>    ::= "RESET" | "CHECK" | "EXPORT" | "IMPORT"
<duration>          ::= <digit>+ ("ms" | "f" | "s")
<easing>            ::= "linear" | "ease-in" | "ease-out" | "ease-in-out" | "sine" | "quad" | "cubic"

<comment>           ::= [any character]*
```

---

## 3. Joint Inventory & Constraints

### Bilateral Joints (Paired Left/Right)

| Joint Code | Full Name | DoF | X-Axis (Primary) | Y-Axis (Secondary) | Z-Axis (Tertiary) | Notes |
|------------|-----------|-----|------------------|-------------------|-------------------|-------|
| `shld` | Shoulder | 3 | Abduction: 0–180° | Flexion: 0–180° | Int/Ext Rot: ±90° | Glenohumeral ball-socket joint |
| `elb` | Elbow | 1 | — | — | Flexion: 0–145° | Hinge joint; supination/pronation in forearm |
| `wrist` | Wrist | 2 | Flexion: ±80° | Radial/Ulnar Dev: ±30° | — | Limited DoF; excludes forearm rotation |
| `hip` | Hip | 3 | Abduction: ±45° | Flexion: 0–120° | Int/Ext Rot: ±45° | Ball-socket; flexion > extension asymmetry |
| `knee` | Knee | 1 | — | — | Flexion: 0–135° | Hinge joint; passive extension ~5–10° |
| `ankle` | Ankle | 2 | Dorsi/Plantarflexion: ±50° | Inversion/Eversion: ±25° | — | Limited DoF |

### Midline Joints (Singular, No Side Prefix)

| Joint Code | Full Name | DoF | X-Axis | Y-Axis | Z-Axis | Notes |
|------------|-----------|-----|--------|--------|--------|-------|
| `head` | Head/Neck | 3 | Pitch (Flexion): ±45° | Yaw (Rotation): ±60° | Roll (Lateral): ±30° | Includes upper cervical spine |
| `spine` | Thoracic/Lumbar Spine | 3 | Flexion: ±45° | Rotation: ±45° | Lateral Flexion: ±25° | Primary trunk articulation |

---

## 4. Coordinate System (Right-Hand Convention)

### Reference Frame (T-Pose Baseline)

```
        +Y (Up)
        ↑
        |
    +Z  ├───→ +X (Right)
  (Back)|
   ←────┘
   (Front)
```

### Per-Joint Coordinate System Definition

All joints follow the **local right-hand convention** derived from the T-Pose:

#### Bilateral Limbs (Arms & Legs)

**Left Side**: Axes mirror the anatomical plane.  
**Right Side**: Axes follow global convention.

| Joint Type | X-Axis | Y-Axis | Z-Axis |
|-----------|--------|--------|--------|
| **Shoulder** | Abduction (±) | Flexion (±) | Internal/External Rotation (±) |
| **Elbow** | (locked) | (locked) | Flexion/Extension (0-145°) |
| **Wrist** | Flexion/Extension (±) | Radial/Ulnar Deviation (±) | (locked) |
| **Hip** | Abduction (±) | Flexion (0-120°) | Internal/External Rotation (±) |
| **Knee** | (locked) | (locked) | Flexion/Extension (0-135°) |
| **Ankle** | Dorsi/Plantarflexion (±) | Inversion/Eversion (±) | (locked) |

#### Midline Joints (Head & Spine)

| Joint Type | X-Axis | Y-Axis | Z-Axis |
|-----------|--------|--------|--------|
| **Head** | Pitch (Flexion) ±45° | Yaw (Rotation) ±60° | Roll (Lateral) ±30° |
| **Spine** | Flexion (Anterior) ±45° | Rotation (Horizontal) ±45° | Lateral Flexion ±25° |

### Angle Representation

- **Range**: 0–360° (full rotation)
- **Negative angles**: Indicate movement in opposite direction (e.g., `-90` = 270°)
- **Precision**: Integer degrees (no decimal places in standard KSC)

---

## 5. Command Syntax

### 5.1 Basic Joint Command

```
[SIDE]-[JOINT]-[AXIS]-[VALUE]
```

**Example**: `L-shld-x-090` → Left shoulder abduction to 90°

### 5.2 Modifiers

#### Duration Modifier (`@`)

Specifies animation duration or timing.

```
@<number><unit>
```

**Units**:
- `f` = frames (default 30 FPS)
- `ms` = milliseconds
- `s` = seconds

**Examples**:
```
@30f      # 30 frames (1 second at 30 FPS)
@500ms    # 500 milliseconds
@2s       # 2 seconds
```

#### Easing Modifier (`~`)

Specifies interpolation curve for motion.

```
~<easing_function>
```

**Functions**:
- `linear`: No acceleration
- `ease-in`: Slow start
- `ease-out`: Slow end
- `ease-in-out`: Smooth start & end
- `sine`, `quad`, `cubic`: Polynomial easing curves

**Example**: `@30f ~ease-in L-shld-z-090` → Raise arm over 1 second with ease-in

#### Force Override (`!`)

Bypasses biomechanical constraints (use with caution).

```
!L-hip-x-200    # Hip abduction to 200° (violates normal constraints)
```

#### Query/Validation (`?`)

Returns constraint status without applying change.

```
?L-elb-z-160    # Returns: "WARNING: Exceeds typical elbow flexion (145°)"
```

#### Comments (`#`)

Inline documentation.

```
@30f L-shld-z-090  # Raise left arm to shoulder height
```

---

## 6. System Commands

| Command | Effect | Example |
|---------|--------|---------|
| `RESET` | Return all joints to T-Pose baseline | `RESET` |
| `CHECK` | Validate current pose against constraints | `CHECK` |
| `EXPORT` | Output pose as JSON | `EXPORT json` |
| `IMPORT <format>` | Load pose from external format | `IMPORT bvh file.bvh` |
| `COMMENT <text>` | Add metadata | `COMMENT Subject: John Doe` |

---

## 7. JSON Interchange Format

### Single Command

```json
{
  "type": "joint_command",
  "side": "L",
  "joint": "elb",
  "axis": "z",
  "value": 90,
  "modifiers": {
    "duration": { "value": 30, "unit": "f" },
    "easing": "ease-in",
    "force": false,
    "comment": "Raise arm to shoulder height"
  }
}
```

### Sequence (Multiple Commands)

```json
{
  "type": "sequence",
  "metadata": {
    "name": "Wave Greeting",
    "duration_total": 2000,
    "fps": 30,
    "created": "2026-05-06T10:00:00Z",
    "author": "himeairi"
  },
  "commands": [
    {
      "type": "system",
      "command": "RESET"
    },
    {
      "type": "joint_command",
      "side": "R",
      "joint": "shld",
      "axis": "z",
      "value": 45,
      "modifiers": { "duration": { "value": 10, "unit": "f" } }
    },
    {
      "type": "joint_command",
      "side": "R",
      "joint": "elb",
      "axis": "z",
      "value": 90,
      "modifiers": { "duration": { "value": 10, "unit": "f" } }
    }
  ]
}
```

---

## 8. Validation Rules

### 8.1 Constraint Validation

Every joint command is validated against:

1. **Range Check**: Angle within ±360°
2. **Joint-Specific Limits**: Compare against joint constraint table (Section 3)
3. **DoF Check**: Ensure only valid axes are used (e.g., elbow only accepts Z-axis)
4. **Side Check**: Verify side prefix is valid (L/R for bilateral, none for midline)

**Return Codes**:
- `OK`: Command is valid
- `WARNING`: Command violates typical constraints but can be executed with `!` override
- `ERROR`: Command is malformed or impossible

### 8.2 Biomechanical Constraints

**Hard Constraints** (cannot be violated):

```
L-elb-x-045    → ERROR: Elbow only supports Z-axis
R-ankle-z-090  → ERROR: Ankle does not support Z-axis rotation
head-w-090     → ERROR: Invalid axis "w"
```

**Soft Constraints** (warning only):

```
L-hip-x-090    → WARNING: Exceeds typical hip abduction (45°), use ! to override
R-knee-z-180   → WARNING: Knee rarely flexes past 135°, use ! to override
```

---

## 9. Parsing Algorithm

### Input: KSC String
### Output: Parsed Command Object or Error

```python
def parse_ksc(command_string):
    """
    1. Tokenize: Split by spaces, extract modifiers
    2. Validate Grammar: Match against BNF
    3. Extract Components: side, joint, axis, value
    4. Check Constraints: Range & DoF validation
    5. Return: Parsed object or error message
    """
    
    # Step 1: Strip comments
    if '#' in command_string:
        command_string = command_string.split('#')[0].strip()
    
    # Step 2: Extract modifiers
    modifiers = {}
    tokens = command_string.split()
    main_command = None
    
    for token in tokens:
        if token.startswith('@'):
            modifiers['duration'] = parse_duration(token)
        elif token.startswith('~'):
            modifiers['easing'] = parse_easing(token)
        elif token == '!':
            modifiers['force'] = True
        elif token == '?':
            modifiers['query'] = True
        else:
            main_command = token
    
    # Step 3: Parse main command
    if main_command in ['RESET', 'CHECK', 'EXPORT']:
        return {'type': 'system', 'command': main_command}
    
    # Step 4: Parse joint command
    parts = main_command.split('-')
    if len(parts) == 3:
        joint, axis, value = parts
        side = ''
    elif len(parts) == 4:
        side, joint, axis, value = parts
    else:
        raise SyntaxError(f"Invalid KSC syntax: {main_command}")
    
    # Step 5: Validate and return
    return {
        'type': 'joint_command',
        'side': side,
        'joint': joint,
        'axis': axis,
        'value': int(value),
        'modifiers': modifiers
    }
```

---

## 10. Extension Framework

### 10.1 Hand Articulation (Future)

```
# 5 digits × 4 joints per digit = 20 DoF per hand
L-f1-x-090   # Left index finger, flexion 90°
R-thumb-z-045  # Right thumb, rotation 45°
```

### 10.2 Facial Animation (FACS Compatible)

```
# Action Units (AUs) mapped to KSC
face-au-001  # Inner brow raiser
face-au-012  # Lip corner puller (smile)
```

### 10.3 Temporal Sequencing

```
# Motion synthesis notation (TBD)
@1000ms L-shld-z-090 → R-shld-z-090  # Sequential motion
```

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-06 | Initial specification; 24-joint core inventory |
| (Planned) | Q2 2026 | Hand articulation extension |
| (Planned) | Q3 2026 | Facial animation (FACS) |

---

## 12. References

### Anatomical References

- **ISB (International Society of Biomechanics)** — Joint coordinate system conventions
- **Mayo Clinic** — Normal range of motion (ROM) standards
- **Neumann, DA** — *Kinesiology of the Musculoskeletal System* (3rd ed.)

### Technical References

- **SMPL Model** (Loper et al., 2015) — Human body parameterization
- **BVH Format** — Biovision Hierarchical Data (de facto motion capture standard)
- **OpenPose** — Joint detection and tracking

---

## 13. Appendix: Quick Reference

### Common Poses

```
# T-Pose (Baseline/RESET)
head-y-000 spine-x-000 spine-y-000 spine-z-000
L-shld-x-000 L-shld-y-000 L-elb-z-000 L-wrist-x-000
R-shld-x-000 R-shld-y-000 R-elb-z-000 R-wrist-x-000
L-hip-x-000 L-hip-y-000 L-knee-z-000 L-ankle-x-000
R-hip-x-000 R-hip-y-000 R-knee-z-000 R-ankle-x-000

# Standing with arms at sides (Neutral)
RESET L-shld-y-045 R-shld-y-045

# Reaching forward (Object manipulation)
L-shld-y-090 L-elb-z-090 L-wrist-x-000

# Yoga: Downward Dog
spine-x-090 head-x-090 L-hip-z-090 R-hip-z-090
L-shld-y-180 R-shld-y-180

# Arm raise overhead (ROM assessment)
@30f ~ease-in-out L-shld-y-090
@30f ~ease-in-out L-shld-y-180
```

---

**End of Specification**  
For questions or proposed amendments, please open a GitHub Issue.
