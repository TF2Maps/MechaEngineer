import struct
import re
import lzma

# Define the lump indices
LUMP_ENTITIES = 0
LUMP_LIGHTING = 8
LUMP_LIGHTING_HDR = 53
LUMP_WORLDLIGHTS_HDR = 54
LUMP_LEAF_AMBIENT_LIGHTING_HDR = 55

# little-endian "LZMA"
LZMA_ID = ((ord('A')<<24)|(ord('M')<<16)|(ord('Z')<<8)|(ord('L')))

# Parse I/O connections from entity keyvalues
def entity_parse_connections(entity):
    connections = []
    for key, value in entity:
        # Check if the value contains a comma or ESC character
        if ',' in value or '\x1b' in value:
            # Split the value into connection parts
            parts = re.split(r',|\x1b', value)
            connections.append(parts)

    return connections    

# Open the .bsp file
def bsp_validate_hdr(name):
    with open(name, 'rb') as f:
        # Read the header
        header_t = struct.Struct('ii')
        header = header_t.unpack(f.read(header_t.size))
        ident, version = header

        # Get the lumps
        lump_t = struct.Struct('iiii')
        lumps = [lump_t.unpack(f.read(lump_t.size)) for _ in range(64)]
        
        # These lumps are required for HDR
        hdr = lumps[LUMP_LIGHTING_HDR][1] != 0 and lumps[LUMP_WORLDLIGHTS_HDR][1] != 0 and lumps[LUMP_LEAF_AMBIENT_LIGHTING_HDR][1] != 0
        
        # Perform the checks
        if lumps[LUMP_LIGHTING][1] == 0:
            if not hdr:
                return [False, "Error: Map has no lighting"]  
            return [False, "Error: Map has no LDR lighting"]       
        elif not hdr:
            return [True, "Success: Map has valid lighting (LDR and no HDR)"]
        else:
            # Get the entities lump
            f.seek(lumps[LUMP_ENTITIES][0])
            entity_lump = f.read(lumps[LUMP_ENTITIES][1])
            
            # Check if the entity lump is compressed
            lzma_header_t = struct.Struct('III5s')
            lzma_header = lzma_header_t.unpack(entity_lump[:lzma_header_t.size])
            id, actual_size, lzma_size, properties = lzma_header
            if id == LZMA_ID:         
                # Convert to standard LZMA header
                standard_lzma_header = struct.pack('<5sQ', properties, actual_size)

                # Read the compressed data
                compressed_data = standard_lzma_header + entity_lump[lzma_header_t.size:]

                # Decompress the data
                try:
                    decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
                    entity_data = decompressor.decompress(compressed_data)
                except lzma.LZMAError as e:
                    return [False, f"Error: Map decompression failed: {e}"]
            else:
                entity_data = entity_lump
            
            #UnicodeDecodeError
            try:
                #entity_data = entity_data.decode('utf-8')
                entity_data = entity_data.decode('cp1252')
            except UnicodeDecodeError as e:
                return [False, f"Error: Something failed in HDR: {e}"]
            
            # Parse the entities
            chunks = re.findall(r'\{[^}]*\}', entity_data)
            
            # Parse key values of each entity
            entities = []
            for entity in chunks:
                # Split the entity into key-value pairs
                pairs = re.findall(r'"([^"]*)"\s*"([^"]*)"', entity)
                entities.append(pairs)
            
            # Find the light_environment
            light_environment = [entity for entity in entities if any(pair for pair in entity if pair[0] == 'classname' and pair[1] == 'light_environment')]
            if light_environment:
                light_environment_light_scale = next(pair[1] for pair in light_environment[0] if pair[0] == '_lightscaleHDR')
                light_scale = light_environment_light_scale.split(' ')[0]
                try:
                    light_scale = float(light_scale)
                except ValueError:
                    light_scale = 0

                if not 0 < light_scale <= 2:
                    return [False, f'Error: Bad HDR brightness scale ({light_scale})']

                light_environment_ambient_scale = next(pair[1] for pair in light_environment[0] if pair[0] == '_AmbientScaleHDR')
                ambient_scale = light_environment_ambient_scale.split(' ')[0]
                try:
                    ambient_scale = float(ambient_scale)
                except ValueError:
                    ambient_scale = 0

                if not 0 < ambient_scale <= 5:
                    return [False, f'Error: Bad HDR ambient scale ({ambient_scale})']

            # Find the env_tonemap_controller
            tonemap_controller = [entity for entity in entities if any(pair for pair in entity if pair[0] == 'classname' and pair[1] == 'env_tonemap_controller')]
            if not tonemap_controller:
                return [False, "Error: Map has HDR lighting but no env_tonemap_controller"]
            else:
                try:
                    tonemap_controller_name = next((pair[1] for pair in tonemap_controller[0] if pair[0] == 'targetname'), 'env_tonemap_controller')
                except RuntimeError as e:
                    return [False, f'Error: Tonemap controller has no name? {e}']
                
                # Check for connections to the env_tonemap_controller
                for entity in entities:
                    connections = entity_parse_connections(entity)
                    for connection in connections:
                        if tonemap_controller_name in connection and 'SetBloomScale' in connection:
                            return [True, "Success: Map has valid lighting (LDR and HDR)"]
                            
                return [False, "Error: env_tonemap_controller is not setup by I/O"   ]      
        
    return "Failed to open map"
