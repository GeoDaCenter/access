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


DO
$$
DECLARE
    rec record;
	r record;
	counties record;
BEGIN
    FOR rec IN 
        SELECT table_name FROM information_schema.tables WHERE table_schema='shapefiles' 
    LOOP
		EXECUTE format('
		--Change Geometry to from CRS 4326 to CRS 2163
		ALTER TABLE shapefiles.%1$s
		 ALTER COLUMN geom TYPE geometry(MultiPolygon,2163) 
		  USING ST_Transform(
			 ST_SetSRID( geom,4326 ) 
			   , 2163 
			   );
		
		--Drop In Case
		SELECT topology.DropTopology(''state_topo''); --NEEDS FIXING: THIS LINE CAUSES ERROR WHEN MULTIPLE STATE FILES ARE BEING SIMPLIFIED.

		-- Create a topology
		SELECT topology.CreateTopology(''state_topo'', find_srid(''shapefiles'', ''%1$s'', ''geom''));

		-- Add a layer to it.
		SELECT topology.AddTopoGeometryColumn(''state_topo'', ''shapefiles'', ''%1$s'', ''topogeom'', ''MULTIPOLYGON'');
		
		DROP TABLE IF EXISTS tempholder;
		CREATE TABLE tempholder As SELECT * FROM shapefiles.%1$s;',rec.table_name);


		 FOR r IN SELECT DISTINCT state FROM tempholder LOOP
		  BEGIN
				RAISE NOTICE 'state = %', r.state;

			UPDATE tempholder 
			SET topogeom = toTopoGeom(geom,'state_topo', 1) 
			WHERE state = r.state;
		   EXCEPTION
			WHEN OTHERS THEN
			 RAISE WARNING 'Loading of % failed: %', r.state, SQLERRM;
		  END;
		 END LOOP;
		 
		-- Simplify all edges up to 1 km
		
		PERFORM SimplifyEdgeGeom('state_topo', edge_id, 10000) FROM state_topo.edge;
		--Add geomsimp table 
		ALTER TABLE tempholder ADD geomsimp GEOMETRY;

		UPDATE tempholder SET geomsimp = topogeom::geometry;

		ALTER TABLE tempholder ADD geoid varchar(15);
		--Remove 1400000US from geoid
		UPDATE tempholder SET geoid = REPLACE(geo_id,'1400000US','');

		ALTER TABLE tempholder DROP COLUMN geo_id;

		--Change files back to CRS 4326 from CRS 2163
		ALTER TABLE tempholder
		 ALTER COLUMN geomsimp TYPE geometry(MultiPolygon,4326) 
		  USING ST_Transform(
			 ST_SetSRID( geomsimp,2163 ) 
			   , 4326
			   );
		
		EXECUTE format('CREATE TABLE countytables.distinctCounties As SELECT DISTINCT county FROM shapefiles.%1$s',rec.table_name);
		FOR counties IN SELECT county FROM countytables.distinctCounties
		LOOP
			EXECUTE format('
			DROP TABLE IF EXISTS countytables.state%2$scounty%1$s;
			CREATE TABLE countytables.state%2$scounty%1$s As SELECT * FROM tempholder WHERE county = ''%1$s'';
			DROP TABLE IF EXISTS geojson.state%2$scounty%1$s;
			CREATE TABLE geojson.state%2$scounty%1$s As SELECT json_build_object(
					''type'', ''FeatureCollection'',
					''features'', json_agg(
						json_build_object(
							''type'',       ''Feature'',
							''geometry'',   ST_AsGeoJSON(geomsimp)::json,
							''properties'', json_build_object(
								''geoid'', geoid,
								''state'', state,
								''county'', county,
								''tract'', tract
							)
						)
					)
				)
				FROM countytables.state%2$scounty%1$s;
			--Save state file
			COPY geojson.state%2$scounty%1$s TO ''D:\maps\state%2$scounty%1$s.geojson'';',counties.county,r.state);
		
		END LOOP;
		DROP TABLE countytables.distinctCounties;
		

    END LOOP;
END;
$$
LANGUAGE plpgsql;