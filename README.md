# Kinematic Syntax Code (KSC)

**A Deterministic, Human-Readable Protocol for Human Skeletal Articulation**

## The Problem

Human motion encoding faces a critical architectural gap:

- **Natural Language** ("raise your arm to shoulder height") is imprecise and ambiguous for machines
- **Binary Motion Formats** (BVH, FBX, SMPL, MOCAP) are unreadable, unsearchable, and impossible to version-control
- **Generative AI models** (MimicMotion, ControlNet, Stable Diffusion) lack a standardized interface for deterministic motion control

**KSC solves this**: A compressed, alphanumeric syntax for encoding anatomical joint rotations into machine-readable strings—think **"MIDI for human motion."**

---

## The Solution

### Core Syntax

```
[SIDE]-[JOINT]-[AXIS]-[VALUE]
```

| Component | Example | Meaning |
|-----------|---------|---------|
| **Side** | `L`, `R` | Left or Right limb (omitted for midline joints like head, spine) |
| **Joint** | `elb`, `shld`, `hip` | Joint identifier from anatomical inventory |
| **Axis** | `x`, `y`, `z` | Rotation axis in 3D space |
| **Value** | `090` | Rotation angle in degrees (0–360) |

### Examples

```ksc
L-elb-z-090      # Left elbow flexion to 90°
R-shld-y-180     # Right shoulder forward flexion to 180° (arm overhead)
head-y-045       # Head rotated 45° to the right
spine-x-045      # Trunk flexion (forward bend) to 45°
```

---

## Use Cases

### 1. Generative AI Control (ControlNet, MimicMotion)

```ksc
# Replace fuzzy natural language with deterministic instructions
@1000ms ~ease-in-out L-shld-y-090 L-elb-z-090 R-shld-y-090 R-elb-z-090
# "Raise both arms to shoulder height over 1 second with ease-in-out interpolation"
```

**Benefit**: Generative models receive **exact, reproducible constraints** instead of probabilistic interpretations.

### 2. Medical & Rehabilitation Documentation

```ksc
# Quantify Range-of-Motion (ROM) assessment
R-shoulder-y-180?  # Query: "Can the patient achieve full shoulder flexion?"
R-knee-z-135?      # Query: "Knee flexion at normal limits?"
```

**Benefit**: Clinical data becomes **textual, auditable, and searchable** for epidemiology studies.

### 3. Robotics & Digital Twins

```ksc
# Industrial manipulation sequence
RESET
@500ms L-shld-y-090 L-elb-z-090 L-wrist-x-000
@300ms L-hand-grip-100  # (Future: hand extension)
@500ms L-shld-y-000      # Reset position
```

**Benefit**: Robot programming becomes **human-readable and versionable** in Git.

### 4. Animation & VFX

```ksc
# Choreography as code
# Wave gesture
@30f R-shld-z-045
@30f R-elb-z-090
@30f R-wrist-x-080
@60f R-shld-z-000 R-elb-z-000 R-wrist-x-000
```

**Benefit**: Motion libraries become **searchable, diffable, and mergeable**.

---

## Technical Stack

### Core Implementation

- **Language**: Python 3.8+
- **Parser**: Tokenizer + BNF grammar validator
- **Validator**: Biomechanical constraint checker
- **Visualizer**: ASCII skeleton renderer (Matplotlib/Plotly optional)

### Interchange Formats

- **Primary**: JSON (web/API compatibility)
- **Import**: BVH (motion capture), SMPL (3D models)
- **Export**: JSON, OpenPose format, BVH

---

## Quick Start

### Installation

```bash
git clone https://github.com/himeairi/Kinematic-Syntax-Code.git
cd Kinematic-Syntax-Code
python3 ksc_core.py
```

### Basic Usage

```python
from ksc_core import KSCParser, KSCValidator

# Parse a KSC command
parser = KSCParser()
parsed = parser.parse("L-elb-z-090")
# Output: {'type': 'joint_command', 'side': 'L', 'joint': 'elb', 'axis': 'z', 'value': 90}

# Validate against biomechanical constraints
validator = KSCValidator()
status = validator.check_constraints(parsed)
# Output: {'valid': True, 'warnings': []}

# Export to JSON
from ksc_core import ksc_to_json
json_output = ksc_to_json(parsed)
```

---

## Joint Inventory (Reference)

### Bilateral Limbs (Left/Right Paired)

