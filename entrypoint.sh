#!/bin/bash

echo "=========================================="
echo "CityGML to I3S Converter - Docker Version"
echo "=========================================="

# Set environment variables with defaults
export POSTGRES_HOST=${POSTGRES_HOST:-localhost}
export POSTGRES_PORT=${POSTGRES_PORT:-5432}
export POSTGRES_DB=${POSTGRES_DB:-3d-DB-lod}
export POSTGRES_USER=${POSTGRES_USER:-postgres}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-c1h1u1k1s1}
export POSTGRES_SCHEMA=${POSTGRES_SCHEMA:-citydb}
export OUTPUT_NAME=${OUTPUT_NAME:-city_model}
export MAX_DEPTH=${MAX_DEPTH:-6}
export OUTPUT_DIR=${OUTPUT_DIR:-/app/output}
export LOG_DIR=${LOG_DIR:-/app/logs}
export LOD_FILTER=${LOD_FILTER:-}
export EXPORT_MODE=${EXPORT_MODE:-Exterior Only}
export LOD_MODE=${LOD_MODE:-Exact Match}

echo "📋 Configuration:"
echo "  Database: ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
echo "  User: ${POSTGRES_USER}"
echo "  Schema: ${POSTGRES_SCHEMA}"
echo "  Output Name: ${OUTPUT_NAME}"
echo "  Max Depth: ${MAX_DEPTH}"
echo "  LOD Filter: ${LOD_FILTER:-All}"
echo "  Export Mode: ${EXPORT_MODE}"
echo "  LOD Mode: ${LOD_MODE}"
echo "  Output Directory: ${OUTPUT_DIR}"
echo "  Log Directory: ${LOG_DIR}"
echo "=========================================="

# Wait for PostgreSQL if needed
if [ "$WAIT_FOR_DB" = "true" ]; then
    echo "⏳ Waiting for database to be ready..."
    until PGPASSWORD=${POSTGRES_PASSWORD} psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -p "${POSTGRES_PORT}" -d "${POSTGRES_DB}" -c '\q' 2>/dev/null; do
        echo "Waiting for database connection..."
        sleep 5
    done
    echo "✅ Database is ready!"
fi

# Check for citydb command
CITYDB_CMD=$(which citydb 2>/dev/null || true)
if [ -z "$CITYDB_CMD" ]; then
    # Try alternative locations
    if [ -f "/usr/local/lib/3dcitydb/tools/citydb" ]; then
        CITYDB_CMD="/usr/local/lib/3dcitydb/tools/citydb"
    elif [ -f "/opt/3dcitydb/tools/citydb" ]; then
        CITYDB_CMD="/opt/3dcitydb/tools/citydb"
    else
        echo "❌ ERROR: citydb command not found!"
        echo "Searching for citydb in common locations..."
        find / -name "*citydb*" -type f 2>/dev/null | head -10
        exit 1
    fi
fi

echo "✅ Using citydb command: $CITYDB_CMD"

# Create directories
echo "🔧 Setting up directories..."
mkdir -p "${OUTPUT_DIR}" "${LOG_DIR}"
mkdir -p "${OUTPUT_DIR}/3dtiles" "${OUTPUT_DIR}/i3s"

# Test if directories are writable
if touch "${OUTPUT_DIR}/.test_write" 2>/dev/null; then
    rm -f "${OUTPUT_DIR}/.test_write"
    echo "✅ Output directory is writable"
else
    echo "⚠️  Output directory may not be writable"
    echo "⚠️  Trying to fix permissions..."
    chmod 777 "${OUTPUT_DIR}" 2>/dev/null || true
fi

# Run the converter script
if [ -f "/app/scripts/citygml_to_i3s.py" ]; then
    echo "🚀 Starting conversion workflow..."
    
    # Build command arguments
    CMD_ARGS="--host ${POSTGRES_HOST} \
              --port ${POSTGRES_PORT} \
              --db ${POSTGRES_DB} \
              --user ${POSTGRES_USER} \
              --password '${POSTGRES_PASSWORD}' \
              --schema ${POSTGRES_SCHEMA} \
              --output-name ${OUTPUT_NAME} \
              --max-depth ${MAX_DEPTH} \
              --output-dir ${OUTPUT_DIR} \
              --log-dir ${LOG_DIR}"
    
    # Add optional arguments if provided
    if [ -n "$LOD_FILTER" ]; then
        CMD_ARGS="$CMD_ARGS --lod $LOD_FILTER"
    fi
    
    # Execute the Python script
    echo "Running: python /app/scripts/citygml_to_i3s.py $CMD_ARGS"
    python /app/scripts/citygml_to_i3s.py \
        --host "${POSTGRES_HOST}" \
        --port "${POSTGRES_PORT}" \
        --db "${POSTGRES_DB}" \
        --user "${POSTGRES_USER}" \
        --password "${POSTGRES_PASSWORD}" \
        --schema "${POSTGRES_SCHEMA}" \
        --output-name "${OUTPUT_NAME}" \
        --max-depth "${MAX_DEPTH}" \
        --output-dir "${OUTPUT_DIR}" \
        --log-dir "${LOG_DIR}" \
        $( [ -n "$LOD_FILTER" ] && echo "--lod $LOD_FILTER" )
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "=========================================="
        echo "🎉 Workflow completed successfully!"
        echo "📁 Output files in: ${OUTPUT_DIR}"
        echo "📄 Log files in: ${LOG_DIR}"
        
        # List generated files
        echo "📦 Generated files:"
        find "${OUTPUT_DIR}" -type f -name "*.slpk" -o -name "*.gml" -o -name "tileset.json" 2>/dev/null | while read file; do
            size=$(du -h "$file" | cut -f1)
            echo "  - $(basename "$file") ($size)"
        done
        echo "=========================================="
    else
        echo "=========================================="
        echo "❌ Workflow failed with exit code: $EXIT_CODE"
        echo "📁 Check logs in: ${LOG_DIR}"
        echo "=========================================="
        exit $EXIT_CODE
    fi
else
    echo "⚠️ No converter script found at /app/scripts/citygml_to_i3s.py"
    echo "Starting bash shell..."
    /bin/bash
fi