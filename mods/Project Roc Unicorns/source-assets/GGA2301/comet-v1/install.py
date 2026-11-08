from pathlib import Path
import shutil,json,hashlib,zipfile,datetime
p=Path(__file__).parent;stage=p/'runtime';mod=p.parents[2]
installed=Path('C:/Users/admin/Documents/My Games/Gas Powered Games/Supreme Commander Forged Alliance/Mods/Project Roc Unicorns')
out=Path('F:/FAF-Development/outputs/IshalThar_Game_Comet_v1');out.mkdir(exist_ok=True)
files=sorted(f for f in stage.rglob('*') if f.is_file())
backup=out/'installed-before-comet.zip'
if not backup.exists():
 with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
  for f in files:
   rel=f.relative_to(stage);old=installed/rel
   if old.exists():z.write(old,str(rel))
manifest=[]
for f in files:
 rel=f.relative_to(stage)
 for dest in [mod,installed]:
  target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
 digest=hashlib.sha256(f.read_bytes()).hexdigest()
 assert hashlib.sha256((installed/rel).read_bytes()).hexdigest()==digest
 manifest.append({'path':rel.as_posix(),'sha256':digest})
with zipfile.ZipFile(out/'IshalThar_comet_patch.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,'Project Roc Unicorns/'+f.relative_to(stage).as_posix())
(out/'installed_manifest.json').write_text(json.dumps(manifest,indent=2))
shutil.copy2(p/'validation.json',out/'validation.json');shutil.copy2(p/'game_mesh_preview.png',out/'game_mesh_preview.png')
text='''# Ishal-Thar — twin comet replacement, local build

Replaces GGA2301 in Project Roc Unicorns. Vael-Itha / GGA2404 is not changed.
Footprint 1x1, SkirtSize 2x2 and offsets -0.5 match stock XSB2301 T2 point defense.
T3 technology, 2000 mass / 17600 energy, 6500 HP and range 60 retained.
New weapon: one shot every 0.3 s, alternating muzzles, velocity 85,
130 damage per shot, 0.35 splash radius, no friendly damage. Initial balance for testing.
Dark metallic model, team-color geometric inlays, fixed white muzzle rings.
Native aiming/recoil; old prism animation references removed. Original files retained in backup.
Stock Seraphim tarmac (Tar6x, 6.4) and own nonblocking reclaimed wreck.
Straight terrain/wall clearance checks, visible/radar-known alternate-target selection,
physical projectile collisions including friendly units/walls. A shot above a low wall is allowed.

Installed by copying ONLY manifest files into the existing mod. Other units untouched.
Start a NEW match to reload blueprint and script changes. Enable Project Roc Unicorns.
Test: build next to stock T2 PD; alternate shots on a visible target; a ridge or tall wall
in the fire line; a second unobstructed enemy; hold fire; kill and reclaim then rebuild.
Lua, geometry, resources and simulated firing/clearance tests passed. Not tested in a running FAF match.
No GitHub publication performed.

Authoritative editable Lua/blueprints are under comet-v1/runtime; build_runtime.py was an initial
scaffold, followed by ready-state recovery and custom wreck corrections. Do not regenerate it blindly.
export_blender.py and pack_assets.py produce geometry/materials; source model is v09.
'''
(p/'README.md').write_text(text);(out/'README.md').write_text(text)
print('INSTALLED_FILES',len(files));print('BACKUP',backup);print('PATCH',out/'IshalThar_comet_patch.zip')