| Joint | Abbreviation | Degrees of Freedom | Primary Axis Range |
|-------|--------------|-------------------|-------------------|
| Shoulder | `shld` | 3 | Abduction (0–180°) |
| Elbow | `elb` | 1 | Flexion (0–145°) |
| Wrist | `wrist` | 2 | Flexion (±80°), Deviation (±30°) |
| Hip | `hip` | 3 | Abduction (±45°), Flexion (0–120°) |
| Knee | `knee` | 1 | Flexion (0–135°) |
| Ankle | `ankle` | 2 | Dorsiflexion (±50°), Inversion (±25°) |

### Midline Joints (No Side Prefix)

| Joint | Abbreviation | Degrees of Freedom | Range |
|-------|--------------|-------------------|-------|
| Head/Neck | `head` | 3 | Pitch ±45°, Yaw ±60°, Roll ±30° |
| Spine | `spine` | 3 | Flexion ±45°, Rotation ±45°, Lateral ±25° |

---

## Syntax Features

### Modifiers

```ksc
@30f              # Duration: 30 frames (1 second at 30 FPS)
~ease-in-out      # Easing: smooth acceleration/deceleration
!                 # Force override: bypass biomechanical constraints
?                 # Query mode: validate without applying
# Comment         # Inline documentation
```

### System Commands

```ksc
RESET             # Return all joints to T-Pose (baseline)
CHECK             # Validate current pose
EXPORT json       # Export pose as JSON
IMPORT bvh file   # Import from external format
```

---

## Example Motions

### T-Pose (Baseline)
```ksc
RESET
```

### Standing with arms raised
```ksc
@1000ms ~ease-in-out L-shld-y-090 L-elb-z-090 R-shld-y-090 R-elb-z-090
```

### Yoga: Downward Dog
```ksc
@2000ms spine-x-090 head-x-090 L-shld-y-180 R-shld-y-180 L-hip-z-090 R-hip-z-090
```

### ROM Assessment (Medical)
```ksc
R-shld-y-000?     # Query: baseline
R-shld-y-090?     # Query: 90° abduction
R-shld-y-180?     # Query: full overhead reach
```

---

## Comparison with Alternatives

| Feature | KSC | Natural Language | BVH | SMPL JSON |
|---------|-----|------------------|-----|-----------|
| **Human-Readable** | ✅ Yes | ✅ Yes | ❌ Binary | ❌ Complex |
| **Deterministic** | ✅ Yes | ❌ Ambiguous | ✅ Yes | ✅ Yes |
| **Searchable/Versionable** | ✅ Yes (text) | ❌ No | ❌ No | ✅ JSON compatible |
| **Compact** | ✅ ~10 bytes/command | ❌ ~100 bytes | ✅ Binary | ❌ ~1KB/frame |
| **Constraint-Aware** | ✅ Built-in | ❌ No | ❌ No | ❌ No |
| **GenAI Compatible** | ✅ Yes | ✅ Yes (fuzzy) | ❌ No | ✅ Yes (verbose) |

---

## Roadmap

- [x] **Phase 1**: Core specification & reference parser (v1.0)
- [ ] **Phase 2**: Hand articulation (25+ joints per hand)
- [ ] **Phase 3**: Facial animation (FACS action units)
- [ ] **Phase 4**: ControlNet integration wrapper for Stable Diffusion
- [ ] **Phase 5**: Temporal sequencing grammar (motion graphs)
- [ ] **Phase 6**: arXiv whitepaper publication

---

## Contributing

This is an open-source technical standard. Contributions are welcome:

1. **Propose amendments** via GitHub Issues
2. **Submit pull requests** with new parsers or validators
3. **Add language implementations** (JavaScript, Rust, C++)
4. **Integrate with tools** (Blender, Maya, MotionBuilder plugins)

---

## Licensing

**MIT License** (2026) — Attribution to Ryutara Kiedcharoensiri

This enables commercial adoption while maintaining original author attribution in all derivative works.

---

## Citation

If you use KSC in research or applications, please cite:

```bibtex
@misc{kiedcharoensiri2026ksc,
  author = {Kiedcharoensiri, Ryutara},
  title = {Kinematic Syntax Code: A Deterministic Protocol for Human Skeletal Articulation},
  year = {2026},
  url = {https://github.com/himeairi/Kinematic-Syntax-Code},
  note = {Formal Specification v1.0}
}
```

---

## Documentation

- **[SPECIFICATION.md](SPECIFICATION.md)** — Formal technical specification
- **[ksc_core.py](ksc_core.py)** — Reference Python implementation
- **[Examples](examples/)** — Motion sequences and use cases

---

**Questions?** Open an issue or contact the author at ryutarakiedcharoensiri@gmail.com

**Status**: Actively maintained | **Last Updated**: May 6, 2026
