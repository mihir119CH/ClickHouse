import os
from typing import Callable, List

from helpers.cluster import ClickHouseCluster, ClickHouseInstance


def generate_cluster_def(name: str, num_nodes: int) -> str:
    path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        f"./_gen/cluster_{name}.xml",
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            """
<clickhouse>
    <remote_servers>
        <cluster>
            <shard>
"""
        )
        for i in range(num_nodes):
            f.write(
                f"""
                <replica>
                    <host>node{i}</host>
                    <port>9000</port>
                </replica>
"""
            )
        f.write(
            """
                </shard>
        </cluster>
    </remote_servers>
</clickhouse>"""
        )
    return path


def gen_nodes(
    cluster: ClickHouseCluster,
    num_nodes: int,
    main_configs: List[str],
    user_configs: List[str],
) -> List[ClickHouseInstance]:
    nodes = []
    for i in range(num_nodes):
        nodes.append(
            cluster.add_instance(
                f"node{i}",
                main_configs=main_configs,
                user_configs=user_configs,
                external_dirs=["/backups/"],
                macros={"replica": f"node{i}", "shard": "shard1"},
                with_zookeeper=True,
            )
        )
    return nodes


def create_and_fill_table(
    nodes: List[ClickHouseInstance], fill: Callable[[List[ClickHouseInstance]], None]
) -> None:
    nodes[0].query(
        "CREATE TABLE tbl ON CLUSTER 'cluster' ("
        "x UInt64"
        ") ENGINE=ReplicatedMergeTree('/clickhouse/tables/tbl/', '{replica}')"
        "ORDER BY x"
    )
    fill(nodes)
