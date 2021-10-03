with avg_travel_time as (
  SELECT source_id, avg(avg_travel_time) "average_travel_time"
  FROM {{ source('sensor_db', 'maindata')}}
  GROUP BY source_id
  ORDER BY average_travel_time DESC
)

SELECT * FROM avg_travel_time