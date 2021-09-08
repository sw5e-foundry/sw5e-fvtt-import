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
];
// let types = [ 'class' ];

let foundry_ids = {};

let allow_delete = false;
let verbose = false;

for (let type of types){
	console.log(type)

	let importer_file = await fetch(`/sw5e-compendiums/${type}.json`);
	let importer_data = await importer_file.json();

	let pack_name = `sw5eImporter-${type}`;
	let pack = await game.packs.get(`world.${pack_name}`);
	if (!pack) pack = await CompendiumCollection.createCompendium({
		entity: `Item`,
		label: pack_name,
		name: pack_name,
		package: `world`,
	});

	let pack_docs = await pack.getDocuments();
	for(let pack_doc of pack_docs){
		let pack_item = pack_doc.data;
		let uid = pack_item.flags.uid;

		let importer_item = null
		if (uid) importer_item = importer_data[uid];
		if (uid && importer_item) {
			if (verbose) console.log(`Should update ${pack_item.name}, foundry_id ${pack_item._id}`);
			// UPDATE
			foundry_ids[uid] = pack_item._id
			importer_data[uid] = null;
		}
		else {
			if (verbose) console.log(`Should delete ${pack_item.name}, foundry_id ${pack_item._id}`);
			if (allow_delete) {
				// DELETE
			}
		}
	}

	let data = []
	for(let uid of Object.keys(importer_data)){
		if (importer_data[uid] == null) continue;
		let importer_item = importer_data[uid][0];
		if (verbose) console.log(`Should create ${importer_item.name}, uid ${uid}`);
		data.push(importer_item)
	}

	items = await Item.createDocuments(data, { pack: `world.${pack_name}` });
	for (let item of items) {
		uid = item.data.flags.uid;
		foundry_id = item.data._id;
		foundry_ids[uid] = foundry_id;
	}
}

console.log(foundry_ids);
