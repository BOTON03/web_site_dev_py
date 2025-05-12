# zoho_sync/services/sync.py
from zoho_sync.zoho.auth import get_access_token
from zoho_sync.zoho.megaProjects import get_mega_projects, get_attributes
from zoho_sync.db.mega_projects import insert_mega_project

def run_sync():
    access_token = get_access_token()
    offset = 0
    while True:
        projects, more_records = get_mega_projects(access_token, offset)
        if not projects:
            break
        for project in projects:
            attributes = get_attributes(access_token, project['id'])
            insert_mega_project(project, attributes)
        if not more_records:
            break
        offset += 200
