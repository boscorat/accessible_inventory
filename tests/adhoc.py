from data.duck import dd

entity_id = "281d67f9-7236-4c63-adaf-c7fac017d962"

ent = (
    dd.execute("select * from entity_sql where entity_id = ?", [entity_id])
    .df()
    .to_dict("records")
)

dd.close()

print(ent[0])
