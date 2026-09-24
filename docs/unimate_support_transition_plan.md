# Pilgrim: biped → quadruped → biped feasibility

Target: a recognizable upright walking phrase, transition into four-limb walking, then a separately generated return to upright walking. Keep the existing blockout and model weights. Preserve raw output and explicitly label any chosen boundary poses and cleanup. This extends the UniMate bring-up after the naming experiment; it does not assume that the failed seven-second text expansion now works.

1. Test the existing upright Pilgrim geometry with explicit biped, four-leg and hands/feet crawling prompts. Use arms/legs and front/hind labels with matched per-case noise across name variants, three seeds each: 18 two-second raw clips. Reuse the existing `p07/9400` walk as a prior baseline.
2. Review front and hind effector trajectories for alternating floor approaches and plausible planted intervals. A crouch or an arm swing is insufficient. Measure strict and permissive height/speed candidates, displacement, penetration, and fixed-length integrity. These proxies do not establish load or balance.
3. If a useful four-limb phrase exists, choose boundary context from the generated biped and quadruped phrases. Test short, separately sampled entry and exit transitions with stock known-frame conditioning. Chosen endpoints and spatial alignment are authored assembly decisions; the free interval is model-generated. Verify endpoint agreement, velocity changes and contact states.
4. Assemble only accepted phrases, preserving source-to-final frame mapping. A translating locomotion cycle requires continuous root travel. Repeated preview playback does not qualify as a seamless cycle.
5. If the first raw gate fails, preserve the evidence and evaluate a versioned quadrupedal reference stance before increasing sample count or forcing a full storyboard. Keep segment lengths and topology fixed where possible. Any rest-frame change needs updated consistent conditions, feature interpretation and FK verification; changing a displayed Blender pose alone is insufficient.

No mesh detail, fabric, model training or new weight download is required for this experiment. Large outputs stay on ShareDrive. Do not hide a failed four-support gate by adding an authored gait and calling it generated.

## Probe outcome

[First raw feasibility results](unimate_support_transition_results.md): 18 detailed-prompt samples plus nine short-prompt controls. Ordinary short walking remains recognizable; no quadrupedal phrase was accepted. One permissive contact-screen candidate was rejected visually because it tumbles. Transition assembly is therefore deferred; the versioned reference stance in step 5 has now also been tested. The [18-clip stance comparison](unimate_stance_results.md) changes posture substantially but yields no accepted quadrupedal walk. A lightly constrained short phrase was subsequently tested; see the outcome below. Full transition assembly remains deferred.

## Animal wording and sparse guidance outcome

The [matched animal-wording and sparse-guidance tests](unimate_guided_results.md) are complete: 15 new generations plus three reused controls, 18 reviewed clips. Dog/cat wording affects motion but does not establish a usable four-limb gait. Three support poses are reached accurately; intervening support remains poor and acceleration increases. Root-path guidance authors travel but does not fix contact. Full transition assembly remains deferred. The next diagnostic is the same forward-walk prompts on the existing ordinary quadruped control versus Pilgrim; no training or larger prompt sweep is required.
