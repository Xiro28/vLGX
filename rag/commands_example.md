# EXAMPLES FOR ROBOTIC COMMAND EXTRACTION

## Example 1: Inserting and tightening a screw
Input visual context: The image shows a hand holding a screw (labeled 156384) and inserting it into an angled hole on a chair leg, followed by a rotational arrow indicating tightening.
Extracted Commands:
- robot_command(pick)
- robot_command(move)
- robot_command(insert)
- robot_command(rotate)
- robot_command(release)

## Example 2: Placing a wooden dowel
Input visual context: The image shows a small wooden cylinder being pushed straight into a hole on a flat wooden board.
Extracted Commands:
- robot_command(pick)
- robot_command(move)
- robot_command(insert)
- robot_command(release)

## Example 3: Connecting two large parts
Input visual context: An arrow shows the entire seat of the chair being lowered onto the pre-assembled base with four legs.
Extracted Commands:
- robot_command(pick)
- robot_command(move)
- robot_command(place)
- robot_command(release)

## Rules:
Always break down the visual action into these fundamental steps. The allowed keywords are strictly: move, pick, place, rotate, insert, release.