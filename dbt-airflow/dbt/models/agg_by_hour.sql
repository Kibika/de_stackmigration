with source_traffic_flow as (
  SELECT EXTRACT(hour FROM utc_time_id) "hour", avg(avg_flow) "average_traffic", avg(avg_speed) "average_speed", avg(avg_occ) "average occupancy"
  FROM {{ source('sensor_db', 'maindata')}}
  GROUP BY EXTRACT(hour FROM utc_time_id)
  ORDER BY hour ASC
)

SELECT * FROM source_traffic_flow