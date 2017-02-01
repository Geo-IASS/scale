"""Defines the command line method for running a Scan process"""
from __future__ import unicode_literals

import logging
import signal
import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from ingest.models import Scan


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that executes the Workspace Scan processor
    """

    option_list = BaseCommand.option_list + (
        make_option('-i', '--scan-id', action='store', type='int', help=('ID of the Scan process to run')),
        make_option('-d', '--dry-run', action="store_true", default=False, help=('Perform a dry-run of scan, skipping ingest'))
    )

    help = 'Executes the Scan processor to make a single pass over a workspace for ingest'

    def __init__(self):
        """Constructor
        """

        super(Command, self).__init__()

        self._scan_id = None
        self._scanner = None
        self._dry_run = False

    def handle(self, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scan processor.
        """

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        self._scan_id = options.get('scan_id')
        self._dry_run = options.get('dry_run')
        
        if not self._scan_id:
            logger.error('-i or --scan-id parameter must be specified for Scan configuration.')
            print('what')
            sys.exit(1)

        logger.info('Command starting: scale_scan')
        logger.info('Scan ID: %i', self._scan_id)
        logger.info('Dry Run: %s', self._dry_run)

        logger.info('Querying database for Scan configuration')
        scan = Scan.objects.select_related('job').get(pk=self._scan_id)
        self._scanner = scan.get_scan_configuration().get_scanner()
        self._scanner.scan_id = self._scan_id

        logger.info('Starting %s scanner', self._scanner.scanner_type)
        self._scanner.run()
        logger.info('Scanner has stopped running')

        logger.info('Command completed: scale_scan')

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Scan command received sigterm, telling scanner to stop')

        if self._scanner:
            self._scanner.stop()
