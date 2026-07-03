from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from django.db.backends.signals import connection_created
        from .utils import slow_query_logger

        def register_slow_query_logger(sender, connection, **kwargs):
            if slow_query_logger not in connection.execute_wrappers:
                connection.execute_wrappers.append(slow_query_logger)

        # Must retain the reference, otherwise the weakref used by connect() is garbage collected
        # or we set weak=False
        connection_created.connect(register_slow_query_logger, weak=False)
