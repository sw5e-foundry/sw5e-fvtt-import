# sw5e-fvtt-import
 
Python script made to import sw5e data from the [API](https://sw5eapi.azurewebsites.net/api/equipment) to a FVTT compatible format.

To use, simply run the `main.py` file with python 3.8 or newer. This will generate the .json files in the output folder.
To import those files into foundry itself, copy them to a folder named `sw5e-compendiums` inside your foundry's data folder, add the `fvtt-import-macro.js` as a macro into your world, and run it.

Currently imports:
- Archetypes
- Classes
- Equipments
- Feats
- Features
- Species