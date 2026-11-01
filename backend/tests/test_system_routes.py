import unittest

from app.main import app


class LocalSystemRouteTests(unittest.TestCase):
    def test_backup_restore_and_media_routes_are_registered(self):
        paths = set(app.openapi()["paths"])
        self.assertIn("/api/system/status", paths)
        self.assertIn("/api/system/assets", paths)
        self.assertIn("/api/system/backup", paths)
        self.assertIn("/api/system/restore", paths)
        self.assertIn("/api/system/safety-backups/{filename}", paths)
        self.assertIn("/api/companions/{companion_id}/avatar", paths)
        route_paths = {getattr(route, "path", None) for route in app.routes}
        self.assertIn("/media", route_paths)


if __name__ == "__main__":
    unittest.main()
