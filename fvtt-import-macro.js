let types = {
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
	'armor': ['Armor'],

	'ammo': ['Ammunition'],
	'explosives': ['Explosive'],

	'implements': ['Tool'],
	'kits': ['Kit'],
	'gamingsets': ['GamingSet'],
	'musicalinstruments': ['MusicalInstrument'],

	'archetypes': ['Archetype'],
	'archetypefeatures': ['ArchetypeFeature'],

	'classes': ['Class'],
	'classfeatures': ['ClassFeature'],

	'species': ['Species'],
	'speciesfeatures': ['SpeciesFeature'],

	'feats': ['Feat']
}
// types = {
// 	'classes': ['Class']
// }

let foundry_ids = {};
let foundry_effects = {};

let allow_delete = true;
let allow_update = true;
let allow_create = true;
let verbose = false;

for (let type of Object.keys(types)){
	console.log(`Updating ${type} compendium`)

	let importer_data = null;
	for (let file_name of types[type]){
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

		let importer_item = null
		if (uid) importer_item = importer_data[uid];
		if (uid && importer_item) {
			if (verbose) console.log(`Should update ${pack_item.name}, foundry_id ${pack_item._id}`);

			foundry_ids[uid] = pack_item._id
			foundry_effects[uid] = pack_item.effects

			importer_item._id = pack_item._id
			to_update.push(importer_item)

			importer_data[uid] = null;
		}
		else {
			if (verbose) console.log(`Should delete ${pack_item.name}, foundry_id ${pack_item._id}`);
			to_delete.push(pack_item._id)
		}
	}

	for(let uid of Object.keys(importer_data)){
		if (importer_data[uid] == null) continue;
		let importer_item = importer_data[uid];
		if (verbose) console.log(`Should create ${importer_item.name}, uid ${uid}`);
		to_create.push(importer_item)
	}

	if (allow_delete) await Item.deleteDocuments(to_delete, {pack: `sw5e.${type}`});
	if (allow_update) await Item.updateDocuments(to_update, {pack: `sw5e.${type}`});
	if (allow_create) {
		items = await Item.createDocuments(to_create, { pack: `sw5e.${type}` });
		for (let item of items) {
			uid = item.data.flags.uid;
			foundry_id = item.data._id;
			foundry_ids[uid] = foundry_id;
			foundry_effects[uid] = item.data.effects;
		}
	}

	await pack.configure({locked: was_locked})
}

console.log('Foundry IDs:')
console.log(foundry_ids);
console.log('Foundry Effects:')
console.log(foundry_effects);
