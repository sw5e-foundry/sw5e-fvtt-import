let item_types = {
	'adventuringgear': [
		'Medical',
		'Clothing',
		'Utility',
		'DataRecordingAndStorage',
		'Storage',
		'Communications',
		'LifeSupport',
		'WeaponOrArmorAccessory',
	],
	'consumables': [
		'AlcoholicBeverage',
		'Spice',
	],
	'blasters': [
		'SimpleBlaster',
		'MartialBlaster',
		'ExoticBlaster',
	],
	'lightweapons': [
		'SimpleLightweapon',
		'MartialLightweapon',
		'ExoticLightweapon',
	],
	'vibroweapons': [
		'SimpleVibroweapon',
		'MartialVibroweapon',
		'Natural',
		'ExoticVibroweapon',
	],
	'enhanceditems': [
		'EnhancedAdventuringGear',
		'EnhancedArmor',
		'EnhancedConsumable',
		'EnhancedFocus',
		'EnhancedShield',
		// 'EnhancedShipArmor',
		// 'EnhancedShipShield',
		// 'EnhancedShipWeapon',
		'EnhancedWeapon',
	],
	'modifications': [
		'EnhancedItemModification',
		'EnhancedCyberneticAugmentation',
		'EnhancedDroidCustomization',
	],
	'armor': ['Armor'],

	'ammo': ['Ammunition'],
	'explosives': ['Explosive'],

	'implements': ['Tool'],
	'kits': ['Kit'],
	'gamingsets': ['GamingSet'],
	'musicalinstruments': ['MusicalInstrument'],

	'forcepowers': ['ForcePower'],
	'techpowers': ['TechPower'],
	'maneuvers': ['Maneuver'],

	'archetypes': ['Archetype'],
	'archetypefeatures': ['ArchetypeFeature'],

	'classes': ['Class'],
	'classfeatures': ['ClassFeature'],
	'invocations': ['ClassInvocation'],

	'species': ['Species'],
	'speciesfeatures': ['SpeciesFeature'],

	'backgrounds': ['Background'],

	'feats': [
		'Feat',
		'ClassImprovement',
		'MulticlassImprovement',
		'SplashclassImprovement',
		'WeaponFocus',
		'WeaponSupremacy',
	],
	'fightingstyles': ['FightingStyle'],
	'fightingmasteries': ['FightingMastery'],
	'lightsaberforms': ['LightsaberForm'],
}

let journal_entry_types = {
	'weaponproperties': ['WeaponProperty'],
	'armorproperties': ['ArmorProperty'],
	'conditions': ['Conditions']
}

let actor_types = {
	'monsters_temp': ['Monster']
}

// item_types = {};
// journal_entry_types = {};

const foundry_data = {};

for (const type of Object.keys(item_types)) {
	console.log(`Extracting from ${type} compendium`);

	const pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	const pack_docs = await pack.getDocuments();
	for(const pack_doc of pack_docs) {
		const pack_item = pack_doc;
		const uid = pack_item.flags["sw5e-importer"]?.uid ?? pack_item.flags.uid;

		if (uid) {
			foundry_data[uid] = {
				id: pack_item._id,
				effects: pack_item.effects
			}
		}
	}
}

for (const type of Object.keys(journal_entry_types)) {
	console.log(`Extracting from ${type} compendium`);

	const pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	const pack_docs = await pack.getDocuments();
	for(const pack_doc of pack_docs) {
		const pack_entry = pack_doc;
		const uid = pack_entry.flags["sw5e-importer"]?.uid ?? pack_entry.flags.uid;

		if (uid) {
			foundry_data[uid] = { id: pack_entry._id };
		}
	}
}

for (const type of Object.keys(actor_types)) {
	console.log(`Extracting from ${type} compendium`);

	const pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	const pack_docs = await pack.getDocuments();
	for(const pack_doc of pack_docs) {
		const pack_actor = pack_doc;
		const actor_uid = pack_actor.flags["sw5e-importer"]?.uid ?? pack_actor.flags.uid;

		if (actor_uid) {
			const foundry_data_items = {};
			for (const pack_item of pack_actor.items) {
				const item_uid = pack_item.flags["sw5e-importer"]?.uid ?? pack_item.flags.uid;
				foundry_data_items[item_uid] = {
					id: pack_item._id,
					effects: pack_item.effects
				};
			}

			foundry_data[actor_uid] = {
				id: pack_actor._id,
				effects: pack_actor.effects,
				sub_entities: foundry_data_items
			}
		}
	}
}


console.log('Foundry Data:');
console.log(foundry_data);
