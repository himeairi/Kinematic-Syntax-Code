#!/usr/bin/env python3
"""
Kinematic Syntax Code (KSC) — Reference Implementation

Core parser, validator, and visualization engine for the KSC protocol.

Author: Ryutara Kiedcharoensiri
License: MIT (2026)
"""

import re
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
from enum import Enum


# ============================================================================
# DATA MODELS
# ============================================================================

class ErrorLevel(Enum):
    """Severity levels for validation results."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Modifier:
    """Container for KSC command modifiers."""
    duration: Optional[Dict[str, str]] = None
    easing: Optional[str] = None
    force_override: bool = False
    query_mode: bool = False
    comment: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None and v is not False}


@dataclass
class KSCCommand:
    """Parsed KSC joint command."""
    type: str  # "joint_command" or "system"
    side: Optional[str] = None
    joint: Optional[str] = None
    axis: Optional[str] = None
    value: Optional[int] = None
    modifiers: Optional[Modifier] = None
    system_command: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self):
        data = {
            'type': self.type,
        }
        if self.type == 'joint_command':
            data.update({
                'side': self.side,
                'joint': self.joint,
                'axis': self.axis,
                'value': self.value,
            })
            if self.modifiers:
                data['modifiers'] = self.modifiers.to_dict()
        elif self.type == 'system':
            data['command'] = self.system_command
        if self.error:
            data['error'] = self.error
        return data


# ============================================================================
# JOINT INVENTORY & CONSTRAINTS
# ============================================================================

JOINT_INVENTORY = {
    # Bilateral limbs (Left/Right)
    "shld": {
        "name": "Shoulder",
        "dof": 3,
        "axes": {
            "x": {"name": "Abduction", "range": (0, 180)},
            "y": {"name": "Flexion", "range": (0, 180)},
            "z": {"name": "Internal/External Rotation", "range": (-90, 90)},
        },
        "bilateral": True,
    },
    "elb": {
        "name": "Elbow",
        "dof": 1,
        "axes": {
            "z": {"name": "Flexion", "range": (0, 145)},
        },
        "bilateral": True,
    },
    "wrist": {
        "name": "Wrist",
        "dof": 2,
        "axes": {
            "x": {"name": "Flexion/Extension", "range": (-80, 80)},
            "y": {"name": "Radial/Ulnar Deviation", "range": (-30, 30)},
        },
        "bilateral": True,
    },
    "hip": {
        "name": "Hip",
        "dof": 3,
        "axes": {
            "x": {"name": "Abduction", "range": (-45, 45)},
            "y": {"name": "Flexion", "range": (0, 120)},
            "z": {"name": "Internal/External Rotation", "range": (-45, 45)},
        },
        "bilateral": True,
    },
    "knee": {
        "name": "Knee",
        "dof": 1,
        "axes": {
            "z": {"name": "Flexion", "range": (0, 135)},
        },
        "bilateral": True,
    },
    "ankle": {
        "name": "Ankle",
        "dof": 2,
        "axes": {
            "x": {"name": "Dorsiflexion/Plantarflexion", "range": (-50, 50)},
            "y": {"name": "Inversion/Eversion", "range": (-25, 25)},
        },
        "bilateral": True,
    },
    # Midline joints (singular)
    "head": {
        "name": "Head/Neck",
        "dof": 3,
        "axes": {
            "x": {"name": "Pitch (Flexion)", "range": (-45, 45)},
            "y": {"name": "Yaw (Rotation)", "range": (-60, 60)},
            "z": {"name": "Roll (Lateral)", "range": (-30, 30)},
        },
        "bilateral": False,
    },
    "spine": {
        "name": "Thoracic/Lumbar Spine",
        "dof": 3,
        "axes": {
            "x": {"name": "Flexion", "range": (-45, 45)},
            "y": {"name": "Rotation", "range": (-45, 45)},
            "z": {"name": "Lateral Flexion", "range": (-25, 25)},
        },
        "bilateral": False,
    },
}

VALID_SIDES = {"L", "R", ""}
VALID_AXES = {"x", "y", "z"}
VALID_EASING = {
    "linear", "ease-in", "ease-out", "ease-in-out",
    "sine", "quad", "cubic"
}
SYSTEM_COMMANDS = {"RESET", "CHECK", "EXPORT", "IMPORT"}


# ============================================================================
# PARSER
# ============================================================================

class KSCParser:
    """Parse and tokenize KSC command strings."""

    def __init__(self):
        self.last_error = None

    def parse(self, command_string: str) -> KSCCommand:
        """
        Parse a KSC command string into a structured command object.

        Args:
            command_string: Raw KSC string (e.g., "@30f L-elb-z-090")

        Returns:
            KSCCommand object with parsed data or error
        """
        command_string = command_string.strip()
        if not command_string:
            return KSCCommand(
                type="error",
                error="Empty command string"
            )

        # Extract comment
        comment = None
        if '#' in command_string:
            command_string, comment = command_string.split('#', 1)
            command_string = command_string.strip()
            comment = comment.strip()

        # Extract modifiers and main command
        tokens = command_string.split()
        modifiers = Modifier(comment=comment)
        main_command = None

        for token in tokens:
            if token.startswith('@'):
                modifiers.duration = self._parse_duration(token)
            elif token.startswith('~'):
                modifiers.easing = self._parse_easing(token)
            elif token == '!':
                modifiers.force_override = True
            elif token == '?':
                modifiers.query_mode = True
            else:
                main_command = token

        if not main_command:
            return KSCCommand(
                type="error",
                error="No command found"
            )

        # Check for system commands
        if main_command.upper() in SYSTEM_COMMANDS:
            return KSCCommand(
                type="system",
                system_command=main_command.upper(),
                modifiers=modifiers
            )

        # Parse joint command
        return self._parse_joint_command(main_command, modifiers)

    def _parse_duration(self, token: str) -> Dict[str, str]:
        """Parse @<number><unit> duration modifier."""
        match = re.match(r'^@(\d+)(f|ms|s)$', token)
        if match:
            return {"value": match.group(1), "unit": match.group(2)}
        return None

    def _parse_easing(self, token: str) -> Optional[str]:
        """Parse ~<easing_function> modifier."""
        easing = token[1:].lower()
        if easing in VALID_EASING:
            return easing
        return None

    def _parse_joint_command(self, command: str, modifiers: Modifier) -> KSCCommand:
        """Parse [SIDE]-[JOINT]-[AXIS]-[VALUE] format."""
        parts = command.split('-')

        # Handle both 3-part (midline) and 4-part (bilateral) commands
        if len(parts) == 3:
            side, joint, axis, value = "", parts[0], parts[1], parts[2]
        elif len(parts) == 4:
            side, joint, axis, value = parts[0], parts[1], parts[2], parts[3]
        else:
            return KSCCommand(
                type="joint_command",
                error=f"Invalid KSC syntax: expected [SIDE]-[JOINT]-[AXIS]-[VALUE] or [JOINT]-[AXIS]-[VALUE], got '{command}'"
            )

        # Validate components
        if side and side not in VALID_SIDES:
            return KSCCommand(
                type="joint_command",
                error=f"Invalid side: '{side}' (expected L, R, or empty)"
            )

        if joint not in JOINT_INVENTORY:
            return KSCCommand(
                type="joint_command",
                error=f"Unknown joint: '{joint}'"
            )

        if axis not in VALID_AXES:
            return KSCCommand(
                type="joint_command",
                error=f"Invalid axis: '{axis}' (expected x, y, or z)"
            )

        try:
            value_int = int(value)
            if value_int < 0 or value_int > 360:
                return KSCCommand(
                    type="joint_command",
                    error=f"Value out of range: {value_int} (expected 0-360)"
                )
        except ValueError:
            return KSCCommand(
                type="joint_command",
                error=f"Invalid value: '{value}' (expected integer 0-360)"
            )

        return KSCCommand(
            type="joint_command",
            side=side,
            joint=joint,
            axis=axis,
            value=value_int,
            modifiers=modifiers if any(asdict(modifiers).values()) else None
        )


# ============================================================================
# VALIDATOR
# ============================================================================

class KSCValidator:
    """Validate KSC commands against biomechanical constraints."""

    def check_constraints(self, command: KSCCommand) -> Dict:
        """
        Validate a parsed KSC command.

        Returns:
            {
                'level': ErrorLevel,
                'valid': bool,
                'message': str,
                'warnings': [list of strings]
            }
        """
        if command.type != "joint_command":
            return {
                'level': ErrorLevel.OK,
                'valid': True,
                'message': 'System command (no constraints)',
                'warnings': []
            }

        if command.error:
            return {
                'level': ErrorLevel.ERROR,
                'valid': False,
                'message': command.error,
                'warnings': []
            }

        warnings = []

        # Check 1: Bilateral joint with side
        if command.side and not JOINT_INVENTORY[command.joint]['bilateral']:
            return {
                'level': ErrorLevel.ERROR,
                'valid': False,
                'message': f"Joint '{command.joint}' is not bilateral (remove side prefix)",
                'warnings': []
            }

        # Check 2: Midline joint without side
        if not command.side and not JOINT_INVENTORY[command.joint]['bilateral']:
            pass  # Valid
        elif command.side and JOINT_INVENTORY[command.joint]['bilateral']:
            pass  # Valid
        else:
            return {
                'level': ErrorLevel.ERROR,
                'valid': False,
                'message': f"Side mismatch for joint '{command.joint}'",
                'warnings': []
            }

        # Check 3: Valid axis for joint
        joint_data = JOINT_INVENTORY[command.joint]
        if command.axis not in joint_data['axes']:
            return {
                'level': ErrorLevel.ERROR,
                'valid': False,
                'message': f"Joint '{command.joint}' does not support axis '{command.axis}'. Valid axes: {list(joint_data['axes'].keys())}",
                'warnings': []
            }

        # Check 4: Value range
        axis_range = joint_data['axes'][command.axis]['range']
        min_val, max_val = axis_range

        if command.value < min_val or command.value > max_val:
            if command.modifiers and command.modifiers.force_override:
                warnings.append(f"⚠ Force override: Value {command.value} exceeds typical range {axis_range}")
            else:
                return {
                    'level': ErrorLevel.WARNING,
                    'valid': False,
                    'message': f"Value {command.value} out of biomechanical range {axis_range} for {command.joint} axis {command.axis}",
                    'warnings': warnings
                }

        return {
            'level': ErrorLevel.OK,
            'valid': True,
            'message': 'Valid command',
            'warnings': warnings
        }


# ============================================================================
# VISUALIZATION
# ============================================================================

class KSCVisualizer:
    """ASCII skeleton visualization."""

    @staticmethod
    def render_skeleton() -> str:
        """Render a simple ASCII skeleton in T-pose."""
        return """
        T-POSE (Baseline Skeleton)
        
               [HEAD]
                  |
         [L-SHLD]-[SPINE]-[R-SHLD]
            |       |         |
         [L-ELB] [WAIST] [R-ELB]
            |       |         |
        [L-WRIST] | [R-WRIST]
                  |
           [L-HIP]-+-[R-HIP]
            |             |
         [L-KNEE]    [R-KNEE]
            |             |
        [L-ANKLE]   [R-ANKLE]
        """

    @staticmethod
    def render_pose(commands: List[KSCCommand]) -> str:
        """Render pose from parsed commands (simplified)."""
        output = "Parsed Pose Commands:\n"
        for cmd in commands:
            if cmd.type == "joint_command" and not cmd.error:
                output += f"  {cmd.side}-{cmd.joint}-{cmd.axis}: {cmd.value}°\n"
        return output


# ============================================================================
# EXPORT / IMPORT
# ============================================================================

def ksc_to_json(command: KSCCommand, pretty: bool = True) -> str:
    """Export parsed KSC command to JSON."""
    data = command.to_dict()
    return json.dumps(data, indent=2 if pretty else None)


def json_to_ksc(json_str: str) -> KSCCommand:
    """Import JSON back to KSC command."""
    data = json.loads(json_str)
    cmd = KSCCommand(type=data.get('type'))

    if cmd.type == 'joint_command':
        cmd.side = data.get('side', '')
        cmd.joint = data.get('joint')
        cmd.axis = data.get('axis')
        cmd.value = data.get('value')
        if 'modifiers' in data:
            mod_data = data['modifiers']
            cmd.modifiers = Modifier(
                duration=mod_data.get('duration'),
                easing=mod_data.get('easing'),
                force_override=mod_data.get('force_override', False),
                query_mode=mod_data.get('query_mode', False),
                comment=mod_data.get('comment'),
            )
    elif cmd.type == 'system':
        cmd.system_command = data.get('command')

    return cmd


# ============================================================================
# MAIN / TESTS
# ============================================================================

def run_tests():
    """Run built-in test suite."""
    print("=" * 70)
    print("KINEMATIC SYNTAX CODE (KSC) — TEST SUITE")
    print("=" * 70)
    print()

    parser = KSCParser()
    validator = KSCValidator()

    test_cases = [
        # Valid commands
        ("L-elb-z-090", "Valid: left elbow flexion"),
        ("R-shld-y-180", "Valid: right shoulder overhead"),
        ("head-y-045", "Valid: head rotation"),
        ("spine-x-045", "Valid: spine flexion"),
        ("@30f L-shld-y-090", "Valid: with duration modifier"),
        ("@500ms ~ease-in R-hip-y-090", "Valid: with duration and easing"),
        ("L-ankle-x-050?", "Valid: query mode"),
        ("!L-hip-x-090", "Valid: force override"),
        ("RESET", "Valid: system command"),

        # Invalid commands
        ("L-elb-x-090", "Invalid: elbow doesn't support x-axis"),
        ("invalid-joint-z-090", "Invalid: unknown joint"),
        ("L-shld-w-090", "Invalid: invalid axis"),
        ("L-shld-y-400", "Invalid: value out of range"),
        ("head-y-000", "Valid midline: head yaw"),
        ("L-head-y-045", "Invalid: midline joint with side"),
    ]

    for i, (ksc_str, description) in enumerate(test_cases, 1):
        print(f"Test {i}: {description}")
        print(f"  Input: {ksc_str}")

        cmd = parser.parse(ksc_str)
        validation = validator.check_constraints(cmd)

        print(f"  Parsed: {cmd.type} | Joint: {cmd.joint} | Value: {cmd.value}")
        print(f"  Validation: {validation['level'].value.upper()} - {validation['message']}")

        if validation['warnings']:
            print(f"  Warnings: {', '.join(validation['warnings'])}")

        print()

    print("=" * 70)
    print("SKELETON VISUALIZATION")
    print("=" * 70)
    print(KSCVisualizer.render_skeleton())

    print("\n" + "=" * 70)
    print("JSON EXPORT EXAMPLE")
    print("=" * 70)
    cmd = parser.parse("@1000ms ~ease-in-out L-shld-y-090")
    print(ksc_to_json(cmd))


if __name__ == "__main__":
    run_tests()
