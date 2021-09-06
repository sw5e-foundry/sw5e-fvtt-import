let types = [
    'archetype',
    // // 'armorProperty',
    // 'background',
    'class',
    // // 'conditions',
    // // 'deployment',
    // 'enhancedItem',
    'equipment',
    'feat',
    'feature',
    // 'fightingMastery',
    // 'fightingStyle',
    // 'lightsaberForm',
    // 'monster',
    // 'power',
    // 'referenceTable',
    // // 'skills',
    'species',
    // // 'starshipEquipment',
    // // 'starshipModification',
    // // 'starshipSizes',
    // // 'venture',
    // // 'weaponProperty',
]
for (let type of types){
    let packName = `sw5eImporter-${type}`
    let pack = game.packs.get(`world.${packName}`);
    if (pack) await pack.deleteCompendium();
    await CompendiumCollection.createCompendium({
        entity: `Item`,
        label: packName,
        name: packName,
        package: `world`,
    });
    let file = await fetch(`/sw5e-compendiums/${type}.json`);
    let data = await file.json();
    let items = await Item.createDocuments(data, { pack: `world.${packName}` });
}