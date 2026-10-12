# Karchi skills

Osobné skilly pre Clauda. Každý priečinok je jeden skill (`SKILL.md` + jeho súbory).

| Skill | Čo robí |
|-------|---------|
| [`taste`](taste/taste.md) | Karchiho vkus: vzhľad, ovládanie, výkon, informácie, spôsob práce |
| [`playwright-cli`](playwright-cli/SKILL.md) | Ovládanie prehliadača príkazom `playwright-cli` |

## Claude Code

```sh
git clone https://github.com/Gooder24/Karchi-skills.md ~/.work/karchi-skills
ln -s ~/.work/karchi-skills/taste ~/.claude/skills/taste
ln -s ~/.work/karchi-skills/playwright-cli ~/.claude/skills/playwright-cli
```

## Claude na webe (claude.ai) a v desktopovej aplikácii

```sh
cd ~/.work/karchi-skills && python3 -m zipfile -c taste.zip taste/
```

Súbor `taste.zip` nahraj v Settings → Capabilities → Skills. Po každej zmene `taste.md` ho treba
zabaliť a nahrať znova, web si repozitár sám nesťahuje.

Bez skillov stačí obsah `taste/taste.md` vložiť do inštrukcií projektu alebo do osobných preferencií.

## playwright-cli

Skill je z [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) (Apache-2.0,
`playwright-cli/LICENSE`), stav `b85c7a7` (v0.1.22). Potrebuje príkaz `playwright-cli`:
`npm install -g @playwright/cli@latest`.
