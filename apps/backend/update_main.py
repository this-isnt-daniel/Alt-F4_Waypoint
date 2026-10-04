import sys
import re

with open('app/main.py', 'r') as f:
    content = f.read()

# Remove demo/orders endpoint
demo_pattern = r'@app\.post\(\"/api/v1/demo/orders\".*?return \{\n.*?\"items\": lines,\n    \}\n'
content = re.sub(demo_pattern, '', content, flags=re.DOTALL)

# Remove api_router
content = content.replace('from app.api.v1.router import api_router\n', '')
content = content.replace('app.include_router(api_router, prefix="/api")\n', '')
content = content.replace('app.include_router(api_router, prefix="/api/v1")\n', '')

# Modify lifespan and DB initialization
content = content.replace('from app.database import init_db\n', '')

new_lifespan = '''@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.session import engine
    from sqlalchemy import text
    try:
        # Verify PostgreSQL connection availability
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        raise RuntimeError("PostgreSQL database is required but unavailable.") from e
    yield'''

old_lifespan_pattern = r'@asynccontextmanager\nasync def lifespan\(app: FastAPI\):\n    init_db\(\).*?yield'
content = re.sub(old_lifespan_pattern, new_lifespan, content, flags=re.DOTALL)

with open('app/main.py', 'w') as f:
    f.write(content)
