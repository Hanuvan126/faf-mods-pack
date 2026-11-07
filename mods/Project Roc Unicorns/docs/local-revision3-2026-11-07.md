# Local revision 3 — DushNai attack pursuit and new Ishal-Thar projectile

DushNai: unit-owned monitor reads only the first explicit Attack order. If its line of fire is
blocked, retains the original queue, sets native weapon max radius to 1 for native attack movement,
and holds aim/fire off in a stable pursuit state. Original max radius is restored when line clears,
command changes/stops, or target dies. No IssueMove/IssueClearCommands and no command rewriting.
Native OnLostTarget was switching the old waiting state back to Idle, re-enabling aim repeatedly.
Both waiting states now retain state on target notifications. Auto-target selection remains separate.
Native path routing and arrival need an in-game check; Lua simulations do not prove engine movement.

GGP2301 rebuilt from scratch: new 0.22-diameter UV sphere, clouded violet material, Unit shader with
low emission; no head glow emitter, brightness animation, point lights or PolyTrail. Non-additive
world-stationary purple mist lives 0.45 s; sparse star specks live 0.35 s. All particles have zero
velocity and acceleration. Old 0.035-second additive glow and fully emissive Seraphim sphere removed.
This removes two plausible sources of the reported flickering/overexposure; actual FAF appearance
still needs verification at the player's bloom/fidelity settings. Range 80, rate 0.6 s, velocity 45
and damage are unchanged. Old active comet effects/textures removed, with ZIP backups.

Files installed into both repository and existing game mod; hashes verified. No GitHub push.
Checks: Lua and BP syntax; state/range restoration and queue preservation in mocked Lua;
projectile triangle winding/indices and sphere size; zero particle velocity; resource paths.
Not tested in a running FAF match. Start a NEW match, order DushNai to attack beyond a ridge,
then Stop and Move, then try a visible target. Check both alternating turret shots and smoke.
