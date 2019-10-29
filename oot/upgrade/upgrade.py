import importlib.util
import logging
import os

import pip._internal.main as pip
from packaging import version as packaging_version

_logger = logging.getLogger(__name__)


def upgrade(current_version, version, path, migration_package):
    if current_version >= version:
        return False
    if os.path.exists(os.path.join(path, "requirements.txt")):
        pass
        pip.main(["install", "-r", os.path.join(path, "requirements.txt"), "--upgrade"])
    migration_path = migration_package.__path__._path[0]
    migrations = []
    for vers in os.listdir(migration_path):
        migration_version = packaging_version.parse(vers)
        if migration_version <= version and migration_version > current_version:
            migrations.append(migration_version)
    migrations = sorted(migrations)
    for migration in migrations:
        spec = importlib.util.spec_from_file_location(
            "migration",
            os.path.join(migration_path, migration.base_version, "migration.py"),
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _logger.info("Executing migration for %s" % migration.base_version)
        module.migrate()
    return True
