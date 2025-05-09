# tests/test_projects.py
import pytest
from zoho_sync.zoho import megaProjects

def test_fetch_mega_projects():
    projects = megaProjects.fetch_mega_projects()
    assert isinstance(projects, list)
    assert all('id' in project for project in projects)
