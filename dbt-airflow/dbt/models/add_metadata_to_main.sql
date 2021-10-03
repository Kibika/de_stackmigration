with source_metadata as (
  SELECT ID, Name, Lanes, Length, State_PM, Abs_PM
  FROM {{ source('sensor_db', 'metadata')}}
  LEFT OUTER JOIN {{ source('sensor_db', 'maindata')}}
  ON {{ source('sensor_db', 'metadata')}}.ID={{ source('sensor_db', 'maindata')}}.source_id
)

SELECT * FROM source_metadata
