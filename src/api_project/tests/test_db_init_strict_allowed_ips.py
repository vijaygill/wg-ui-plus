"""Tests for the WG_STRICT_ALLOWED_IPS_IN_PEER_CONFIG sync (REV-09).

The db_init_db_on_start command must only sync the environment value into the
saved ServerConfiguration when the variable is actually present. An absent
variable must leave the database value untouched; a present value is
authoritative in both directions.
"""

import os
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from api_app.models import ServerConfiguration

ENV_VAR = "WG_STRICT_ALLOWED_IPS_IN_PEER_CONFIG"


class DbInitStrictAllowedIpsTests(TestCase):
    def _seed(self):
        """Run the command once with the variable absent to seed the database."""
        with patch.dict(os.environ, {}, clear=True):
            call_command("db_init_db_on_start")

    def test_absent_variable_preserves_saved_true(self):
        self._seed()
        sc = ServerConfiguration.objects.get()
        sc.strict_allowed_ips_in_peer_config = True
        sc.save()

        self._seed()

        sc.refresh_from_db()
        self.assertTrue(
            sc.strict_allowed_ips_in_peer_config,
            "an absent WG_STRICT_ALLOWED_IPS_IN_PEER_CONFIG must not reset "
            "a saved True value",
        )

    def test_present_false_turns_field_off(self):
        self._seed()
        sc = ServerConfiguration.objects.get()
        sc.strict_allowed_ips_in_peer_config = True
        sc.save()

        with patch.dict(os.environ, {ENV_VAR: "false"}, clear=True):
            call_command("db_init_db_on_start")

        sc.refresh_from_db()
        self.assertFalse(
            sc.strict_allowed_ips_in_peer_config,
            "an explicit false must turn the field off",
        )

    def test_present_true_turns_field_on(self):
        self._seed()
        sc = ServerConfiguration.objects.get()
        sc.strict_allowed_ips_in_peer_config = False
        sc.save()

        with patch.dict(os.environ, {ENV_VAR: "true"}, clear=True):
            call_command("db_init_db_on_start")

        sc.refresh_from_db()
        self.assertTrue(
            sc.strict_allowed_ips_in_peer_config,
            "an explicit true must turn the field on",
        )

    def test_present_nonsense_value_is_treated_as_false(self):
        self._seed()
        sc = ServerConfiguration.objects.get()
        sc.strict_allowed_ips_in_peer_config = True
        sc.save()

        with patch.dict(os.environ, {ENV_VAR: "maybe"}, clear=True):
            call_command("db_init_db_on_start")

        sc.refresh_from_db()
        self.assertFalse(
            sc.strict_allowed_ips_in_peer_config,
            "a value outside TRUE_VALUES must be treated as false without "
            "raising",
        )
