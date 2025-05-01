# C9 R3M/R3CM Importer for Blender

Blender plugin for importing static mesh formats `.r3m` and `.r3cm` from the MMORPG **Continent of the Ninth (C9)**.

## Features

- Import `.r3m` and `.r3cm` model files
- Mesh reconstruction with UVs and normals
- Automatic material and texture assignment
- Batch import support
- Adjustable scaling and mesh combining
- Support for specular and normal maps (`_sp`, `_n` suffix)

## Requirements

- Blender 3.6+
- Game model and texture files extracted from C9

## Installation

1. Download the repository or install via `.zip`
2. Open Blender → `Edit > Preferences > Add-ons > Install`
3. Select the downloaded `.zip` and enable the addon
4. Configure paths (R3M folder, texture folder) in add-on settings

## Usage

Go to:

- File > Import > C9 Formats > Import R3CM (.r3cm)
- File > Import > C9 Formats > Import R3M (.r3m)


Adjust import options like:

- Scale factor
- Combine meshes toggle

Textures will be auto-loaded from the specified texture directory.

## Disclaimer

This tool is for educational and archival purposes. All trademarks belong to their respective owners.

## Author

Developed by [Trolll67](https://github.com/Trolll67)  
License: GNU GPL v3