# Sha’Veyr: low blaster, approved 2026-11-08

Original synthesized A blaster, down 10 semitones without stretching time. Mono PCM16 48 kHz, 0.45 seconds per shot. Source: ../sha-veyr-blaster-low-v2/A_blaster_shot_01.wav. Master gain +1 dB, peak -5.70 dBFS; maximum 100 ms RMS -13.43 dBFS (stock XSL0201 Spectra -11.75 dBFS before cue attenuation). Both use sound volume byte 120 (about -7 dB), category 6, weapon RPC codes 918/1355/1437 from the installed SupCom.xgs. No stock waveform distributed.

Runtime banks: sounds/PRU_ShaVeyr.xsb + .xwb. Unique bank PRU_ShaVeyr; cue ShaVeyr_Blaster. The installed FAF init_faf.lua mounts mod sounds folders automatically; completely restart Forged Alliance after installing. No game installation changes required.

Five single-shot sounds are triggered by the native projectile weapon at offsets 0, .1, .2, .3, .4 seconds. Native salvo time .5 sec + reload 3 sec = next barrel starts at 3.5 sec. RateOfFire=1/3.5. No whole-burst recording or separate audio timer.

Validation: generated bank loaded by native Microsoft XACT 3.0 with the installed game's globals; named cue resolved and prepared; five muted overlapping plays 100 ms apart accepted. CRC16/X25 covers bytes 18 onward. Lua/native weapon harness verifies timings and barrel alternation; installed and working hashes match. Actual in-game mix/listening remains to be checked.

Build scripts retained here for maintenance. They currently use the documented local development paths and audio_tools/sha_veyr_release output under the working directory. Original synthesis scripts are in ../sha-veyr-blaster-low-v2/.

Format/API references: https://github.com/FNA-XNA/FAudio/blob/master/src/FACT_internal.c and https://github.com/wine-mirror/wine/blob/master/include/xact3.h . Native files were used only to verify version, category and global RPC indices. Generated banks contain our original sound only.
