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

let allow_delete = true;
let allow_update = true;
let allow_create = true;
let verbose = false;

for (let type of Object.keys(item_types)) {
	console.log(`Updating ${type} compendium`);

	let importer_data = null;
	for (let file_name of item_types[type]) {
		let file = await fetch(`/sw5e-compendiums/${file_name}.json`);
		let data = await file.json();
		importer_data = {
			...importer_data,
			...data,
		}
	}

	let pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	let was_locked = pack.locked;
	await pack.configure({locked: false})

	let to_delete = [];
	let to_update = [];
	let to_create = [];

	let pack_docs = await pack.getDocuments();
	for(let pack_doc of pack_docs) {
		let pack_item = pack_doc.data;
		let uid = pack_item.flags.uid;

		let importer_item = null;
		if (uid) importer_item = importer_data[uid];
		if (uid && importer_item) {
			foundry_data[uid] = {
				id: pack_item._id,
				effects: pack_item.effects
			}

			importer_item._id = pack_item._id;
			to_update.push(importer_item);

			importer_data[uid] = null;
		}
		else to_delete.push(pack_item._id);
	}

	for (let uid of Object.keys(importer_data)) {
		if (importer_data[uid] == null) continue;
		let importer_item = importer_data[uid];
		to_create.push(importer_item);
	}

	if (verbose) {
		console.debug(`to_delete: ${to_delete}`);
		console.debug(`to_update: ${to_update}`);
		console.debug(`to_create: ${to_create}`);
	}

	if (allow_delete) await Item.deleteDocuments(to_delete, {pack: `sw5e.${type}`});
	if (allow_update) await Item.updateDocuments(to_update, {pack: `sw5e.${type}`});
	if (allow_create) {
		const items = await Item.createDocuments(to_create, { pack: `sw5e.${type}` });
		for (let item of items) {
			const uid = item.data.flags.uid;

			foundry_data[uid] = {
				id: item.data._id,
				effects: item.data.effects
			}
		}
	}

	await pack.configure({locked: was_locked});
}

for (let type of Object.keys(journal_entry_types)) {
	console.log(`Updating ${type} compendium`);

	let importer_data = null;
	for (let file_name of journal_entry_types[type]) {
		let file = await fetch(`/sw5e-compendiums/${file_name}.json`);
		let data = await file.json();
		importer_data = {
			...importer_data,
			...data,
		}
	}

	let pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	let was_locked = pack.locked;
	await pack.configure({locked: false})

	let to_delete = [];
	let to_update = [];
	let to_create = [];

	let pack_docs = await pack.getDocuments();
	for(let pack_doc of pack_docs) {
		let pack_entry = pack_doc.data;
		let uid = pack_entry.flags.uid;

		let importer_entry = null;
		if (uid) importer_entry = importer_data[uid];
		if (uid && importer_entry) {
			foundry_data[uid] = { id: pack_entry._id };

			importer_entry._id = pack_entry._id;
			to_update.push(importer_entry);

			importer_data[uid] = null;
		}
		else to_delete.push(pack_entry._id);
	}

	for(let uid of Object.keys(importer_data)) {
		if (importer_data[uid] == null) continue;
		let importer_entry = importer_data[uid];
		to_create.push(importer_entry);
	}

	if (verbose) {
		console.debug(`to_delete: ${to_delete}`);
		console.debug(`to_update: ${to_update}`);
		console.debug(`to_create: ${to_create}`);
	}

	if (allow_delete) await JournalEntry.deleteDocuments(to_delete, {pack: `sw5e.${type}`});
	if (allow_update) await JournalEntry.updateDocuments(to_update, {pack: `sw5e.${type}`});
	if (allow_create) {
		const entries = await JournalEntry.createDocuments(to_create, { pack: `sw5e.${type}` });
		for (let entry of entries) {
			const uid = entry.data.flags.uid;
			foundry_data[uid] = { id: entry.data._id };
		}
	}

	await pack.configure({locked: was_locked});
}

for (let type of Object.keys(actor_types)) {
	console.log(`Updating ${type} compendium`);

	let importer_data = null;
	for (let file_name of actor_types[type]) {
		let file = await fetch(`/sw5e-compendiums/${file_name}.json`);
		let data = await file.json();
		importer_data = {
			...importer_data,
			...data,
		}
	}

	let pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	let was_locked = pack.locked;
	await pack.configure({locked: false})

	let to_delete = [];
	let to_update = [];
	let to_create = [];

	let pack_docs = await pack.getDocuments();
	for(let pack_doc of pack_docs) {
		let pack_actor = pack_doc.data;
		let actor_uid = pack_actor.flags.uid;

		let importer_actor = null;
		if (actor_uid) importer_actor = importer_data[actor_uid];
		if (actor_uid && importer_actor) {
			let foundry_data_items = {};
			for (let importer_item of importer_actor.items) {
				foundry_data_items[importer_item.flags.uid] = {
					id: importer_item._id,
					effects: importer_item.effects
				};
			}

			let items_to_delete = [];
			for (let pack_item of pack_actor.items) {
				let item_uid = pack_item.data.flags.uid;
				let foundry_data_item = foundry_data_items[item_uid];
				if (foundry_data_item?.id != pack_item.id) items_to_delete.push(pack_item.id);
			}
			await pack_actor.document.deleteEmbeddedDocuments("Item", items_to_delete);

			foundry_data[actor_uid] = {
				id: pack_actor._id,
				effects: pack_actor.effects,
				sub_entities: foundry_data_items
			}

			importer_actor._id = pack_actor._id;
			to_update.push(importer_actor);

			importer_data[actor_uid] = null;
		}
		else to_delete.push(pack_actor._id);
	}

	for (let actor_uid of Object.keys(importer_data)) {
		if (importer_data[actor_uid] == null) continue;
		let importer_actor = importer_data[actor_uid];
		to_create.push(importer_actor);
	}

	if (verbose) {
		console.debug(`to_delete: ${to_delete}`);
		console.debug(`to_update: ${to_update}`);
		console.debug(`to_create: ${to_create}`);
	}

	if (allow_delete) await Actor.deleteDocuments(to_delete, {pack: `sw5e.${type}`});
	if (allow_update) await Actor.updateDocuments(to_update, {pack: `sw5e.${type}`});
	if (allow_create) {
		const actors = await Actor.createDocuments(to_create, { pack: `sw5e.${type}` });
		for (let actor of actors) {
			uid = actor.data.flags.uid;

			let items = {};
			for (let item of actor.items) {
				items[item.data.flags.uid] = {
					id: item.id,
					effects: item.effects
				};
			}

			foundry_data[uid] = {
				id: actor.data._id,
				effects: actor.data.effects,
				sub_entities: items
			}
		}
	}

	await pack.configure({locked: was_locked});
}


console.log('Foundry Data:');
console.log(foundry_data);
