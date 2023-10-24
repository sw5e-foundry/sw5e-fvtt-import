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

const allow_delete = true;
const allow_update = true;
const allow_create = true;
const verbose = false;

for (const type of Object.keys(item_types)) {
	console.log(`Updating ${type} compendium`);

	let importer_data = null;
	for (const file_name of item_types[type]) {
		const file = await fetch(`/sw5e-compendiums/${file_name}.json`);
		const data = await file.json();
		importer_data = {
			...importer_data,
			...data,
		}
	}

	const pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	const was_locked = pack.locked;
	await pack.configure({locked: false})

	const to_delete = [];
	const to_update = [];
	const to_create = [];

	const pack_docs = await pack.getDocuments();
	for(const pack_doc of pack_docs) {
		const pack_item = pack_doc;
		const uid = pack_item.flags["sw5e-importer"]?.uid ?? pack_item.flags.uid;

		let importer_item = null;
		if (uid) importer_item = importer_data[uid];
		if (uid && importer_item) {
			foundry_data[uid] = {
				id: pack_item._id,
				effects: pack_item.effects
			}

			if (pack_item.flags.uid) importer_item.flags["-=uid"] = null;
			if (pack_item.flags.importer_version) importer_item.flags["-=importer_version"] = null;
			if (pack_item.flags.timestamp) importer_item.flags["-=timestamp"] = null;
			importer_item._id = pack_item._id;
			to_update.push(importer_item);

			importer_data[uid] = null;
		}
		else to_delete.push(pack_item._id);
	}

	for (let uid of Object.keys(importer_data)) {
		if (importer_data[uid] == null) continue;
		const importer_item = importer_data[uid];
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
		for (const item of items) {
			const uid = item.flags["sw5e-importer"]?.uid ?? item.flags.uid;

			foundry_data[uid] = {
				id: item._id,
				effects: item.effects
			}
		}
	}

	await pack.configure({locked: was_locked});
}

for (const type of Object.keys(journal_entry_types)) {
	console.log(`Updating ${type} compendium`);

	let importer_data = null;
	for (const file_name of journal_entry_types[type]) {
		const file = await fetch(`/sw5e-compendiums/${file_name}.json`);
		const data = await file.json();
		importer_data = {
			...importer_data,
			...data,
		}
	}

	const pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	const was_locked = pack.locked;
	await pack.configure({locked: false})

	const to_delete = [];
	const to_update = [];
	const to_create = [];

	const pack_docs = await pack.getDocuments();
	for(const pack_doc of pack_docs) {
		const pack_entry = pack_doc;
		const uid = pack_entry.flags["sw5e-importer"]?.uid ?? pack_entry.flags.uid;

		let importer_entry = null;
		if (uid) importer_entry = importer_data[uid];
		if (uid && importer_entry) {
			foundry_data[uid] = { id: pack_entry._id };

			if (pack_entry.flags.uid) importer_entry.flags["-=uid"] = null;
			if (pack_entry.flags.importer_version) importer_entry.flags["-=importer_version"] = null;
			if (pack_entry.flags.timestamp) importer_entry.flags["-=timestamp"] = null;
			importer_entry._id = pack_entry._id;
			to_update.push(importer_entry);

			importer_data[uid] = null;
		}
		else to_delete.push(pack_entry._id);
	}

	for(const uid of Object.keys(importer_data)) {
		if (importer_data[uid] == null) continue;
		const importer_entry = importer_data[uid];
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
		for (const entry of entries) {
			const uid = entry.flags["sw5e-importer"]?.uid ?? entry.flags.uid;
			foundry_data[uid] = { id: entry._id };
		}
	}

	await pack.configure({locked: was_locked});
}

for (const type of Object.keys(actor_types)) {
	console.log(`Updating ${type} compendium`);

	let importer_data = null;
	for (const file_name of actor_types[type]) {
		const file = await fetch(`/sw5e-compendiums/${file_name}.json`);
		const data = await file.json();
		importer_data = {
			...importer_data,
			...data,
		}
	}

	const pack = await game.packs.get(`sw5e.${type}`);
	if (!pack) {
		console.log(`Compendium pack sw5e.${type} not found`);
		continue;
	}

	const was_locked = pack.locked;
	await pack.configure({locked: false})

	const to_delete = [];
	const to_update = [];
	const to_create = [];

	const pack_docs = await pack.getDocuments();
	for(const pack_doc of pack_docs) {
		const pack_actor = pack_doc;
		const actor_uid = pack_actor.flags["sw5e-importer"]?.uid ?? pack_actor.flags.uid;

		let importer_actor = null;
		if (actor_uid) importer_actor = importer_data[actor_uid];
		if (actor_uid && importer_actor) {
			const foundry_data_items = {};
			for (const importer_item of importer_actor.items) {
				const item_uid = importer_item.flags["sw5e-importer"]?.uid ?? importer_item.flags.uid;
				foundry_data_items[item_uid] = {
					id: importer_item._id,
					effects: importer_item.effects
				};
			}

			const items_to_delete = [];
			for (const pack_item of pack_actor.items) {
				const item_uid = pack_item.flags["sw5e-importer"]?.uid ?? pack_item.flags.uid;
				const foundry_data_item = foundry_data_items[item_uid];
				if (foundry_data_item?.id != pack_item.id) items_to_delete.push(pack_item.id);
			}
			await pack_actor.deleteEmbeddedDocuments("Item", items_to_delete);

			foundry_data[actor_uid] = {
				id: pack_actor._id,
				effects: pack_actor.effects,
				sub_entities: foundry_data_items
			}

			if (pack_actor.flags.uid) importer_actor.flags["-=uid"] = null;
			if (pack_actor.flags.importer_version) importer_actor.flags["-=importer_version"] = null;
			if (pack_actor.flags.timestamp) importer_actor.flags["-=timestamp"] = null;
			importer_actor._id = pack_actor._id;
			to_update.push(importer_actor);

			importer_data[actor_uid] = null;
		}
		else to_delete.push(pack_actor._id);
	}

	for (const actor_uid of Object.keys(importer_data)) {
		if (importer_data[actor_uid] == null) continue;
		const importer_actor = importer_data[actor_uid];
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
		for (const actor of actors) {
			const uid = actor.flags["sw5e-importer"]?.uid ?? actor.flags.uid;

			const items = {};
			for (const item of actor.items) {
				const item_uid = item.flags["sw5e-importer"]?.uid ?? item.flags.uid;
				items[item_uid] = {
					id: item.id,
					effects: item.effects
				};
			}

			foundry_data[uid] = {
				id: actor._id,
				effects: actor.effects,
				sub_entities: items
			}
		}
	}

	await pack.configure({locked: was_locked});
}


console.log('Foundry Data:');
console.log(foundry_data);
