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
		'MartialBlaster'
	],
	'lightweapons': [
		'SimpleLightweapon',
		'MartialLightweapon'
	],
	'vibroweapons': [
		'SimpleVibroweapon',
		'MartialVibroweapon'
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
	// 'modifications': [
	// 	'EnhancedArmorModification',
	// 	'EnhancedBlasterModification',
	// 	'EnhancedClothingModification',
	// 	'EnhancedFocusGeneratorModification',
	// 	'EnhancedItemModification',
	// 	'EnhancedLightweaponModification',
	// 	'EnhancedVibroweaponModification',
	// 	'EnhancedWristpadModification',
	// ],
	'armor': ['Armor'],

	'ammo': ['Ammunition'],
	'explosives': ['Explosive'],

	'implements': ['Tool'],
	'kits': ['Kit'],
	'gamingsets': ['GamingSet'],
	'musicalinstruments': ['MusicalInstrument'],

	'forcepowers': ['ForcePower'],
	'techpowers': ['TechPower'],

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

let foundry_data = {};

let allow_delete = true;
let allow_update = true;
let allow_create = true;
let verbose = false;


// item_types = { 'invocations': ['ClassInvocation'] }
// journal_entry_types = {}
// verbose = true

for (let type of Object.keys(item_types)){
	console.log(`Updating ${type} compendium`);

	let importer_data = null;
	for (let file_name of item_types[type]){
		let file = await fetch(`/sw5e-compendiums/${file_name}.json`);
		let data = await file.json();
		importer_data = {
			...importer_data,
			...data,
		}
	}

	let pack = await game.packs.get(`sw5e.${type}`);
	if (!pack){
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	let was_locked = pack.locked;
	await pack.configure({locked: false})

	let to_delete = [];
	let to_update = [];
	let to_create = [];

	let pack_docs = await pack.getDocuments();
	for(let pack_doc of pack_docs){
		let pack_item = pack_doc.data;
		let uid = pack_item.flags.uid;

		let importer_item = null;
		if (uid) importer_item = importer_data[uid];
		if (uid && importer_item) {
			if (verbose) console.log(`Should update ${pack_item.name}, foundry_id ${pack_item._id}, uid ${uid}`);

			foundry_data[uid] = {
				id: pack_item._id,
				effects: pack_item.effects
			}

			importer_item._id = pack_item._id;
			to_update.push(importer_item);

			importer_data[uid] = null;
		}
		else {
			if (verbose) console.log(`Should delete ${pack_item.name}, foundry_id ${pack_item._id}, uid ${uid}`);
			to_delete.push(pack_item._id);
		}
	}

	for (let uid of Object.keys(importer_data)) {
		if (importer_data[uid] == null) continue;
		let importer_item = importer_data[uid];
		if (verbose) console.log(`Should create ${importer_item.name}, uid ${uid}`);
		to_create.push(importer_item);
	}

	if (allow_delete) await Item.deleteDocuments(to_delete, {pack: `sw5e.${type}`});
	if (allow_update) await Item.updateDocuments(to_update, {pack: `sw5e.${type}`});
	if (allow_create) {
		items = await Item.createDocuments(to_create, { pack: `sw5e.${type}` });
		for (let item of items) {
			uid = item.data.flags.uid;

			foundry_data[uid] = {
				id: item.data._id,
				effects: item.data.effects
			}
		}
	}

	await pack.configure({locked: was_locked});
}

for (let type of Object.keys(journal_entry_types)){
	console.log(`Updating ${type} compendium`);

	let importer_data = null;
	for (let file_name of journal_entry_types[type]){
		let file = await fetch(`/sw5e-compendiums/${file_name}.json`);
		let data = await file.json();
		importer_data = {
			...importer_data,
			...data,
		}
	}

	let pack = await game.packs.get(`sw5e.${type}`);
	if (!pack){
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	let was_locked = pack.locked;
	await pack.configure({locked: false})

	let to_delete = [];
	let to_update = [];
	let to_create = [];

	let pack_docs = await pack.getDocuments();
	for(let pack_doc of pack_docs){
		let pack_entry = pack_doc.data;
		let uid = pack_entry.flags.uid;

		let importer_entry = null;
		if (uid) importer_entry = importer_data[uid];
		if (uid && importer_entry) {
			if (verbose) console.log(`Should update ${pack_entry.name}, foundry_id ${pack_entry._id}`);

			foundry_data[uid] = { id: pack_entry._id };

			importer_entry._id = pack_entry._id;
			to_update.push(importer_entry);

			importer_data[uid] = null;
		}
		else {
			if (verbose) console.log(`Should delete ${pack_entry.name}, foundry_id ${pack_entry._id}`);
			to_delete.push(pack_entry._id);
		}
	}

	for(let uid of Object.keys(importer_data)){
		if (importer_data[uid] == null) continue;
		let importer_entry = importer_data[uid];
		if (verbose) console.log(`Should create ${importer_entry.name}, uid ${uid}`);
		to_create.push(importer_entry);
	}

	if (allow_delete) await JournalEntry.deleteDocuments(to_delete, {pack: `sw5e.${type}`});
	if (allow_update) await JournalEntry.updateDocuments(to_update, {pack: `sw5e.${type}`});
	if (allow_create) {
		entries = await JournalEntry.createDocuments(to_create, { pack: `sw5e.${type}` });
		for (let entry of entries) {
			uid = entry.data.flags.uid;
			foundry_data[uid] = { id: entry.data._id };
		}
	}

	await pack.configure({locked: was_locked});
}


console.log('Foundry Data:');
console.log(foundry_data);
