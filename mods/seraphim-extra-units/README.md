# Seraphim Additional Units

Дополнительные юниты Серафимов для Supreme Commander: Forged Alliance / FAF.
Самостоятельный симуляционный мод с экспериментальными парящими танками.

| Юнит | Название | Назначение |
| --- | --- | --- |
| `GGA0401` | Dush'Nai | Штурмовой танк на воздушной подушке T2 |
| `GGA0404` | Cyclops - Циклоп | Штурмовой шагоход T2 с центральным лучом и ПВО |
| `GGA2302` | Sha'Veyr | Оборонительная башня T3 с двумя кометными пушками |
| `GGA0402` | Itha-Suun | Танк с двумя фазонными пушками, четырьмя зенитками и персональным щитом |
| `GGA0403` | Itha-Vael | Штурмовой танк «Полумесяц» с фазонной пушкой, четырьмя зенитками и персональным щитом |

GGA0401 и GGA0404 доступны инженерам и командирам T2/T3, GGA0402 и GGA0403 — инженерам и командирам T3; GGA2302 строится инженерами и командирами T3.
Их blueprint ID, названия, баланс, модели, текстуры и иконки сохранены.
Артиллерия GGA2404 Vael-Itha возвращена в Seraphim Rework и в этот мод не входит.

## Требования и установка

Нужны Forged Alliance и FAF. Seraphim Rework не требуется. Оба актуальных мода
можно включать вместе: GGA0401/GGA0402/GGA0403/GGA0404/GGA2302 находятся здесь, GGA2301/GGA2404 — в Project Roc Unicorns.

Скопируйте папку `seraphim-extra-units` целиком в каталог `mods` данных FAF,
с `mod_info.lua` в корне. Включите **Seraphim Additional Units** в списке
симуляционных модов перед матчем. Для сетевой игры мод нужен всем участникам.
При обновлении замените прежние установленные папки обоих модов целиком,
чтобы не оставлять перенесённые юниты одновременно в двух модах с одинаковыми ID.
Установленные копии в этой задаче не менялись.

## Ресурсы и совместимость

- `units/GGA0402`, `units/GGA0403` — два танка с самостоятельными ресурсами модели.
- `projectiles/GGP0402`, `projectiles/GGP0402Charge` — общие для этих танков снаряд
  и визуал зарядки. Меш, три карты материалов и эффекты скопированы из проектных
  ресурсов GGA0401; все пути ведут внутрь Additional Units.
- `effects/emitters/gga0402_impact_*` — общие эффекты попадания без дополнительного урона.
- `icons/units` и `textures/ui/common/icons/units` — иконки обоих танков.
- `source-assets/GGA0402` и `source-assets/GGA0403` — исходники, генераторы,
  предпросмотры и исторические версии. Архивные blueprint имеют расширение
  `.bp.txt`, чтобы не загружаться как действующие варианты.

Танки сохраняют категории `EXPERIMENTAL MOBILE LAND DIRECTFIRE` и стандартные
категории строителей. Отдельного хука M28AI в этом моде нет; фактический выбор
юнитов зависит от стратегии ИИ и требует проверки в матче. Хук тактической
артиллерии GGA2404 возвращён в Rework.

## Статус

Ссылки на ресурсы, сохранность бинарных файлов и неизменность игровой логики при
переносе проверены по файлам. После переноса игра не запускалась; загрузка,
строительство, стрельба и поведение ИИ в матче ещё не проверены.

[Itha-Suun: исходники](source-assets/GGA0402/README.md) ·
[Itha-Vael: исходники](source-assets/GGA0403/README.md) ·
[Проверка переноса](docs/MIGRATION.md).

## Перенос Dush’Nai, Cyclops и Sha’Veyr

## T2 hover assault tank

`GGA0401` **Dush'Nai** replaces the original Itha-Yen model with an eight-petal
hover hull and paired floating gondolas. It has reflective dark steel, army-color
ornaments and fixed violet ring lining. Three native SCM LODs share a 33-bone
rig. Its construction icon now depicts this model.

One main gun fires a fast phason sphere with a Seraphim trail at **80 range**, dealing **2,000
damage** with **4 splash radius**, **1-second muzzle charge** and `RateOfFire =
0.3`. Projectile speed is **70**. The four inherited AA weapons and AA metadata are removed. Ground/water
speed remains **3.6**, reverse **2.5**. Durability is **6,000 hull HP** plus a
**14,000 HP personal shield**, regenerating **1,000 HP/s after 5 seconds**.
It costs **4,800 mass / 60,000 energy / 4,000 build points** and is available
to Seraphim T2 and T3 engineers and commanders with the corresponding engineering upgrade.
These balance and T2 availability changes have not yet been tested in a match.

After a shot the gondolas close, electrical links intensify, the original phason
model grows between the rings and the gondolas reopen. A full sphere waits for a
target. A blocked terrain corridor is rejected before the native salvo/clock;
the weapon searches actively known enemies with clear paths using its original
priorities. A path closing during charge cancels discharge and its clock. No
player orders, vision radius or projectile damage behavior are changed.

User checks confirm building, movement, firing, accepted charge animation and
AA removal. Latest blocked-target/progress recovery and the new icon have file
and mocked-state checks, with fresh match verification pending. Source/rebuild
instructions: [approved hover model](source-assets/GGA0401/approved-hover/README.md).


## T2 experimental Cyclops

`GGA0404` **Cyclops - Циклоп** is a Seraphim walking experimental built by T2/T3 engineers and commanders with matching engineering upgrades. It appears only in the T2 construction tab: it retains its experimental description but uses the TECH2 category without EXPERIMENTAL. It costs 4,999 mass, 22,000 energy and 6,000 build time; movement speed is 2.5 and its footprint and construction skirt are 3×3. Initial hull health is provisionally 6,000. Its central surface beam has range 30, 25 damage per simulation tick (nominally 250 per second), five seconds active and a nominal seven-second shot cycle. Each hand carries the stock Uyanah surface and anti-air lightning weapon settings. The imported GLB, converter, animation and previews are in [the source directory](source-assets/GGA0404/README.md). A user reported a freeze and a broken model during construction. The source was rebuilt with 28 bones (the local shader palette has 80) and inline mesh LOD metadata for the Seraphim construction effect. The revised version has not yet been verified in a match; walk, aiming, timing, construction and M28AI selection remain unverified.

`GGA2302` **Sha'Veyr** is a separate T3 twin-comet defense with range 80.
It is buildable by Seraphim T3 engineers and commanders; its projectile,
effects, model and wreck are included. [Details](docs/ShaVeyr-GGA2302.md).


Игровые файлы, ресурсы, исходники и иконки перенесены в этот мод; работа в FAF после переноса ещё не проверена.
