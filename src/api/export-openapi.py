import yaml
from src.api.main import app

openapi_schema = app.openapi()

with open("docs/api/openapi-generated.yaml", "w", encoding="utf-8") as f:
    yaml.dump(openapi_schema, f, allow_unicode=True)

print("OpenAPI specification exported to docs/api/openapi-generated.yaml")
