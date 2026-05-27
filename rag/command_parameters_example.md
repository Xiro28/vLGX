TASK: Extract exact parameters and provide a short visual description.
FORMAT: key: value, description: "short text"
VALID KEYS: object, target, direction, tool

INPUT: Command: pick (picking two long wooden dowels)
OUTPUT: object wooden_dowel_long_1, wooden_dowel_long_2, description "the robotic arm picks up two long wooden dowels from the flat surface"

INPUT: Command: move (moving to the left side panel)
OUTPUT: target side_panel_left_surface, description "the arm moves the dowels towards the pre-drilled holes on the left side panel"

INPUT: Command: insert (attaching the four legs to the four base corners)
OUTPUT: object chair_leg_1, chair_leg_2, chair_leg_3, chair_leg_4, target [base_corner_front_left, base_corner_front_right, base_corner_back_left, base_corner_back_right], description "inserting each of the four chair legs into its corresponding corner hole on the base"

INPUT: Command: insert (putting the screws into the holes)
OUTPUT: object screw_156384_a, target base_hole_front_left, description "inserting the screw into the angled hole of the front left leg"

INPUT: Command: rotate (screwing them all in with a cross screwdriver)
OUTPUT: direction clockwise, tool cross_screwdriver, description "tightening the screw clockwise using a crosshead screwdriver until fully flush"

INPUT: Command: place (putting seat on base)
OUTPUT: object chair_seat, target assembled_base, description "lowering the main chair seat onto the assembled four-leg base"