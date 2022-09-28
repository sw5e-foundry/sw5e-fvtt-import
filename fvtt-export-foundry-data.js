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
		'EnhancedCyberneticAugmentation',
		'EnhancedDroidCustomization',
		'EnhancedFocus',
		'EnhancedShield',
		// 'EnhancedShipArmor',
		// 'EnhancedShipShield',
		// 'EnhancedShipWeapon',
		'EnhancedWeapon',
	],
	'modifications': [
		'EnhancedItemModification',
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
	'lightsaberform': ['LightsaberForm'],
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

let foundry_data = {};

for (let type of Object.keys(item_types)) {
	console.log(`Extracting from ${type} compendium`);

	let pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	let pack_docs = await pack.getDocuments();
	for(let pack_doc of pack_docs) {
		let pack_item = pack_doc.data;
		let uid = pack_item.flags.uid;

		if (uid) {
			foundry_data[uid] = {
				id: pack_item._id,
				effects: pack_item.effects
			}
		}
	}
}

for (let type of Object.keys(journal_entry_types)) {
	console.log(`Extracting from ${type} compendium`);

	let pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	let pack_docs = await pack.getDocuments();
	for(let pack_doc of pack_docs) {
		let pack_entry = pack_doc.data;
		let uid = pack_entry.flags.uid;

		if (uid) {
			foundry_data[uid] = { id: pack_entry._id };
		}
	}
}

for (let type of Object.keys(actor_types)) {
	console.log(`Extracting from ${type} compendium`);

	let pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	let pack_docs = await pack.getDocuments();
	for(let pack_doc of pack_docs) {
		let pack_actor = pack_doc.data;
		let actor_uid = pack_actor.flags.uid;

		if (actor_uid) {
			let foundry_data_items = {};
			for (let itm of pack_actor.items) {
				let pack_item = itm.data;
				foundry_data_items[pack_item.flags.uid] = {
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
