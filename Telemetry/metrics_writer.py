import os
from check_health import gather_all_metrics

def export_to_prom():
    metrics = gather_all_metrics()

    with open("metrics.prom", "w") as f:
        for key, value in metrics.items():
            line = f'aws_service_health{{service="{key}"}} {value}\n'
            f.write(line)

        print("Métricas exportadas con exito a metrics.prom")

if __name__ == "__main__":
    export_to_prom()