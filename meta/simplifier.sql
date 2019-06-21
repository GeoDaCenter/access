-- SIMPLIFIED CENSUS GEOMETRY IN POSTGIS
-- COPIED FROM https://strk.kbt.io/blog/2012/04/13/simplifying-a-map-layer-using-postgis-topology/

CREATE OR REPLACE FUNCTION SimplifyEdgeGeom(atopo varchar, anedge int, maxtolerance float8)
RETURNS float8 AS $$
DECLARE
  tol float8;
  sql varchar;
BEGIN
  tol := maxtolerance;
  LOOP
    sql := 'SELECT topology.ST_ChangeEdgeGeom(' || quote_literal(atopo) || ', ' || anedge
      || ', ST_Simplify(geom, ' || tol || ')) FROM '
      || quote_ident(atopo) || '.edge WHERE edge_id = ' || anedge;
    BEGIN
      -- RAISE NOTICE 'Running %', sql;
      EXECUTE sql;
      RETURN tol;
    EXCEPTION
     WHEN OTHERS THEN
      RAISE WARNING 'Simplification of edge % with tolerance % failed: %', anedge, tol, SQLERRM;
      tol := round( (tol/2.0) * 1e8 ) / 1e8; -- round to get to zero quicker
      IF tol = 0 THEN 
        RAISE NOTICE 'Tolerance reached 0.  Exception: %', SQLERRM; 
        RETURN 0;
      END IF;
    END;
  END LOOP;
END
$$ LANGUAGE 'plpgsql' STABLE STRICT;




--Change Geometry to from CRS 4326 to CRS 2163
ALTER TABLE gz_2010_17_140_00_500k
 ALTER COLUMN geom TYPE geometry(MultiPolygon,2163) 
  USING ST_Transform(
     ST_SetSRID( geom,4326 ) 
       , 2163 
       );
	   


-- Drop the topology, in case:
SELECT topology.DropTopology('state_topo');
-- Create a topology
SELECT topology.CreateTopology('state_topo', find_srid('public', 'gz_2010_17_140_00_500k', 'geom'));

-- Add a layer to it.
SELECT topology.AddTopoGeometryColumn('state_topo', 'public', 'gz_2010_17_140_00_500k', 'topogeom', 'MULTIPOLYGON');

DO $$DECLARE r record;
BEGIN
 FOR r IN SELECT DISTINCT state FROM gz_2010_17_140_00_500k LOOP
  BEGIN
		RAISE NOTICE 'state = %', r.state;
    UPDATE gz_2010_17_140_00_500k 
		SET topogeom = toTopoGeom(geom,'state_topo', 1) 
    WHERE state = r.state;
   EXCEPTION
    WHEN OTHERS THEN
     RAISE WARNING 'Loading of % failed: %', r.state, SQLERRM;
  END;
 END LOOP;
END$$;


-- Simplify all edges up to 1 km
SELECT SimplifyEdgeGeom('state_topo', edge_id, 10000) FROM state_topo.edge;

--Add geomsimp table 
ALTER TABLE gz_2010_17_140_00_500k ADD geomsimp GEOMETRY;

UPDATE gz_2010_17_140_00_500k SET geomsimp = topogeom::geometry;

--Change files back to CRS 4326 from CRS 2163
ALTER TABLE gz_2010_17_140_00_500k
 ALTER COLUMN geomsimp TYPE geometry(MultiPolygon,4326) 
  USING ST_Transform(
     ST_SetSRID( geom,2163 ) 
       , 4326
       );

-- Changes table to geoJSON format
CREATE TABLE state17 As SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(
            json_build_object(
                'type',       'Feature',
                'geometry',   ST_AsGeoJSON(geomsimp)::json,
                'properties', json_build_object(
                    'geo_id', geo_id,
                    'state', state,
                    'county', county,
                    'tract', tract
                )
            )
        )
    )
    FROM gz_2010_17_140_00_500k;
--Save state file
COPY state17 TO 'D:\maps\state17.geojson';