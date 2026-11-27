# Домашнее задание 14. Средство визуализации Grafana

## Задание 1. Источник данных

Стенд запущен в Ubuntu внутри VMware по [манифесту из директории help](https://github.com/netology-code/mnt-homeworks/blob/MNT-video/10-monitoring-03-grafana/help/docker-compose.yml). В Compose указана Grafana 12.4.0, её веб-интерфейс опубликован на `127.0.0.1:3000`.

Prometheus опрашивает `nodeexporter:9100` раз в пять секунд. В Grafana подключён источник Prometheus по адресу `http://prometheus:9090` внутри сети Compose.

![Prometheus в списке источников данных](https://github.com/user-attachments/assets/59c4254f-cd03-4ff7-8493-ed77124ae2b5)

## Задание 2. Дашборд и PromQL

Дашборд «Ubuntu — мониторинг узла» содержит четыре панели.

**Утилизация CPU, %**

```promql
100 - 100 * avg by (instance) (rate(node_cpu_seconds_total{job="nodeexporter",mode="idle"}[1m]))
```

**Load Average за 1, 5 и 15 минут**

```promql
node_load1{job="nodeexporter"}
node_load5{job="nodeexporter"}
node_load15{job="nodeexporter"}
```

**Доступная оперативная память, байты**

```promql
node_memory_MemAvailable_bytes{job="nodeexporter"}
```

**Свободное место на корневой файловой системе, байты**

```promql
node_filesystem_avail_bytes{job="nodeexporter",mountpoint="/",fstype!~"tmpfs|overlay|rootfs"}
```

![Дашборд с CPU, Load Average, оперативной памятью и диском](https://github.com/user-attachments/assets/2b889b31-0996-4863-891a-dcbb46cf94e3)

## Задание 3. Алерты

| Панель | Условие в течение 5 минут |
| --- | --- |
| Загрузка CPU | Выше 85% |
| Load Average | Load Average за 5 минут выше числа логических CPU |
| Доступная оперативная память | Ниже 512 МиБ |
| Свободное место на / | Ниже 2 ГиБ |

Правила проверяются раз в минуту и привязаны к соответствующим панелям. На скриншотах правила в состоянии **Normal**, панели отмечены зелёными индикаторами. [Скрипт настройки Grafana](setup-grafana.py).

![Четыре правила Grafana Alerting в состоянии Normal](https://github.com/user-attachments/assets/f6e773ab-18ec-45ee-a569-180e778e05d9)

## Задание 4. JSON Model

[Листинг dashboard.json](dashboard.json).
