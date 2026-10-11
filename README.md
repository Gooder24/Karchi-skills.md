# Karchi skills

Osobné skilly pre Clauda. Každý priečinok je jeden skill (`SKILL.md` + jeho súbory).

| Skill | Čo robí |
|-------|---------|
| [`taste`](taste/taste.md) | Karchiho vkus: vzhľad, ovládanie, výkon, informácie, spôsob práce |

## Claude Code

```sh
git clone https://github.com/Gooder24/Karchi-skills.md ~/.work/karchi-skills
ln -s ~/.work/karchi-skills/taste ~/.claude/skills/taste
```

## Claude na webe (claude.ai) a v desktopovej aplikácii

```sh
cd ~/.work/karchi-skills && python3 -m zipfile -c taste.zip taste/
```

Súbor `taste.zip` nahraj v Settings → Capabilities → Skills. Po každej zmene `taste.md` ho treba
zabaliť a nahrať znova, web si repozitár sám nesťahuje.

Bez skillov stačí obsah `taste/taste.md` vložiť do inštrukcií projektu alebo do osobných preferencií.
