from typing import ForwardRef

from django.test import SimpleTestCase
from mcp.server.fastmcp.server import Settings


class MCPCompatibilityTests(SimpleTestCase):
    def test_fastmcp_lifespan_annotation_is_resolved_before_server_startup(self):
        self.assertNotIsInstance(Settings.model_fields["lifespan"].annotation, ForwardRef)
