# Copyright 2026 The RPent Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Code-policy instructions for yam."""

from collections.abc import Mapping

from robots.yam.prompts import system as system_parts
from rpent.prompt import code_policy as common
from rpent.prompt.utils import PromptNode

CODE_RUNTIME = """
The registered YAM Toolkit is the only robot control surface.
Use Python only to orchestrate registered `robo` methods.
Do not use shell commands, raw network clients, hidden robot APIs,
or direct hardware access to control the robot.

The environment server owns CAN communication, cameras, operator
readiness and success marking. When enabled in the site configuration,
the server checks sampled model link geometry for self/two-arm collisions
and the configured table plane. These checks exclude wrist cameras,
cables, teaching arms, held objects, bags, bowls, and other scene obstacles.
They are not a full collision planner or a guarantee about physical tracking.

Inspect the complete arm and payload path before moving.
Re-observe after every motion. Never bypass safety guards,
clear a latched stop, or fabricate operator readiness.
A cancelled Python cell does not undo physical motion.
"""

CODE_READ_ORDER = """
Before the first robot mutation:
1. Inspect the current robot state using registered observation tools.
2. Inspect the top, left-wrist and right-wrist camera views.
3. Identify the current target, destination, arm roles and
   possible collision risks from fresh observations.

Do not retrieve task memory in Code Policy mode.
Current camera frames and task language are authoritative.
"""

CODE_SUCCESS = """
Only the current environment's eval_success=true confirms
task success. On the real YAM robot, this may require an
operator-confirmed verdict.

A successful Python cell or motion primitive is not proof
of task success. A pending or refused finish is not success.
Never fabricate an operator verdict.

If an operator verdict is required, use only the registered
operator workflow and wait for its authoritative result.

A pending or finish-refused response does not end the session.
Continue through the supported operator workflow until an authoritative
result is available; do not report success from the pending response.
"""

CODE_RECOVERY = """
When observations are ambiguous, pause release and forward motion.
Inspect fresh top and both wrist views, measured pose, grip retention,
and the complete arm and payload path before selecting another action.
Deformation alone proves neither contact nor clearance.

Use a retreat or lift only when current observations and planning support
its complete path. Reversing an earlier path is not automatically safe.
Never push through unknown contact or use VLA to bypass uncertain contact;
VLA may move both arms and release.

For the same local obstacle, try at most three distinct evidence-driven
observation/recovery cycles. Each cycle must identify the hypothesis,
missing evidence, changed approach, and observed result.
Preserve useful partial progress. If no supported recovery exists,
the evidence cannot establish a safe next action, or the local budget
is exhausted, request the specific missing onsite assistance and hold motion.
Do not repeat blind moves or declare task failure merely because a view
is ambiguous.

Feedback faults, latched stops, operator aborts, and nonrecoverable servo
failures require stopping motion and following the supported recovery protocol.
If ready_for_motion is false, follow the registered reset/readiness protocol
and wait for operator readiness before motion. Never fabricate readiness.
An operator abort requires robo.finish(status="failure") immediately.
"""


def system_prompt(
    variables: Mapping[str, object] | None = None,
) -> dict[str, PromptNode]:
    """Assemble code execution rules and YAM operating knowledge."""
    variables = variables or {}

    policy = (
        system_parts.VLA
        if variables.get("vla_enabled", False)
        else system_parts.PRIMITIVES_ONLY
    )

    return {
        **common.system_prompt(),
        "ROLE": system_parts.ROLE,
        "READ ORDER": CODE_READ_ORDER,
        "RUNTIME AND SAFETY": CODE_RUNTIME,
        "PERCEPTION": system_parts.PERCEPTION,
        "CONTROL": system_parts.CONTROL,
        "POLICY AVAILABILITY": policy,
        "SUCCESS": CODE_SUCCESS,
        "API reference": "{{code_policy_api}}",
        "SAFETY AND RECOVERY": CODE_RECOVERY,
    }
