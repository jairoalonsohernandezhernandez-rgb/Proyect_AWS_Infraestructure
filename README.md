# Arquitectura Serverless de Ingesta de Eventos en AWS, con Monitoreo

Arquitectura serverless en AWS que desacopla la recepción de eventos del procesamiento, usando **API Gateway → SQS → Lambda → S3**, con la infraestructura definida en **Terraform** y desplegada mediante un pipeline de CI/CD autenticado con **OIDC** (sin credenciales estáticas). Incluye una capa de **monitoreo**: scripts en Python que verifican el estado de los servicios y lo exportan en formato **Prometheus**, junto con un stack local de **Prometheus y Grafana** con Docker Compose.

## Arquitectura

```
Cliente ──▶ API Gateway ──▶ SQS (buffer) ──▶ Lambda ──▶ S3
                                                          │
                                                 Lifecycle policy:
                                                 Standard → Standard-IA (30d)
                                                 → Glacier (90d) → Eliminación (365d)

Monitoreo:
  Script Python (boto3) ──▶ metrics.prom ──▶ node_exporter ──▶ Prometheus ──▶ Grafana
```

1. **API Gateway** recibe la petición del cliente y publica el evento en una cola **SQS**.
2. **SQS** actúa como buffer: desacopla la recepción del procesamiento, controla el ritmo al que Lambda recibe trabajo ante picos de tráfico, y evita que se pierdan eventos si el consumidor falla momentáneamente.
3. **Lambda** consume los mensajes de forma asíncrona y escala según el volumen disponible. El handler (`index.js`) extrae el cuerpo del mensaje, lo parsea (incluyendo el formato codificado por API Gateway), genera una clave única y sube el evento procesado a S3.
4. **S3** almacena los eventos procesados, con una política de **lifecycle** que gestiona el costo de almacenamiento a lo largo del tiempo.

## ¿Por qué SQS entre API Gateway y Lambda?

No es un balanceador de carga: Lambda ya escala automáticamente sin necesidad de SQS. La cola cumple dos funciones distintas:

- **Control de tráfico**: amortigua picos de peticiones y evita saturar recursos aguas abajo.
- **Durabilidad**: si Lambda falla o está momentáneamente ocupada, el mensaje permanece en la cola y se reintenta, en vez de perderse.

## Seguridad e IAM

El pipeline se autentica con AWS mediante **OIDC** (OpenID Connect), sin almacenar credenciales de larga duración como secretos en GitHub.

Cada componente opera con un **rol de IAM independiente**, con los permisos que su función requiere:

| Rol | Permisos |
|---|---|
| **API Gateway** | `sqs:SendMessage`: solo puede publicar en la cola |
| **Lambda** | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` sobre SQS · `s3:PutObject`, `s3:GetObject` sobre S3 |

## Gestión de costos: lifecycle del bucket S3

| Período | Clase de almacenamiento |
|---|---|
| 0 – 30 días | S3 Standard |
| 30 – 90 días | S3 Standard-IA |
| 90 – 365 días | S3 Glacier |
| 365 días | Eliminación automática |

## Monitoreo (`Telemetry/`)

### Verificación de estado

El script `check_health.py` usa **boto3** para comprobar que cada servicio de la arquitectura existe y responde, y devuelve `1` (disponible) o `0` (no disponible):

| Servicio | Llamada a la API |
|---|---|
| S3 | `head_bucket` |
| SQS | `get_queue_attributes` |
| Lambda | `get_function` |
| API Gateway | `get_rest_api` |

Los identificadores se leen de variables de entorno (`S3_BUCKET_NAME`, `SQS_QUEUE_URL`, `LAMBDA_FUNCTION_NAME`, `API_GATEWAY_ID`). En el pipeline, esos valores salen de los **outputs de Terraform**, así que el script siempre apunta a los recursos recién desplegados.

### Exportación a Prometheus

El script `metrics_exporter.py` toma esos resultados y los escribe en `metrics.prom`, en el formato de texto de Prometheus:

```
aws_service_health{service="s3_status"} 1
```

### Stack local de visualización

`docker-compose.yml` levanta tres contenedores:

- **node_exporter**, con el *textfile collector* leyendo `metrics.prom`.
- **Prometheus**, que consulta a node_exporter cada 15 segundos (`prometheus.yml`).
- **Grafana**, en el puerto 3000, para visualizar las métricas.

Ejecución local:

```bash
export S3_BUCKET_NAME=... SQS_QUEUE_URL=... LAMBDA_FUNCTION_NAME=... API_GATEWAY_ID=...
python metrics_exporter.py      # genera metrics.prom
docker compose up -d            # Prometheus en :9090, Grafana en :3000
```

### Alcance y limitaciones

- La verificación es una **instantánea**: se ejecuta en cada corrida del pipeline y no de forma continua.
- "Disponible" significa que el servicio existe y responde a la API, no mide rendimiento (por ejemplo, errores de Lambda o profundidad de la cola).
- Grafana no trae dashboards ni la fuente de datos preconfigurados; se agrega Prometheus (`http://prometheus:9090`) manualmente.

## Pipeline de CI/CD (GitHub Actions)

El workflow se ejecuta en cada push y pull request a `main`:

1. Checkout del código.
2. Autenticación con AWS vía OIDC (`aws-actions/configure-aws-credentials`).
3. Setup de Terraform, `terraform init` y `terraform fmt -check`.
4. `terraform plan`: en pull requests se queda aquí (solo revisión).
5. `terraform apply`: solo en push a `main`.
6. Extracción de los outputs de Terraform como variables de entorno.
7. Instalación de Python y boto3, y ejecución del exportador de métricas.
8. Publicación de `metrics.prom` como artefacto del workflow.

## Estructura del repositorio

```
.
├── .github/workflows/        # Pipeline de CI/CD
├── terraform/environments/dev/   # Infraestructura como código
├── Telemetry/                # Scripts de monitoreo y configuración de Prometheus y Grafana
└── (Lambda) index.js         # Handler de procesamiento
```

## Próximos pasos

- Agregar métricas de rendimiento (profundidad de la cola, errores y duración de Lambda) desde CloudWatch.
- Provisionar la fuente de datos y un dashboard de Grafana.
- Ejecutar la verificación de forma periódica y configurar alertas.

## Tecnologías

Terraform · AWS (API Gateway, SQS, Lambda, S3, IAM, STS) · Python (boto3) · Prometheus · Grafana · Docker Compose · GitHub Actions · OIDC · Node.js

---

*Proyecto personal de práctica, orientado a arquitectura de soluciones serverless, observabilidad y buenas prácticas de seguridad en pipelines CI/CD.*
