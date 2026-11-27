import json
from pathlib import Path

folder = Path("grafana-provisioning")
datasource = {"type": "prometheus", "uid": "prometheus"}
dashboard_uid = "ubuntu-node"
cpu = '100 - 100 * avg by (instance) (rate(node_cpu_seconds_total{job="nodeexporter",mode="idle"}[1m]))'
load = [f'node_load{minutes}{{job="nodeexporter"}}' for minutes in (1, 5, 15)]
memory = 'node_memory_MemAvailable_bytes{job="nodeexporter"}'
disk = 'node_filesystem_avail_bytes{job="nodeexporter",mountpoint="/",fstype!~"tmpfs|overlay|rootfs"}'

panels = [
    ("Загрузка CPU", "percent", [("CPU", cpu)]),
    ("Load Average 1 / 5 / 15", "short", list(zip(("1 мин", "5 мин", "15 мин"), load))),
    ("Доступная оперативная память", "bytes", [("RAM", memory)]),
    ("Свободное место на /", "bytes", [("/", disk)]),
]

rules = [
    ("high-cpu", "CPU выше 85%", cpu, ">", 85, "5m"),
    ("high-load", "Load Average выше числа CPU", load[1] + ' / on(instance) count by (instance) (node_cpu_seconds_total{job="nodeexporter",mode="idle"})', ">", 1, "5m"),
    ("low-memory", "Доступная RAM ниже 512 МиБ", memory, "<", 536870912, "5m"),
    ("low-disk", "Свободное место на / ниже 2 ГиБ", disk, "<", 2147483648, "5m"),
]

def write(path, value):
    destination = folder / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

write("datasources/prometheus.yaml", {
    "apiVersion": 1,
    "datasources": [{"name": "Prometheus", **datasource, "access": "proxy",
                     "url": "http://prometheus:9090", "isDefault": True,
                     "jsonData": {"timeInterval": "5s"}}],
})
write("dashboards/provider.yaml", {
    "apiVersion": 1,
    "providers": [{"name": "netology", "folder": "Нетология", "type": "file",
                   "allowUiUpdates": True, "options": {"path": "/var/lib/grafana/netology-dashboards"}}],
})
write("models/dashboard.json", {
    "uid": dashboard_uid, "title": "Ubuntu — мониторинг узла", "schemaVersion": 39,
    "tags": ["netology", "node-exporter"], "refresh": "10s",
    "time": {"from": "now-15m", "to": "now"},
    "panels": [
        {"id": number, "title": title, "type": "timeseries", "datasource": datasource,
         "gridPos": {"x": 12 * ((number - 1) % 2), "y": 9 * ((number - 1) // 2), "w": 12, "h": 9},
         "fieldConfig": {"defaults": {"unit": unit, "min": 0}, "overrides": []},
         "targets": [{"refId": chr(65 + index), "expr": expression,
                      "legendFormat": label, "range": True, "datasource": datasource}
                     for index, (label, expression) in enumerate(queries)]}
        for number, (title, unit, queries) in enumerate(panels, start=1)
    ],
})

expression_source = {"type": "__expr__", "uid": "__expr__"}
alert_rules = [
    {"uid": uid, "title": title, "condition": "B", "for": duration,
     "noDataState": "NoData", "execErrState": "Error",
     "annotations": {"__dashboardUid__": dashboard_uid, "__panelId__": str(number), "summary": title},
     "labels": {"severity": "warning"},
     "data": [
         {"refId": "A", "datasourceUid": "prometheus", "relativeTimeRange": {"from": 300, "to": 0},
          "model": {"refId": "A", "datasource": datasource, "expr": expression,
                    "instant": True, "range": False, "intervalMs": 1000, "maxDataPoints": 43200}},
         {"refId": "B", "datasourceUid": "__expr__", "relativeTimeRange": {"from": 0, "to": 0},
          "model": {"refId": "B", "datasource": expression_source, "type": "math",
                    "expression": f"$A {operator} {threshold}",
                    "intervalMs": 1000, "maxDataPoints": 43200}},
     ]}
    for number, (uid, title, expression, operator, threshold, duration) in enumerate(rules, start=1)
]
write("alerting/rules.yaml", {
    "apiVersion": 1,
    "groups": [{"orgId": 1, "name": "Ubuntu node", "folder": "Нетология",
                "interval": "1m", "rules": alert_rules}],
})

Path("compose.grafana.yaml").write_text("""services:
  grafana:
    volumes:
      - ./grafana-provisioning/datasources:/etc/grafana/provisioning/datasources:ro
      - ./grafana-provisioning/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./grafana-provisioning/alerting:/etc/grafana/provisioning/alerting:ro
      - ./grafana-provisioning/models:/var/lib/grafana/netology-dashboards:ro
""", encoding="utf-8")
