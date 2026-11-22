import logging
import signal
import unittest
from unittest.mock import MagicMock, patch

from worker_common.runner import run_consumer

log = logging.getLogger("test_runner")


class BrokerDown(Exception):
    pass


@patch("worker_common.runner.signal.signal")
class RunConsumerTest(unittest.TestCase):
    def test_normal_run_returns_0_and_closes(self, _signal):
        consumer = MagicMock()
        self.assertEqual(0, run_consumer(consumer, log, BrokerDown))
        consumer.connect.assert_called_once()
        consumer.start.assert_called_once()
        consumer.close.assert_called_once()

    def test_broker_error_returns_1_and_closes(self, _signal):
        consumer = MagicMock()
        consumer.connect.side_effect = BrokerDown("down")
        with self.assertLogs(log, level="CRITICAL"):
            self.assertEqual(1, run_consumer(consumer, log, BrokerDown))
        consumer.close.assert_called_once()

    def test_signal_handlers_stop_the_consumer(self, signal_mock):
        consumer = MagicMock()
        run_consumer(consumer, log, BrokerDown)
        handlers = {c.args[0]: c.args[1] for c in signal_mock.call_args_list}
        self.assertEqual({signal.SIGTERM, signal.SIGINT}, set(handlers))
        with self.assertLogs(log, level="INFO"):
            handlers[signal.SIGTERM](signal.SIGTERM, None)
        consumer.stop.assert_called_once()
