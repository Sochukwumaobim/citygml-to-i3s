# Dockerized CityGML to I3S Converter

A complete Docker-based workflow for converting CityGML files to I3S Scene Layer Packages (SLPK).

## Features

- **Full workflow**: CityGML → 3DCityDB → 3D Tiles → I3S SLPK
- **Dockerized**: Easy deployment and sharing
- **Batch processing**: Process multiple CityGML files
- **Persistent storage**: Keep input/output data
- **PostgreSQL with PostGIS**: Ready-to-use database
- **Automatic schema creation**: 3DCityDB schema initialization

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM recommended
- 20GB+ free disk space

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone https://github.com/yourusername/citygml-to-i3s-docker.git
   cd citygml-to-i3s-docker