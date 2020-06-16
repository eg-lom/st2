from __future__ import absolute_import

import json
from st2common import log as logging
from st2common.persistence.execution import ActionExecution
from st2common.transport import consumers
from st2common.transport import utils as transport_utils
from st2common.models.db.liveaction import LiveActionDB
from st2common.transport.queues import EXECUTION_BUILDER_RESUME_QUEUE

from st2executionbuilder.st2executionbuilder.helper import *
import redis

LOG = logging.getLogger(__name__)


class ExecutionBuilder(consumers.MessageHandler):
    message_type = LiveActionDB

    def __init__(self, connection, queues):
        super(ExecutionBuilder, self).__init__(connection, queues)
        self.redis_con = redis.Redis(host='192.168.1.24')

    def process(self, liveaction):
        execution = ActionExecution.get(liveaction__id=str(liveaction.id))
        exec_id = str(execution.id) if execution else None

        changelog = {
            "name": liveaction.context.get('mistral', {}).get('task_name') or liveaction.action,
            "id": str(liveaction.id),
            "execution_id": exec_id,
            "context": liveaction.context,
            "status": liveaction.status,
            "action_is_workflow": liveaction.action_is_workflow,

        }

        LOG.info("Change log {} ".format(json.dumps(changelog)))

        parent_hircy = get_parent_array(changelog)
        exec_graph = self.redis_con.get(parent_hircy[-1])
        exec_graph = json.loads(exec_graph) if exec_graph else None
        if not exec_graph:
            exec_graph = {'children': [], 'status': changelog['status'], 'name': changelog['name'],
                  'id': changelog['execution_id']}
        else:
            update_parent_execution_graph(exec_graph, parent_hircy, len(parent_hircy) - 1, changelog, 1)
        LOG.info("Updated Graph {}".format(json.dumps(exec_graph)))
        self.redis_con.set(parent_hircy[-1], json.dumps(exec_graph))



def get_builder():
    with transport_utils.get_connection() as conn:
        return ExecutionBuilder(conn, [EXECUTION_BUILDER_RESUME_QUEUE])
