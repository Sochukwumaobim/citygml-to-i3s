# CityGML to I3S Converter

> **The first documented, reproducible open-source workflow for converting 3DCityDB-based CityGML data into Esri I3S Scene Layer Packages (SLPK).**

This tool implements and packages the conversion pipeline developed in the MSc thesis:

> **Ugwu, C. (2026).** *Evaluating Open and Semantic-Aware Workflows for Converting 3DCityDB-Based CityGML to Esri I3S for Interoperable 3D City Models.* MSc Photogrammetry and Geoinformatics, HFT Stuttgart – University of Applied Sciences. Supervised by Prof. Dr. Zhihang Yao and Prof. Dr. Volker Coors.

A paper based on this work has been submitted to the **21st International 3D GeoInfo Conference (GeoSofia 2026)**, Sofia, Bulgaria, September–October 2026.

---

## Overview

[CityGML](https://www.ogc.org/standard/citygml/) is the international OGC standard for semantically rich 3D city models. [I3S (Indexed 3D Scene Layer)](https://www.ogc.org/standard/i3s/) is the OGC community standard for streaming and visualising large-scale 3D geospatial content in the Esri ecosystem and CesiumJS. Despite being complementary standards, no open-source, end-to-end conversion pathway between them existed prior to this work.

This tool bridges that gap using [3D Tiles 1.0](https://github.com/CesiumGS/3d-tiles) as a pragmatic intermediary format, connecting [3DCityDB v5](https://github.com/3dcitydb/3dcitydb) to a functional I3S SLPK output.

```
3DCityDB v5 → citydb-tool → CityGML → citygml-to-3dtiles → 3D Tiles 1.0 → tile-converter → I3S SLPK
```

---

## Key Findings (from empirical evaluation)

The thesis tested two conversion architectures across four datasets. The empirical results establish clear guidance for practitioners:

### The Four Thresholds Framework

| Threshold | Recommended ✅ | Caution ⚠️ | Not Suitable ❌ |
|-----------|---------------|-----------|----------------|
| **LOD Complexity** | LOD1–2 | LOD3 (windows visible but unlabelled) | LOD4 (anonymous interiors) |
| **Schema** | AAA® (100%), Planning Extension (~75%) | Core CityGML (6–9%) | EnergyADE (0%), surface/interior schemas |
| **Geometry Type** | Polygon / MultiSurface | Solid (LOD2 only) | LineString, Curve, Point *(silent failure)* |
| **Viewer Platform** | I3S Explorer / CesiumJS | ArcGIS Pro (partial) | ArcGIS Online (no display) |

### Performance benchmarks

- **2,571 buildings** processed in **58 seconds** (0.023 s/building)
- **91% file size reduction**: 52 MB CityGML → 4.6 MB SLPK
- Compression efficiency scales with dataset complexity (20%–91%)

### Important limitations to be aware of

- **Non-polygonal geometry is silently dropped** (38–62% data loss for affected datasets) — no warning is currently issued by the underlying tools
- **Surface-level and interior semantics are completely lost** (0% retention) — termed *semantic annihilation* in the thesis
- **Textures are not supported** — all geometry renders in uniform default colour
- **3D Tiles 1.1 pathway does not work** with tile-converter v3.2.6 — use 3D Tiles 1.0 only

---

## Prerequisites

- [Docker Engine](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/) 2.0+
- 8 GB+ RAM recommended
- 20 GB+ free disk space
- A running or accessible **3DCityDB v5** instance with your CityGML data imported

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Sochukwumaobim/citygml-to-i3s.git
cd citygml-to-i3s
```

### 2. Configure your environment

Copy the example environment file and fill in your database connection details:

```bash
cp .env.example .env
```

Edit `.env` with your 3DCityDB connection parameters:

```env
CITYDB_HOST=localhost
CITYDB_PORT=5432
CITYDB_NAME=your_database_name
CITYDB_USER=your_username
CITYDB_PASSWORD=your_password
CITYDB_SCHEMA=citydb
OUTPUT_NAME=my_output
```

> ⚠️ **Never commit your `.env` file to version control.** It is listed in `.gitignore`.

### 3. Place your CityGML input

Copy your CityGML file(s) into the `input/` directory:

```bash
cp /path/to/your/model.gml input/
```

### 4. Run the conversion

```bash
docker-compose up
```

The workflow will:
1. Export CityGML from your 3DCityDB instance using `citydb-tool`
2. Convert to 3D Tiles 1.0 using `citygml-to-3dtiles`
3. Convert to I3S SLPK using `tile-converter` (v3.2.6)
4. Write the final `.slpk` file to the `output/` directory

### 5. View your output

Open the `.slpk` file in:
- **[I3S Explorer](https://i3s.esri.com/i3s-explorer)** (recommended — full support)
- **ArcGIS Pro 3.x** (partial support; avoid district-scale datasets)
- **CesiumJS** (via I3S layer loading)

---

## Verified Toolchain

This workflow was verified with the following specific versions. **Do not substitute without testing** — version mismatches are the primary cause of silent failures.

| Tool | Version | Role |
|------|---------|------|
| 3DCityDB | 5.3.0 | Source database |
| citydb-tool | 1.1.0 | CityGML export |
| citygml-to-3dtiles | 0.6.2 | 3D Tiles 1.0 generation |
| @loaders.gl/tile-converter | **3.2.6** | I3S SLPK generation |
| PostgreSQL | 15 | Database backend |
| PostGIS | 3.4 | Spatial extensions |
| Node.js | 16.20.2 | Runtime for tile-converter |

> **Critical:** tile-converter v3.2.6 supports 3D Tiles 1.0 only. The 3D Tiles 1.1 pathway (via PG2B3DM) produces structurally valid but unrenderable SLPK output due to specification incompatibility. Use the file-based 3D Tiles 1.0 pathway.

---

## Repository Structure

```
citygml-to-i3s/
├── config/              # Configuration templates
├── scripts/             # Python orchestration and export scripts
├── logs/                # Conversion logs (generated at runtime)
├── output/              # SLPK output (generated at runtime)
├── Dockerfile           # Container definition
├── docker-compose.yml   # Service orchestration
├── entrypoint.sh        # Container entry point
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Docker Hub

A pre-built image is available on Docker Hub:

```bash
docker pull sochuma/citygml-to-i3s
```

[→ View on Docker Hub](https://hub.docker.com/r/sochuma/citygml-to-i3s)

---

## Academic Context

This tool is the practical output of research that identified and filled a documented gap in the open-source geospatial ecosystem. Prior to this work, the only available pathway for CityGML-to-I3S conversion required proprietary tools (Esri's FME-based Data Interoperability extension).

The research introduced several concepts now used in the field:

- **Semantic annihilation** — the complete, systematic elimination of all semantic attributes below the building feature level during conversion
- **Loss vs. absence distinction** — a methodological framework distinguishing converter failure (attribute present in source, absent in output) from source limitation (attribute never present)
- **Four Thresholds Framework** — empirically-derived decision guidance for practitioners evaluating conversion suitability

The thesis findings directly informed subsequent development of a prototype demonstrating direct I3S export from 3DCityDB v5 at scale, rendering 9.7 million LOD2 buildings from Open Bayern on CesiumJS (acknowledged by Prof. Dr. Zhihang Yao, HFT Stuttgart, 2026).

---

## Citation

If you use this tool or the findings from the associated thesis in your work, please cite:

```bibtex
@mastersthesis{ugwu2026citygml,
  author    = {Ugwu, Chukwuma},
  title     = {Evaluating Open and Semantic-Aware Workflows for Converting
               3DCityDB-Based CityGML to Esri I3S for Interoperable 3D City Models},
  school    = {HFT Stuttgart -- University of Applied Sciences},
  year      = {2026},
  month     = {February},
  type      = {MSc Thesis},
  note      = {M.Sc. Photogrammetry and Geoinformatics.
               Supervisors: Prof. Dr. Zhihang Yao, Prof. Dr. Volker Coors}
}
```

A conference paper based on this work is under review:

> Ugwu, C. and Yao, Z. (2026). From CityGML to I3S: An empirical evaluation of open-source conversion workflows for interoperable 3D city models. *21st International 3D GeoInfo Conference (GeoSofia 2026)*, Sofia, Bulgaria.

---

## Known Issues and Roadmap

### Current known issues
- [ ] Non-polygonal geometry (LineString, Point) is silently dropped with no warning to the user
- [ ] EnergyADE attributes are not preserved (0% retention)
- [ ] Textures and appearance models are not supported
- [ ] District-scale datasets exhibit rendering distortion in ArcGIS Pro (root cause unknown)
- [ ] ArcGIS Online does not render output

### Planned improvements
- [ ] Pre-conversion geometry inventory with explicit warnings for unsupported types
- [ ] Post-conversion semantic preservation report
- [ ] Configurable attribute mapping profiles (planning, cadastre, minimal)
- [ ] Investigation of 3D Tiles 1.1 pathway as tile-converter support matures

Contributions addressing any of the above are welcome — see [Contributing](#contributing).

---

## Contributing

Contributions are welcome, particularly around the known issues listed above. Please open an issue before submitting a pull request so we can discuss the approach.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/geometry-warning`)
3. Commit your changes
4. Open a pull request with a clear description of what you've changed and why

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgements

This work was carried out at **HFT Stuttgart – University of Applied Sciences** under the M.Sc. Photogrammetry and Geoinformatics programme, supported by a **DAAD scholarship**.

Supervisors: **Prof. Dr. Zhihang Yao** and **Prof. Dr. Volker Coors**, HFT Stuttgart.

The workflow builds on the following open-source projects: [3DCityDB](https://github.com/3dcitydb/3dcitydb), [citygml-to-3dtiles](https://github.com/njam/citygml-to-3dtiles), [@loaders.gl/tile-converter](https://github.com/visgl/loaders.gl), [citydb-tool](https://github.com/3dcitydb/citydb-tool).
