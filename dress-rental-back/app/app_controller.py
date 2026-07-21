from app.db.session import DSQLDatabase
from app.config import config


class AppController:
    def __init__(self, dsql_cluster_endpoint, dsql_cluster_user):
        self.dsql_session = DSQLDatabase(cluster_endpoint=dsql_cluster_endpoint, cluster_user=dsql_cluster_user)

app_controller = AppController(
    dsql_cluster_endpoint=config.DSQL_CLUSTER_ENDPOINT,
    dsql_cluster_user=config.DSQL_CLUSTER_USER
)
