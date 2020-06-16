from __future__ import absolute_import
import os
import sys

from st2executionbuilder.st2executionbuilder import config
from st2common import log as logging
from st2executionbuilder.st2executionbuilder import executionbuilder
from st2common.service_setup import setup as common_setup
from st2common.service_setup import teardown as common_teardown
from st2common.util.monkey_patch import monkey_patch

__all__ = [
    'main'
]

monkey_patch()

LOG = logging.getLogger(__name__)


def _setup():
    capabilities = {
        'name': 'executionbuilder',
        'type': 'passive'
    }
    common_setup(service='executionbuilder', config=config, setup_db=True, register_mq_exchanges=True,
                 register_signal_handlers=True, service_registry=True, capabilities=capabilities, run_migrations=False,
                 register_runners=False)


def _run_worker():
    LOG.info('(PID=%s) Execution builder started.', os.getpid())
    actions_notifier = executionbuilder.get_builder()
    try:
        actions_notifier.start(wait=True)
    except (KeyboardInterrupt, SystemExit):
        LOG.info('(PID=%s) Execution builder stopped.', os.getpid())
        actions_notifier.shutdown()
    return 0


def _teardown():
    common_teardown()


def main():
    try:
        _setup()
        return _run_worker()
    except SystemExit as exit_code:
        sys.exit(exit_code)
    except:
        LOG.exception('(PID=%s) Execution builder quit due to exception.', os.getpid())
        return 1
    finally:
        _teardown()
