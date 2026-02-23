#!/usr/bin/env python3
"""
CityGML to I3S Converter - Complete Docker Version
"""

import os
import sys
import argparse
import psycopg2
from datetime import datetime
import subprocess
import json
import logging
import shutil
import time

def setup_logging(log_dir):
    """Setup logging configuration"""
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'conversion_{timestamp}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def connect_to_database(params):
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            database=params['db'],
            user=params['user'],
            password=params['password']
        )
        return conn
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")

def export_to_citygml(params, output_dir, logger):
    """Export database to CityGML"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"export_{timestamp}.gml")
    
    logger.info(f"Exporting to CityGML: {output_file}")
    
    # Build export command
    cmd = [
        'citydb',
        'export', 'citygml',
        '--db-host', params['host'],
        '--db-port', str(params['port']),
        '--db-name', params['db'],
        '--db-schema', params['schema'],
        '--db-username', params['user'],
        '--db-password', params['password'],
        '--output', output_file,
        '--citygml-version', '2.0',
        '--no-appearances'
    ]
    
    # Add LOD filter if specified
    if params.get('lod'):
        cmd.extend(['--lod', params['lod']])
    
    # Add export mode
    export_mode = os.getenv('EXPORT_MODE', 'Exterior Only')
    if export_mode == "Exterior Only":
        cmd.extend(['--type-name', 'bldg:Building'])
    elif export_mode == "Exterior + Installations":
        cmd.extend(['--type-name', 'bldg:Building,bldg:BuildingInstallation'])
    
    # Add LOD mode
    lod_mode = os.getenv('LOD_MODE', 'Exact Match')
    if lod_mode == "Exact Match" and params.get('lod'):
        cmd.extend(['--lod-mode', 'and'])
    elif lod_mode == "Any Match" and params.get('lod'):
        cmd.extend(['--lod-mode', 'or'])
    
    logger.info(f"Running command: {' '.join(cmd[:10])}... [password hidden]")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"✅ CityGML export completed")
        
        # Check file was created
        if os.path.exists(output_file):
            size = os.path.getsize(output_file) / (1024 * 1024)
            logger.info(f"📁 File created: {os.path.basename(output_file)} ({size:.2f} MB)")
            return output_file
        else:
            raise Exception(f"CityGML file not created: {output_file}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ CityGML export failed")
        logger.error(f"stderr: {e.stderr[:500]}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during export: {str(e)}")
        raise

def convert_to_3dtiles(citygml_file, output_dir, logger):
    """Convert CityGML to 3D Tiles"""
    logger.info("Converting CityGML to 3D Tiles...")
    
    # Create output directory
    tiles_dir = os.path.join(output_dir, '3dtiles')
    
    # Clean up existing directory
    if os.path.exists(tiles_dir):
        try:
            shutil.rmtree(tiles_dir)
            logger.info(f"🧹 Cleaned existing directory: {tiles_dir}")
        except Exception as e:
            logger.warning(f"Could not remove existing directory: {str(e)}")
    
    # Create directory
    os.makedirs(tiles_dir, exist_ok=True)
    
    # Test if directory is writable
    try:
        test_file = os.path.join(tiles_dir, '.test_write')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.info(f"✅ Directory is writable: {tiles_dir}")
    except Exception as e:
        logger.error(f"❌ Directory not writable: {str(e)}")
        raise
    
    cmd = [
        'citygml-to-3dtiles',
        citygml_file,
        tiles_dir
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run conversion
        env = os.environ.copy()
        env['NODE_OPTIONS'] = '--max-old-space-size=4096'
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            env=env
        )
        
        logger.info("✅ 3D Tiles conversion completed")
        
        # Verify output
        tileset_json = find_tileset_json(tiles_dir)
        if tileset_json:
            logger.info(f"✅ Found tileset.json: {tileset_json}")
            return tiles_dir
        else:
            raise Exception("tileset.json not found after conversion")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 3D Tiles conversion failed")
        logger.error(f"stderr: {e.stderr[:500]}")
        
        # Check for specific errors
        if "EACCES" in e.stderr or "permission denied" in e.stderr:
            logger.error("⚠️ Permission error detected!")
        
        if "out of memory" in e.stderr.lower():
            logger.error("⚠️ Out of memory error!")
        
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during 3D Tiles conversion: {str(e)}")
        raise

def convert_to_i3s(tiles_dir, output_dir, output_name, max_depth, logger):
    """Convert 3D Tiles to I3S SLPK"""
    logger.info("Converting 3D Tiles to I3S SLPK...")
    
    # Create output directory
    i3s_dir = os.path.join(output_dir, 'i3s')
    os.makedirs(i3s_dir, exist_ok=True)
    
    # Test if directory is writable
    try:
        test_file = os.path.join(i3s_dir, '.test_write')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.info(f"✅ I3S directory is writable: {i3s_dir}")
    except Exception as e:
        logger.error(f"❌ I3S directory not writable: {str(e)}")
        raise
    
    # Find tileset.json
    tileset_json = find_tileset_json(tiles_dir)
    if not os.path.exists(tileset_json):
        raise Exception(f"tileset.json not found in {tiles_dir}")
    
    logger.info(f"Using tileset: {tileset_json}")
    
    # Run WITHOUT EGM file (simpler, works for most cases)
    logger.info("Running without EGM file (optional for height adjustment)")
    cmd = [
        'npx', 'tile-converter',
        '--input-type', '3DTILES',
        '--tileset', tileset_json,
        '--name', output_name,
        '--output', i3s_dir,
        '--max-depth', str(max_depth),
        '--slpk'
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run conversion
        env = os.environ.copy()
        env['NODE_OPTIONS'] = '--max-old-space-size=4096'
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env=env,
            cwd="/app"  # Run from /app directory
        )
        
        logger.info("✅ I3S conversion completed")
        
        # Find the SLPK file
        slpk_file = None
        for root, dirs, files in os.walk(i3s_dir):
            for file in files:
                if file.endswith('.slpk'):
                    slpk_file = os.path.join(root, file)
                    break
            if slpk_file:
                break
        
        if slpk_file and os.path.exists(slpk_file):
            size = os.path.getsize(slpk_file) / (1024 * 1024)
            logger.info(f"✅ SLPK file created: {os.path.basename(slpk_file)} ({size:.2f} MB)")
            
            # Copy to main output directory
            final_slpk = os.path.join(output_dir, os.path.basename(slpk_file))
            shutil.copy2(slpk_file, final_slpk)
            logger.info(f"📁 SLPK copied to: {final_slpk}")
            
            return final_slpk
        else:
            # Check output directory directly
            for file in os.listdir(output_dir):
                if file.endswith('.slpk'):
                    slpk_file = os.path.join(output_dir, file)
                    size = os.path.getsize(slpk_file) / (1024 * 1024)
                    logger.info(f"✅ Found SLPK in output directory: {slpk_file} ({size:.2f} MB)")
                    return slpk_file
            
            raise Exception("No SLPK file created after conversion")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ I3S conversion failed")
        logger.error(f"stderr: {e.stderr[:500]}")
        
        # Check for specific errors
        if "EACCES" in e.stderr or "permission denied" in e.stderr:
            logger.error("⚠️ Permission error during I3S conversion!")
            
        if "zip" in e.stderr and "ENOENT" in e.stderr:
            logger.error("⚠️ ZIP command not found! Install with: apt-get install -y zip")
            
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during I3S conversion: {str(e)}")
        raise

def find_tileset_json(directory):
    """Find tileset.json in directory"""
    for root, dirs, files in os.walk(directory):
        if "tileset.json" in files:
            return os.path.join(root, "tileset.json")
    
    # Also check for .json files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json') and 'tileset' in file.lower():
                return os.path.join(root, file)
    
    return None

def main():
    parser = argparse.ArgumentParser(description='CityGML to I3S Converter')
    
    # Database parameters
    parser.add_argument('--host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--port', type=int, default=5432, help='PostgreSQL port')
    parser.add_argument('--db', required=True, help='Database name')
    parser.add_argument('--user', required=True, help='Database user')
    parser.add_argument('--password', required=True, help='Database password')
    parser.add_argument('--schema', default='citydb', help='Database schema')
    
    # Conversion parameters
    parser.add_argument('--output-name', default='city_model', help='Output name for SLPK')
    parser.add_argument('--max-depth', type=int, default=6, help='Max depth for conversion')
    parser.add_argument('--lod', help='LOD level to export (e.g., 2)')
    
    # Directory parameters
    parser.add_argument('--output-dir', default='/app/output', help='Output directory')
    parser.add_argument('--log-dir', default='/app/logs', help='Log directory')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_dir)
    
    logger.info("=" * 60)
    logger.info("Starting CityGML to I3S Conversion Workflow")
    logger.info("=" * 60)
    
    try:
        # Database parameters
        db_params = {
            'host': args.host,
            'port': args.port,
            'db': args.db,
            'user': args.user,
            'password': args.password,
            'schema': args.schema,
            'lod': args.lod
        }
        
        logger.info(f"Database: {db_params['host']}:{db_params['port']}/{db_params['db']}")
        logger.info(f"User: {db_params['user']}")
        logger.info(f"LOD Filter: {db_params.get('lod', 'All')}")
        
        # Step 1: Export to CityGML
        logger.info("=" * 60)
        logger.info("Step 1: Exporting database to CityGML...")
        logger.info("=" * 60)
        citygml_file = export_to_citygml(db_params, args.output_dir, logger)
        
        # Step 2: Convert to 3D Tiles
        logger.info("=" * 60)
        logger.info("Step 2: Converting CityGML to 3D Tiles...")
        logger.info("=" * 60)
        tiles_dir = convert_to_3dtiles(citygml_file, args.output_dir, logger)
        
        # Step 3: Convert to I3S SLPK
        logger.info("=" * 60)
        logger.info("Step 3: Converting 3D Tiles to I3S SLPK...")
        logger.info("=" * 60)
        slpk_file = convert_to_i3s(tiles_dir, args.output_dir, args.output_name, args.max_depth, logger)
        
        logger.info("=" * 60)
        logger.info("✅ CONVERSION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"📦 Final SLPK file: {slpk_file}")
        logger.info(f"📊 File size: {os.path.getsize(slpk_file) / (1024 * 1024):.2f} MB")
        logger.info(f"🎯 LOD Filter: {db_params.get('lod', 'All')}")
        logger.info(f"📁 All output in: {args.output_dir}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ CONVERSION FAILED!")
        logger.error("=" * 60)
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())